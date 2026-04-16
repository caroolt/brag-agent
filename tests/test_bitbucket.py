import sys
import pytest
from unittest.mock import patch, MagicMock
from services import bitbucket


def _mock_response(status_code, json_data=None):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data or {}
    resp.text = str(json_data)
    return resp


@patch("services.bitbucket.requests.get")
def test_get_current_user_success(mock_get):
    mock_get.return_value = _mock_response(200, {
        "username": "johndoe",
        "display_name": "John Doe",
    })
    result = bitbucket.get_current_user("user@example.com", "app_pw")
    assert result["username"] == "johndoe"
    assert result["display_name"] == "John Doe"


@patch("services.bitbucket.requests.get")
def test_get_current_user_401_exits(mock_get):
    mock_get.return_value = _mock_response(401)
    with pytest.raises(SystemExit) as exc_info:
        bitbucket.get_current_user("user@example.com", "bad_pw")
    assert exc_info.value.code == 1


@patch("services.bitbucket.requests.get")
def test_get_current_user_nickname_fallback(mock_get):
    # Bitbucket Cloud sometimes uses 'nickname' instead of 'username'
    mock_get.return_value = _mock_response(200, {
        "nickname": "johndoe",
        "display_name": "John Doe",
    })
    result = bitbucket.get_current_user("user@example.com", "app_pw")
    assert result["username"] == "johndoe"


@patch("services.bitbucket.requests.get")
def test_get_with_retry_retries_on_429(mock_get):
    mock_get.side_effect = [
        _mock_response(429),
        _mock_response(429),
        _mock_response(200, {"ok": True}),
    ]
    with patch("services.bitbucket.time.sleep") as mock_sleep:
        resp = bitbucket._get_with_retry(
            "https://api.bitbucket.org/2.0/user",
            ("email", "token")
        )
    assert resp.status_code == 200
    assert mock_sleep.call_count == 2
    mock_sleep.assert_called_with(60)


@patch("services.bitbucket.requests.get")
def test_get_with_retry_exits_on_401(mock_get):
    mock_get.return_value = _mock_response(401)
    with pytest.raises(SystemExit) as exc_info:
        bitbucket._get_with_retry("https://api.bitbucket.org/2.0/user", ("email", "token"))
    assert exc_info.value.code == 1


def _make_pr(id, title, author_username, description=""):
    return {
        "id": id,
        "title": title,
        "description": description,
        "author": {"username": author_username, "display_name": "Test User"},
        "source": {"branch": {"name": f"feature/{id}"}},
        "destination": {"branch": {"name": "main"}},
        "merged_on": f"2026-01-{id:02d}T10:00:00+00:00",
        "links": {"html": {"href": f"https://bitbucket.org/ws/repo/pullrequests/{id}"}},
    }


@patch("services.bitbucket.requests.get")
def test_get_merged_prs_as_author_returns_own_prs(mock_get):
    mock_get.return_value = _mock_response(200, {
        "values": [
            _make_pr(1, "My PR", "johndoe"),
            _make_pr(2, "Other PR", "janedoe"),  # not mine
        ],
        "next": None,
    })
    result = bitbucket.get_merged_prs_as_author(
        "ws", "repo", "johndoe",
        "2026-01-01T00:00:00+00:00", "2026-01-31T23:59:59+00:00",
        "user@example.com", "token"
    )
    assert len(result) == 1
    assert result[0]["id"] == 1
    assert result[0]["title"] == "My PR"
    assert result[0]["source_branch"] == "feature/1"
    assert result[0]["dest_branch"] == "main"


@patch("services.bitbucket.requests.get")
def test_get_merged_prs_as_author_paginates(mock_get):
    page1 = _mock_response(200, {
        "values": [_make_pr(1, "PR One", "johndoe")],
        "next": "https://api.bitbucket.org/2.0/repositories/ws/repo/pullrequests?page=2",
    })
    page2 = _mock_response(200, {
        "values": [_make_pr(2, "PR Two", "johndoe")],
        "next": None,
    })
    mock_get.side_effect = [page1, page2]
    result = bitbucket.get_merged_prs_as_author(
        "ws", "repo", "johndoe",
        "2026-01-01T00:00:00+00:00", "2026-01-31T23:59:59+00:00",
        "user@example.com", "token"
    )
    assert len(result) == 2
    assert mock_get.call_count == 2


@patch("services.bitbucket.requests.get")
def test_get_merged_prs_as_author_403_returns_empty(mock_get, capsys):
    mock_get.return_value = _mock_response(403)
    result = bitbucket.get_merged_prs_as_author(
        "ws", "repo", "johndoe",
        "2026-01-01T00:00:00+00:00", "2026-01-31T23:59:59+00:00",
        "user@example.com", "token"
    )
    assert result == []
    captured = capsys.readouterr()
    assert "permissão" in captured.out.lower() or "repo" in captured.out


@patch("services.bitbucket.requests.get")
def test_get_merged_prs_as_author_404_returns_empty(mock_get, capsys):
    mock_get.return_value = _mock_response(404)
    result = bitbucket.get_merged_prs_as_author(
        "ws", "repo", "johndoe",
        "2026-01-01T00:00:00+00:00", "2026-01-31T23:59:59+00:00",
        "user@example.com", "token"
    )
    assert result == []
    captured = capsys.readouterr()
    assert "não encontrado" in captured.out.lower() or "repo" in captured.out
