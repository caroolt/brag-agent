import sys
import time
import requests
from requests.auth import HTTPBasicAuth

BASE_URL = "https://api.bitbucket.org/2.0"


def _get_with_retry(url, auth, params=None, max_retries=3):
    for attempt in range(max_retries):
        resp = requests.get(url, auth=auth, params=params)
        if resp.status_code == 401:
            print("Token inválido. Rode /config novamente.")
            sys.exit(1)
        if resp.status_code == 429:
            if attempt < max_retries - 1:
                print("Rate limit atingido. Aguardando 60 segundos...")
                time.sleep(60)
                continue
            else:
                print(f"Rate limit persistente após {max_retries} tentativas.")
                return resp
        return resp
    return resp


def get_current_user(email: str, token: str) -> dict:
    auth = HTTPBasicAuth(email, token)
    resp = _get_with_retry(f"{BASE_URL}/user", auth)
    data = resp.json()
    username = data.get("username") or data.get("nickname", "")
    return {
        "username": username,
        "display_name": data.get("display_name", ""),
    }
