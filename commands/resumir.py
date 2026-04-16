from pathlib import Path
from services import storage


def run():
    month_files = storage.list_bragdoc_months()

    if not month_files:
        print("Nenhum brag document mensal encontrado em .bragdoc/")
        print("Rode /gerar-bragdoc primeiro.")
        return

    print("Arquivos mensais encontrados:")
    for path in month_files:
        print(f"  - {Path(path).name}")

    print("\nPronto para resumir. Claude Code vai gerar o bragdoc anual agora.")
