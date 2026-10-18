"""Guard manual collector access and the explicitly approved daily run switch."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_manual_import_and_daily_refresh_keep_independent_controls():
    contents = (ROOT / ".github/workflows/cloud-refresh.yml").read_text(
        encoding="utf-8")
    assert "github.event_name == 'workflow_dispatch'" in contents
    assert "vars.ENABLE_PUBLIC_REFRESH != 'false'" in contents
    assert "github.ref == 'refs/heads/main'" in contents
    assert "(github.event_name == 'workflow_dispatch' || (github.event_name == 'schedule' && vars.ENABLE_PUBLIC_REFRESH != 'false'))" in contents
    # A one-time push trial has completed; a new workflow-code push must not
    # implicitly write new observations to the production database.
    assert "\\n  push:" not in contents
    assert '17 7 * * *' in contents
    assert "NEON_BRANCH_NAME: ${{ vars.NEON_BRANCH_NAME || 'production' }}" in contents


def test_refresh_has_secret_only_credentials_and_no_public_url():
    contents = (ROOT / ".github/workflows/cloud-refresh.yml").read_text(
        encoding="utf-8")
    assert "secrets.FINGRID_API_KEY" in contents
    assert "secrets.ENTSOE_API_TOKEN" in contents
    assert "secrets.NEON_API_KEY" in contents
    assert "python -m src.neon_connection --export-github-env" in contents
    assert "DATABASE_WRITE_URL: https://" not in contents
