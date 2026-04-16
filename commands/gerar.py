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


def _format_author_pr(pr: dict) -> str:
    return (
        f"#### PR #{pr['id']} — {pr['title']}\n"
        f"- Branch: {pr['source_branch']} → {pr['dest_branch']}\n"
        f"- Merged em: {pr['merged_on']}\n"
        f"- Link: {pr['link']}\n"
        f"- Descrição: {pr['description'] or 'sem descrição'}"
    )


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
