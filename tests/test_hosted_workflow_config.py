"""Guard the separation between one-time/manual collection and opt-in recurring runs."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_manual_hosted_import_is_not_gated_on_recurring_refresh():
    contents = (ROOT / ".github/workflows/cloud-refresh.yml").read_text(
        encoding="utf-8")
    assert "github.event_name == 'workflow_dispatch'" in contents
    assert "vars.ENABLE_PUBLIC_REFRESH == 'true'" in contents
    assert "github.ref == 'refs/heads/main'" in contents
    assert "(github.event_name == 'workflow_dispatch' || vars.ENABLE_PUBLIC_REFRESH == 'true')" in contents
    assert "NEON_BRANCH_NAME: ${{ vars.NEON_BRANCH_NAME || 'production' }}" in contents


def test_refresh_has_secret_only_credentials_and_no_public_url():
    contents = (ROOT / ".github/workflows/cloud-refresh.yml").read_text(
        encoding="utf-8")
    assert "secrets.FINGRID_API_KEY" in contents
    assert "secrets.ENTSOE_API_TOKEN" in contents
    assert "secrets.NEON_API_KEY" in contents
    assert "python -m src.neon_connection --export-github-env" in contents
    assert "DATABASE_WRITE_URL: https://" not in contents
