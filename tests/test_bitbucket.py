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
