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
