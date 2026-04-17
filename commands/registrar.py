import sys
import argparse
import re
from datetime import datetime, timezone
from pathlib import Path


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", default=None)
    parser.add_argument("--description", default=None)
    parser.add_argument("--impact", default="")
    parser.add_argument("--date", default=None)
    parser.add_argument("--references", default="")
    args, _ = parser.parse_known_args()

    if all([args.type, args.description, args.date]):
        _save(args.type, args.description, args.impact, args.date, args.references)
        return

    # modo interativo — fallback para rodar direto no terminal
    print("=== BragDoc Agent — Registrar Contexto ===\n")
    TYPE_OPTIONS = {
        "1": "Architecture decision",
        "2": "Technical discussion",
        "3": "Cross-team alignment",
        "4": "Technical influence",
        "5": "Incident response",
        "6": "Mentorship or knowledge sharing",
        "7": "Other",
    }
    print("Tipo de contribuição:")
    for key, label in TYPE_OPTIONS.items():
        print(f"  {key}. {label}")
    while True:
        choice = input("Escolha (1-7): ").strip()
        if choice in TYPE_OPTIONS:
            contribution_type = TYPE_OPTIONS[choice]
            break
        print("Opção inválida.")

    print("\nDescreva o que aconteceu (ENTER duas vezes para encerrar):")
    lines = []
    empty_count = 0
    while empty_count < 2:
        line = input()
        if line == "":
            empty_count += 1
        else:
            empty_count = 0
        lines.append(line)
    description = "\n".join(lines).strip()

    impact = input("\nQual foi o impacto ou resultado? (pode deixar em branco): ").strip()
    date = input("Quando aconteceu? (ex: hoje, 10/04, semana passada): ").strip()
    references = input("Tickets, PRs ou pessoas envolvidas? (opcional): ").strip()

    _save(contribution_type, description, impact, date, references)


def _save(contribution_type, description, impact, date, references):
    context_dir = Path(".bragdoc/context")
    context_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now(tz=timezone.utc)
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    slug = re.sub(r"[^a-z0-9]+", "_", contribution_type.lower())[:30]
    filename = f"{timestamp}_{slug}.md"
    filepath = context_dir / filename

    lines = [
        f"# Context Entry — {contribution_type}",
        f"",
        f"**Date:** {date}",
        f"**Recorded at:** {now.strftime('%Y-%m-%d %H:%M UTC')}",
        f"**Type:** {contribution_type}",
        f"",
        f"## Description",
        f"",
        description,
        f"",
    ]
    if impact:
        lines += [
            f"## Impact",
            f"",
            impact,
            f"",
        ]
    if references:
        lines += [
            f"## References",
            f"",
            references,
            f"",
        ]

    filepath.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nEntrada salva em: {filepath}")
