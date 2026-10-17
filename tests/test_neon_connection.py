"""Tests for the Neon GitHub Actions integration without real secrets."""
from datetime import datetime, timezone
import pytest

from src.neon_connection import resolve_connection
from src.neon_bootstrap import bootstrap


class FakeResponse:
    status_code=200
    def __init__(self, json_body, status=200):
        self.body=json_body
        self.status_code=status
    def json(self):
        return self.body


class FakeSession:
    def __init__(self, *, branches=None, databases=None, uri=None):
        self.calls=[]
        self.branches=branches if branches is not None else [
            {"name": "main", "id": "br-main-111"},
            {"name": "production", "id": "br-production-222"}]
        self.databases=databases if databases is not None else [
            {"name":"neondb","owner_name":"neondb_owner"}]
        self.uri=uri or ("postgresql://neondb_owner:NOT_A_SECRET@"
                         "test.neon.tech/neondb?sslmode=require")
    def get(self,url,*,headers,params,timeout,allow_redirects):
        assert allow_redirects is False
        assert headers["Authorization"]=="Bearer FAKE_API_KEY"
        assert "FAKE_API_KEY" not in url
        self.calls.append((url,params))
        if url.endswith("/branches"):
            return FakeResponse({"branches":self.branches})
        if url.endswith("/databases"):
            return FakeResponse({"databases":self.databases})
        if url.endswith("/connection_uri"):
            return FakeResponse({"uri":self.uri})
        raise AssertionError("Unexpected Neon API request")


def test_resolves_exact_existing_project_branch_and_database_without_guessing():
    fake=FakeSession()
    result=resolve_connection("fragrant-dawn-65247206","FAKE_API_KEY",
                              branch_name="production",session=fake)
    assert result["branch"]=="production"
    assert result["database_name"]=="neondb"
    assert result["role_name"]=="neondb_owner"
    assert result["uri"].startswith("postgresql://")
    assert len(fake.calls)==3
    assert "br-production-222" in fake.calls[1][0]
    assert fake.calls[2][1]=={"branch_id":"br-production-222",
                              "database_name":"neondb",
                              "role_name":"neondb_owner",
                              "pooled":"false"}


def test_wrong_branch_fails_closed_without_silent_default_switch():
    fake=FakeSession(branches=[{"name":"main","id":"br-main-111"}])
    with pytest.raises(ValueError,match="branch not found"):
        resolve_connection("fragrant-dawn-65247206","FAKE_API_KEY",
                           branch_name="production",session=fake)
    assert len(fake.calls)==1


def test_multiple_unrelated_databases_require_explicit_selection():
    fake=FakeSession(databases=[{"name":"foo","owner_name":"foo_owner"},
                                {"name":"bar","owner_name":"bar_owner"}])
    with pytest.raises(ValueError,match="selection ambiguous"):
        resolve_connection("fragrant-dawn-65247206","FAKE_API_KEY",
                           session=fake)
    assert len(fake.calls)==2
    result=resolve_connection("fragrant-dawn-65247206","FAKE_API_KEY",
                              database_name="foo",session=fake)
    assert result["database_name"]=="foo"


def test_missing_api_key_and_disallowed_project_id_rejected_prior_to_network():
    with pytest.raises(ValueError,match="NEON_API_KEY"):
        resolve_connection("fragrant-dawn-65247206","")
    with pytest.raises(ValueError,match="NEON_PROJECT_ID"):
        resolve_connection("../outside","FAKE_API_KEY")


def test_tls_required_and_no_unspecified_owner():
    fake=FakeSession(uri="postgresql://user:p@host/db?sslmode=disable")
    with pytest.raises(ValueError,match="sslmode"):
        resolve_connection("fragrant-dawn-65247206","FAKE_API_KEY",session=fake)
    fake=FakeSession(databases=[{"name":"neondb"}])
    with pytest.raises(ValueError,match="owner role"):
        resolve_connection("fragrant-dawn-65247206","FAKE_API_KEY",session=fake)


def test_bootstrap_source_sample_against_real_ephemeral_postgres(pg_engine,tmp_path,monkeypatch):
    # Fixture is defined in test_cloud_store and needs to be accessible here.
    from sqlalchemy.engine import make_url
    url=make_url(str(pg_engine.url)).set(query={"sslmode":"require"}).render_as_string(hide_password=False)
    # The CI fixture uses a non-TLS ephemeral postgres. This test exercises
    # bootstrap through a substituted cloud engine, without Neon networking.
    monkeypatch.setattr("src.neon_bootstrap.engine_for",lambda _:pg_engine)
    result=bootstrap(url)
    assert result["status"]=="neon_schema_and_sample_readback_passed"
    assert result["points"]==5
    assert result["indicative_capacity_observations"]==18
    again=bootstrap(url)
    assert again["inserted"]["capacity_observation"]==0
