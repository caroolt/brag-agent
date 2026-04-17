import sys
import argparse
from pathlib import Path
from services import storage, bitbucket

SENIORITY_OPTIONS = {
    "1": "Junior",
    "2": "Pleno",
    "3": "Senior",
    "4": "Staff",
    "5": "Principal",
}

AREA_OPTIONS = {
    "1": "Frontend",
    "2": "Backend",
    "3": "Fullstack",
    "4": "Mobile",
    "5": "Data/ML",
    "6": "DevOps/Infra",
}


def _ensure_gitignore():
    gitignore = Path(".gitignore")
    entries = {".env", ".bragdoc/"}
    existing = set()
    if gitignore.exists():
        existing = set(gitignore.read_text(encoding="utf-8").splitlines())
    missing = entries - existing
    if missing:
        with gitignore.open("a", encoding="utf-8") as f:
            for entry in sorted(missing):
                f.write(f"{entry}\n")


def _save(seniority, area, workspace, token, email, repos_raw):
    repos = [r.strip() for r in repos_raw.split(",") if r.strip()]

    user_data = None
    try:
        user_data = bitbucket.get_current_user(token, email)
    except SystemExit:
        print("Token inválido. Rode /configure novamente.")
        sys.exit(1)

    storage.write_env({"BITBUCKET_TOKEN": token, "BITBUCKET_EMAIL": email})

    config_data = {
        "username": user_data["username"],
        "display_name": user_data["display_name"],
        "workspace": workspace,
        "seniority": seniority,
        "area": area,
        "repositories": repos,
        "last_run_date": None,
        "generated_months": [],
        "processed_context": [],
    }
    storage.write_config(config_data)
    _ensure_gitignore()

    print("\n=== Configuração salva ===")
    print(f"  Usuário:      {user_data['display_name']} ({user_data['username']})")
    print(f"  Workspace:    {workspace}")
    print(f"  Senioridade:  {seniority}")
    print(f"  Área:         {area}")
    print(f"  Repositórios: {', '.join(repos) if repos else '(nenhum)'}")
    print(f"  Token:        {'*' * 8} (salvo em .env)")


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seniority", default=None)
    parser.add_argument("--area", default=None)
    parser.add_argument("--workspace", default=None)
    parser.add_argument("--token", default=None)
    parser.add_argument("--email", default=None)
    parser.add_argument("--repos", default=None)
    args, _ = parser.parse_known_args()

    # modo CLI — chamado pelo Claude Code com argumentos
    if all([args.seniority, args.area, args.workspace, args.token, args.email, args.repos]):
        _save(args.seniority, args.area, args.workspace, args.token, args.email, args.repos)
        return

    # modo interativo — fallback para rodar direto no terminal
    print("=== BragDoc Agent — Configuração ===\n")
    print("Nível de senioridade:")
    for key, label in SENIORITY_OPTIONS.items():
        print(f"  {key}. {label}")
    while True:
        choice = input("Escolha (1-5): ").strip()
        if choice in SENIORITY_OPTIONS:
            seniority = SENIORITY_OPTIONS[choice]
            break
        print("Opção inválida.")

    print("\nÁrea de atuação:")
    for key, label in AREA_OPTIONS.items():
        print(f"  {key}. {label}")
    while True:
        choice = input("Escolha (1-6): ").strip()
        if choice in AREA_OPTIONS:
            area = AREA_OPTIONS[choice]
            break
        print("Opção inválida.")

    workspace = input("\nBitbucket workspace: ").strip()
    token = input("Bitbucket API Token: ").strip()
    email = input("Email do Bitbucket: ").strip()

    print("\nRepositórios a monitorar (um por linha, linha vazia para encerrar):")
    repos = []
    while True:
        repo = input("  Repositório: ").strip()
        if not repo:
            break
        repos.append(repo)

    _save(seniority, area, workspace, token, email, ",".join(repos))
