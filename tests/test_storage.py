import pytest
from pathlib import Path
from services import storage


@pytest.fixture(autouse=True)
def reset_base_dir(tmp_path):
    storage._set_base_dir(tmp_path)
    yield
    storage._set_base_dir(Path("."))


def _write_config_file(tmp_path, content):
    (tmp_path / ".bragdoc").mkdir(exist_ok=True)
    (tmp_path / ".bragdoc" / "config.md").write_text(content, encoding="utf-8")


def test_read_config_basic(tmp_path):
    _write_config_file(tmp_path,
        "# BragDoc Config\n"
        "username: johndoe\n"
        "display_name: John Doe\n"
        "workspace: my-workspace\n"
        "seniority: Senior\n"
        "repositories:\n"
        "  - repo-one\n"
        "  - repo-two\n"
        "last_run_date: null\n"
        "generated_months: []\n"
    )
    result = storage.read_config()
    assert result["username"] == "johndoe"
    assert result["display_name"] == "John Doe"
    assert result["workspace"] == "my-workspace"
    assert result["seniority"] == "Senior"
    assert result["repositories"] == ["repo-one", "repo-two"]
    assert result["last_run_date"] is None
    assert result["generated_months"] == []


def test_read_config_with_generated_months(tmp_path):
    _write_config_file(tmp_path,
        "# BragDoc Config\n"
        "username: johndoe\n"
        "display_name: John Doe\n"
        "workspace: my-workspace\n"
        "seniority: Senior\n"
        "repositories:\n"
        "  - repo-one\n"
        "last_run_date: 2026-01-31T12:00:00+00:00\n"
        "generated_months:\n"
        "  - jan_2026\n"
        "  - fev_2026\n"
    )
    result = storage.read_config()
    assert result["last_run_date"] == "2026-01-31T12:00:00+00:00"
    assert result["generated_months"] == ["jan_2026", "fev_2026"]


def test_write_config_roundtrip(tmp_path):
    (tmp_path / ".bragdoc").mkdir(exist_ok=True)
    data = {
        "username": "johndoe",
        "display_name": "John Doe",
        "workspace": "my-workspace",
        "seniority": "Senior",
        "repositories": ["repo-one", "repo-two"],
        "last_run_date": None,
        "generated_months": [],
    }
    storage.write_config(data)
    result = storage.read_config()
    assert result["username"] == "johndoe"
    assert result["repositories"] == ["repo-one", "repo-two"]
    assert result["last_run_date"] is None
    assert result["generated_months"] == []


def test_write_config_creates_bragdoc_dir(tmp_path):
    data = {
        "username": "x", "display_name": "X", "workspace": "ws",
        "seniority": "Junior", "repositories": [],
        "last_run_date": None, "generated_months": [],
    }
    storage.write_config(data)
    assert (tmp_path / ".bragdoc" / "config.md").exists()


def test_read_env_returns_empty_when_missing(tmp_path):
    result = storage.read_env()
    assert result == {}


def test_write_env_creates_file(tmp_path):
    storage.write_env({"BITBUCKET_EMAIL": "user@example.com", "BITBUCKET_TOKEN": "secret"})
    env_file = tmp_path / ".env"
    assert env_file.exists()
    content = env_file.read_text(encoding="utf-8")
    assert "BITBUCKET_EMAIL=user@example.com" in content
    assert "BITBUCKET_TOKEN=secret" in content


def test_write_env_merges_without_overwriting_existing(tmp_path):
    (tmp_path / ".env").write_text("EXISTING_KEY=keep_me\n", encoding="utf-8")
    storage.write_env({"BITBUCKET_EMAIL": "user@example.com"})
    result = storage.read_env()
    assert result["EXISTING_KEY"] == "keep_me"
    assert result["BITBUCKET_EMAIL"] == "user@example.com"


def test_write_env_updates_existing_key(tmp_path):
    (tmp_path / ".env").write_text("BITBUCKET_TOKEN=old_token\n", encoding="utf-8")
    storage.write_env({"BITBUCKET_TOKEN": "new_token"})
    result = storage.read_env()
    assert result["BITBUCKET_TOKEN"] == "new_token"


def test_read_env_parses_key_value(tmp_path):
    (tmp_path / ".env").write_text(
        "BITBUCKET_EMAIL=user@example.com\nBITBUCKET_TOKEN=mytoken\n",
        encoding="utf-8"
    )
    result = storage.read_env()
    assert result["BITBUCKET_EMAIL"] == "user@example.com"
    assert result["BITBUCKET_TOKEN"] == "mytoken"


def test_write_raw_creates_file(tmp_path):
    storage.write_raw("jan_2026", "# Dados Brutos — Janeiro 2026\n")
    raw_file = tmp_path / ".bragdoc" / "raw_jan_2026.md"
    assert raw_file.exists()
    assert "Janeiro 2026" in raw_file.read_text(encoding="utf-8")


def test_delete_raw_removes_file(tmp_path):
    storage.write_raw("jan_2026", "content")
    storage.delete_raw("jan_2026")
    assert not (tmp_path / ".bragdoc" / "raw_jan_2026.md").exists()


def test_delete_raw_ignores_missing_file(tmp_path):
    storage.delete_raw("nonexistent_2026")  # should not raise


def test_write_month_creates_file(tmp_path):
    storage.write_month("jan", 2026, "# Brag Doc Janeiro\n")
    f = tmp_path / ".bragdoc" / "bragdoc_jan_2026.md"
    assert f.exists()
    assert "Janeiro" in f.read_text(encoding="utf-8")


def test_append_to_month_creates_if_missing(tmp_path):
    storage.append_to_month("jan", 2026, "### Período: 15/01 - 31/01\ncontent\n")
    f = tmp_path / ".bragdoc" / "bragdoc_jan_2026.md"
    assert f.exists()
    assert "15/01" in f.read_text(encoding="utf-8")


def test_append_to_month_appends_if_existing(tmp_path):
    storage.write_month("jan", 2026, "# Original content\n")
    storage.append_to_month("jan", 2026, "\n### Período: 20/01 - 31/01\nnew content\n")
    content = (tmp_path / ".bragdoc" / "bragdoc_jan_2026.md").read_text(encoding="utf-8")
    assert "Original content" in content
    assert "new content" in content


def test_write_annual_creates_file(tmp_path):
    storage.write_annual(2026, "# Brag Doc 2026\n")
    f = tmp_path / ".bragdoc" / "bragdoc_2026.md"
    assert f.exists()


def test_list_bragdoc_months_returns_monthly_files(tmp_path):
    (tmp_path / ".bragdoc").mkdir(exist_ok=True)
    (tmp_path / ".bragdoc" / "bragdoc_jan_2026.md").write_text("x")
    (tmp_path / ".bragdoc" / "bragdoc_fev_2026.md").write_text("x")
    (tmp_path / ".bragdoc" / "bragdoc_2026.md").write_text("x")  # annual — should NOT appear
    result = storage.list_bragdoc_months()
    names = [Path(p).name for p in result]
    assert "bragdoc_jan_2026.md" in names
    assert "bragdoc_fev_2026.md" in names
    assert "bragdoc_2026.md" not in names
