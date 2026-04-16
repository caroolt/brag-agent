import sys
from pathlib import Path
from services import storage, bitbucket

SENIORITY_OPTIONS = {
    "1": "Junior",
    "2": "Pleno",
    "3": "Senior",
    "4": "Staff",
    "5": "Principal",
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


def _ask_seniority() -> str:
    print("\nNível de senioridade:")
    for key, label in SENIORITY_OPTIONS.items():
        print(f"  {key}. {label}")
    while True:
        choice = input("Escolha (1-5): ").strip()
        if choice in SENIORITY_OPTIONS:
            return SENIORITY_OPTIONS[choice]
        print("Opção inválida. Digite um número de 1 a 5.")


def _ask_repositories() -> list:
    print("\nRepositórios a monitorar (um por linha, linha vazia para encerrar):")
    repos = []
    while True:
        repo = input("  Repositório: ").strip()
        if not repo:
            break
        repos.append(repo)
    return repos


def run():
    print("=== BragDoc Agent — Configuração ===\n")

    seniority = _ask_seniority()
    workspace = input("\nBitbucket workspace (ex: minha-empresa): ").strip()

    user_data = None
    while user_data is None:
        token = input("Bitbucket API Token (Bearer): ").strip()
        print("Validando credenciais...")
        try:
            user_data = bitbucket.get_current_user(token)
            print(f"Autenticado como: {user_data['display_name']} ({user_data['username']})")
        except SystemExit:
            print("Token inválido. Tente novamente.")
            user_data = None

    repositories = _ask_repositories()

    storage.write_env({"BITBUCKET_TOKEN": token})

    config_data = {
        "username": user_data["username"],
        "display_name": user_data["display_name"],
        "workspace": workspace,
        "seniority": seniority,
        "repositories": repositories,
        "last_run_date": None,
        "generated_months": [],
    }
    storage.write_config(config_data)
    _ensure_gitignore()

    print("\n=== Configuração salva ===")
    print(f"  Usuário:      {user_data['display_name']} ({user_data['username']})")
    print(f"  Workspace:    {workspace}")
    print(f"  Senioridade:  {seniority}")
    print(f"  Repositórios: {', '.join(repositories) if repositories else '(nenhum)'}")
    print(f"  Token:        {'*' * 8} (salvo em .env)")
