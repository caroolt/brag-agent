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
    result = bitbucket.get_current_user("app_token")
    assert result["username"] == "johndoe"
    assert result["display_name"] == "John Doe"


@patch("services.bitbucket.requests.get")
def test_get_current_user_401_exits(mock_get):
    mock_get.return_value = _mock_response(401)
    with pytest.raises(SystemExit) as exc_info:
        bitbucket.get_current_user("bad_token")
    assert exc_info.value.code == 1


@patch("services.bitbucket.requests.get")
def test_get_current_user_nickname_fallback(mock_get):
    # Bitbucket Cloud sometimes uses 'nickname' instead of 'username'
    mock_get.return_value = _mock_response(200, {
        "nickname": "johndoe",
        "display_name": "John Doe",
    })
    result = bitbucket.get_current_user("app_token")
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
            "token"
        )
    assert resp.status_code == 200
    assert mock_sleep.call_count == 2
    mock_sleep.assert_called_with(60)


@patch("services.bitbucket.requests.get")
def test_get_with_retry_exits_on_401(mock_get):
    mock_get.return_value = _mock_response(401)
    with pytest.raises(SystemExit) as exc_info:
        bitbucket._get_with_retry("https://api.bitbucket.org/2.0/user", "token")
    assert exc_info.value.code == 1


@patch("services.bitbucket.requests.get")
def test_get_with_retry_uses_bearer_header(mock_get):
    mock_get.return_value = _mock_response(200, {"ok": True})
    bitbucket._get_with_retry("https://api.bitbucket.org/2.0/user", "mytoken")
    call_kwargs = mock_get.call_args
    headers = call_kwargs[1].get("headers") or {}
    assert headers.get("Authorization") == "Bearer mytoken"


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
        "token"
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
        "token"
    )
    assert len(result) == 2
    assert mock_get.call_count == 2


@patch("services.bitbucket.requests.get")
def test_get_merged_prs_as_author_403_returns_empty(mock_get, capsys):
    mock_get.return_value = _mock_response(403)
    result = bitbucket.get_merged_prs_as_author(
        "ws", "repo", "johndoe",
        "2026-01-01T00:00:00+00:00", "2026-01-31T23:59:59+00:00",
        "token"
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
        "token"
    )
    assert result == []
    captured = capsys.readouterr()
    assert "não encontrado" in captured.out.lower() or "repo" in captured.out


def _make_reviewed_pr(id, title, author_username="otherdev"):
    return {
        "id": id,
        "title": title,
        "description": "desc",
        "author": {"username": author_username, "display_name": "Other Dev"},
        "source": {"branch": {"name": f"feature/{id}"}},
        "destination": {"branch": {"name": "main"}},
        "merged_on": f"2026-01-{id:02d}T10:00:00+00:00",
        "links": {"html": {"href": f"https://bitbucket.org/ws/repo/pullrequests/{id}"}},
    }


@patch("services.bitbucket.requests.get")
def test_get_reviewed_prs_returns_all_prs(mock_get):
    mock_get.return_value = _mock_response(200, {
        "values": [
            _make_reviewed_pr(10, "Someone's PR"),
            _make_reviewed_pr(11, "Another PR"),
        ],
        "next": None,
    })
    result = bitbucket.get_reviewed_prs(
        "ws", "repo", "johndoe",
        "2026-01-01T00:00:00+00:00", "2026-01-31T23:59:59+00:00",
        "token"
    )
    assert len(result) == 2
    assert result[0]["id"] == 10
    assert result[0]["author_display_name"] == "Other Dev"


@patch("services.bitbucket.requests.get")
def test_get_reviewed_prs_paginates(mock_get):
    page1 = _mock_response(200, {
        "values": [_make_reviewed_pr(10, "PR Ten")],
        "next": "https://api.bitbucket.org/2.0/repositories/ws/repo/pullrequests?page=2",
    })
    page2 = _mock_response(200, {
        "values": [_make_reviewed_pr(11, "PR Eleven")],
        "next": None,
    })
    mock_get.side_effect = [page1, page2]
    result = bitbucket.get_reviewed_prs(
        "ws", "repo", "johndoe",
        "2026-01-01T00:00:00+00:00", "2026-01-31T23:59:59+00:00",
        "token"
    )
    assert len(result) == 2
    assert mock_get.call_count == 2


@patch("services.bitbucket.requests.get")
def test_get_reviewed_prs_uses_role_reviewer_param(mock_get):
    mock_get.return_value = _mock_response(200, {"values": [], "next": None})
    bitbucket.get_reviewed_prs(
        "ws", "repo", "johndoe",
        "2026-01-01T00:00:00+00:00", "2026-01-31T23:59:59+00:00",
        "token"
    )
    call_kwargs = mock_get.call_args
    params = call_kwargs[1].get("params") or (call_kwargs[0][1] if len(call_kwargs[0]) > 1 else {})
    # Verify role=REVIEWER is in the request params
    assert params.get("role") == "REVIEWER"


@patch("services.bitbucket.requests.get")
def test_get_pr_diff_returns_content(mock_get):
    resp = _mock_response(200)
    resp.text = "--- a/file.py\n+++ b/file.py\n@@ -1 +1 @@\n+new line"
    mock_get.return_value = resp
    result = bitbucket.get_pr_diff("ws", "repo", 42, "token")
    assert result is not None
    assert "--- a/file.py" in result
    assert "+new line" in result


@patch("services.bitbucket.requests.get")
def test_get_pr_diff_uses_bearer_header(mock_get):
    resp = _mock_response(200)
    resp.text = "--- a/file.py\n+++ b/file.py"
    mock_get.return_value = resp
    bitbucket.get_pr_diff("ws", "repo", 42, "mytoken")
    call_kwargs = mock_get.call_args
    headers = call_kwargs[1].get("headers") or {}
    assert headers.get("Authorization") == "Bearer mytoken"


@patch("services.bitbucket.requests.get")
def test_get_pr_diff_truncates_at_max_lines(mock_get):
    resp = _mock_response(200)
    resp.text = "\n".join([f"line {i}" for i in range(600)])
    mock_get.return_value = resp
    result = bitbucket.get_pr_diff("ws", "repo", 42, "token")
    assert "diff truncado em 500 linhas" in result
    content_lines = result.splitlines()
    assert content_lines[499] == "line 499"
    assert "line 500" not in result


@patch("services.bitbucket.requests.get")
def test_get_pr_diff_returns_none_on_error(mock_get):
    mock_get.return_value = _mock_response(404)
    result = bitbucket.get_pr_diff("ws", "repo", 42, "token")
    assert result is None


@patch("services.bitbucket.requests.get")
def test_get_pr_diff_no_truncation_when_under_limit(mock_get):
    resp = _mock_response(200)
    resp.text = "\n".join([f"line {i}" for i in range(10)])
    mock_get.return_value = resp
    result = bitbucket.get_pr_diff("ws", "repo", 42, "token")
    assert "truncado" not in result
    assert result.count("\n") == 9
