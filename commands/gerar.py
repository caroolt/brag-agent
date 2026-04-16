import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from services import storage, bitbucket

MONTH_ABBR = ["jan", "fev", "mar", "abr", "mai", "jun",
              "jul", "ago", "set", "out", "nov", "dez"]
MONTH_NAMES_PT = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                  "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]


def _month_ranges(start: datetime, end: datetime):
    """Yield (range_start, range_end, mes_abbr, year, month_name) for each month."""
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)

    current = start.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    while current <= end:
        next_month = (current.replace(day=28) + timedelta(days=4)).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        range_start = max(start, current)
        range_end = min(end, next_month - timedelta(seconds=1))
        mes = MONTH_ABBR[current.month - 1]
        month_name = MONTH_NAMES_PT[current.month - 1]
        yield range_start, range_end, mes, current.year, month_name
        current = next_month


def _is_description_insufficient(description) -> bool:
    if description is None:
        return True
    return len(str(description).strip()) < 20


def _format_author_pr(pr: dict) -> str:
    text = (
        f"#### PR #{pr['id']} — {pr['title']}\n"
        f"- Branch: {pr['source_branch']} → {pr['dest_branch']}\n"
        f"- Merged em: {pr['merged_on']}\n"
        f"- Link: {pr['link']}\n"
        f"- Descrição: {pr['description'] or 'sem descrição'}"
    )
    if pr.get("diff"):
        text += f"\n- Diff:\n{pr['diff']}"
    return text


def _format_reviewed_pr(pr: dict) -> str:
    return (
        f"#### PR #{pr['id']} — {pr['title']} (autor: {pr['author_display_name']})\n"
        f"- Merged em: {pr['merged_on']}\n"
        f"- Link: {pr['link']}\n"
        f"- Descrição: {pr['description'] or 'sem descrição'}"
    )


def _build_raw_content(
    month_name: str, year: int,
    start: datetime, end: datetime,
    mode: str, repos: list,
    author_prs_by_repo: dict,
    reviewed_prs_by_repo: dict,
) -> str:
    lines = [
        f"# Dados Brutos — {month_name} {year}",
        f"## Período: {start.strftime('%d/%m/%Y')} até {end.strftime('%d/%m/%Y')}",
        f"## Modo: {mode}",
        "",
        "## PRs de Autoria (merged)",
    ]
    for repo in repos:
        lines.append(f"\n### Repositório: {repo}")
        prs = author_prs_by_repo.get(repo, [])
        if not prs:
            lines.append("_(nenhum PR de autoria neste período)_")
        for pr in prs:
            lines.append("")
            lines.append(_format_author_pr(pr))

    lines.append("")
    lines.append("## PRs Revisados/Aprovados")
    for repo in repos:
        lines.append(f"\n### Repositório: {repo}")
        prs = reviewed_prs_by_repo.get(repo, [])
        if not prs:
            lines.append("_(nenhum PR revisado neste período)_")
        for pr in prs:
            lines.append("")
            lines.append(_format_reviewed_pr(pr))

    return "\n".join(lines) + "\n"


def run():
    if not Path(".bragdoc/config.md").exists():
        print("Rode /config primeiro")
        sys.exit(1)

    config = storage.read_config()
    env = storage.read_env()
    token = env.get("BITBUCKET_TOKEN", "")
    email = env.get("BITBUCKET_EMAIL", "")
    workspace = config["workspace"]
    username = config["username"]
    repos = config.get("repositories") or []
    last_run = config.get("last_run_date")

    now = datetime.now(tz=timezone.utc)

    if last_run is None:
        mode = "retroativo"
        start = datetime(now.year, 1, 1, tzinfo=timezone.utc)
    else:
        mode = "delta"
        start = datetime.fromisoformat(last_run)
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)

    processed_months = []

    for range_start, range_end, mes, year, month_name in _month_ranges(start, now):
        start_iso = range_start.strftime("%Y-%m-%dT%H:%M:%S+00:00")
        end_iso = range_end.strftime("%Y-%m-%dT%H:%M:%S+00:00")

        author_prs_by_repo = {}
        reviewed_prs_by_repo = {}

        for repo in repos:
            print(f"Buscando PRs em {repo} ({mes}/{year})...")
            author_prs = bitbucket.get_merged_prs_as_author(
                workspace, repo, username, start_iso, end_iso, token, email
            )
            for pr in author_prs:
                if _is_description_insufficient(pr.get("description")):
                    diff = bitbucket.get_pr_diff(workspace, repo, pr["id"], token, email)
                    if diff:
                        pr["diff"] = diff
            author_prs_by_repo[repo] = author_prs
            reviewed_prs_by_repo[repo] = bitbucket.get_reviewed_prs(
                workspace, repo, username, start_iso, end_iso, token, email
            )

        content = _build_raw_content(
            month_name, year, range_start, range_end, mode,
            repos, author_prs_by_repo, reviewed_prs_by_repo
        )

        storage.write_raw(f"{mes}_{year}", content)

        month_key = f"{mes}_{year}"
        if month_key not in processed_months:
            processed_months.append(month_key)

    existing_months = config.get("generated_months") or []
    for m in processed_months:
        if m not in existing_months:
            existing_months.append(m)
    config["generated_months"] = existing_months
    config["last_run_date"] = now.isoformat()
    storage.write_config(config)

    print("Dados coletados. Claude Code vai processar e gerar os brag docs agora.")
