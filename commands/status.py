from pathlib import Path
from services import storage


def run():
    if not Path(".bragdoc/config.md").exists():
        print("Nenhuma configuração encontrada. Rode /configure primeiro.")
        return

    config = storage.read_config()
    env = storage.read_env()

    print("=== BragDoc Agent — Status ===\n")
    print(f"Usuário:       {config.get('display_name', '?')} ({config.get('username', '?')})")
    print(f"Email:         {env.get('BITBUCKET_EMAIL', '(não configurado)')}")
    print(f"Workspace:     {config.get('workspace', '?')}")
    print(f"Senioridade:   {config.get('seniority', '?')}")

    repos = config.get("repositories") or []
    if repos:
        print("Repositórios:")
        for repo in repos:
            print(f"  - {repo}")
    else:
        print("Repositórios:  (nenhum configurado)")

    last_run = config.get("last_run_date")
    print(f"\nÚltima run:    {last_run if last_run else 'nunca'}")

    months = config.get("generated_months") or []
    if months:
        print(f"Meses gerados: {', '.join(months)}")
    else:
        print("Meses gerados: (nenhum)")
