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


def _extract_pr(pr: dict) -> dict:
    desc = (pr.get("description") or "").strip() or None
    return {
        "id": pr["id"],
        "title": pr["title"],
        "description": desc,
        "source_branch": pr.get("source", {}).get("branch", {}).get("name", ""),
        "dest_branch": pr.get("destination", {}).get("branch", {}).get("name", ""),
        "merged_on": pr.get("merged_on", ""),
        "link": pr.get("links", {}).get("html", {}).get("href", ""),
    }


def get_merged_prs_as_author(
    workspace: str, repo: str, username: str,
    start_date: str, end_date: str,
    email: str, token: str
) -> list:
    auth = HTTPBasicAuth(email, token)
    url = f"{BASE_URL}/repositories/{workspace}/{repo}/pullrequests"
    params = {
        "state": "MERGED",
        "q": f'merged_on>="{start_date}" AND merged_on<="{end_date}"',
        "pagelen": 50,
    }

    results = []
    current_url = url
    current_params = params

    while current_url:
        resp = _get_with_retry(current_url, auth, params=current_params)
        if resp.status_code == 403:
            print(f"Sem permissão para o repositório {repo}.")
            break
        if resp.status_code == 404:
            print(f"Repositório {repo} não encontrado no workspace {workspace}.")
            break
        if resp.status_code != 200:
            print(f"Erro {resp.status_code} em {repo}: {resp.text[:200]}")
            break

        data = resp.json()
        for pr in data.get("values", []):
            author = pr.get("author", {})
            author_id = author.get("username") or author.get("nickname", "")
            if author_id == username:
                results.append(_extract_pr(pr))

        current_url = data.get("next")
        current_params = None

    return results


def _extract_reviewed_pr(pr: dict) -> dict:
    data = _extract_pr(pr)
    data["author_display_name"] = pr.get("author", {}).get("display_name", "")
    return data


def get_reviewed_prs(
    workspace: str, repo: str, username: str,
    start_date: str, end_date: str,
    email: str, token: str
) -> list:
    auth = HTTPBasicAuth(email, token)
    url = f"{BASE_URL}/repositories/{workspace}/{repo}/pullrequests"
    params = {
        "state": "MERGED",
        "role": "REVIEWER",
        "q": f'merged_on>="{start_date}" AND merged_on<="{end_date}"',
        "pagelen": 50,
    }

    results = []
    current_url = url
    current_params = params

    while current_url:
        resp = _get_with_retry(current_url, auth, params=current_params)
        if resp.status_code == 403:
            print(f"Sem permissão para o repositório {repo}.")
            break
        if resp.status_code == 404:
            print(f"Repositório {repo} não encontrado no workspace {workspace}.")
            break
        if resp.status_code != 200:
            print(f"Erro {resp.status_code} em {repo}: {resp.text[:200]}")
            break

        data = resp.json()
        results.extend(_extract_reviewed_pr(pr) for pr in data.get("values", []))
        current_url = data.get("next")
        current_params = None

    return results
