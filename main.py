import sys


def main():
    commands = {
        "config": "commands.config",
        "gerar": "commands.gerar",
        "resumir": "commands.resumir",
        "status": "commands.status",
    }

    if len(sys.argv) < 2 or sys.argv[1] not in commands:
        print("Uso: python main.py <comando>")
        print("Comandos disponíveis:")
        for cmd in commands:
            print(f"  {cmd}")
        sys.exit(0 if len(sys.argv) < 2 else 1)

    module_name = commands[sys.argv[1]]
    module = __import__(module_name, fromlist=["run"])
    module.run()


if __name__ == "__main__":
    main()
