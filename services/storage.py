from pathlib import Path

BASE_DIR = Path(".")


def _set_base_dir(path):
    global BASE_DIR
    BASE_DIR = Path(path)


def _bragdoc_dir() -> Path:
    return BASE_DIR / ".bragdoc"


def read_config() -> dict:
    config_path = _bragdoc_dir() / "config.md"
    if not config_path.exists():
        return {}

    data = {}
    current_list_key = None

    for line in config_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("#") or not line.strip():
            current_list_key = None if not line.startswith("  - ") else current_list_key
            if not line.startswith("  - "):
                continue
        if line.startswith("  - "):
            if current_list_key is not None:
                data[current_list_key].append(line[4:].strip())
            continue
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()
            if value == "null":
                data[key] = None
                current_list_key = None
            elif value == "[]":
                data[key] = []
                current_list_key = key
            elif value == "":
                data[key] = []
                current_list_key = key
            else:
                data[key] = value
                current_list_key = None

    return data


_CONFIG_KEY_ORDER = [
    "username", "display_name", "workspace", "seniority",
    "repositories", "last_run_date", "generated_months",
]


def write_config(data: dict) -> None:
    _bragdoc_dir().mkdir(exist_ok=True)
    lines = ["# BragDoc Config"]

    ordered_keys = _CONFIG_KEY_ORDER + [k for k in data if k not in _CONFIG_KEY_ORDER]
    for key in ordered_keys:
        if key not in data:
            continue
        value = data[key]
        if isinstance(value, list):
            if not value:
                lines.append(f"{key}: []")
            else:
                lines.append(f"{key}:")
                for item in value:
                    lines.append(f"  - {item}")
        elif value is None:
            lines.append(f"{key}: null")
        else:
            lines.append(f"{key}: {value}")

    (_bragdoc_dir() / "config.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def read_env() -> dict:
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        return {}
    result = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        result[key.strip()] = value.strip()
    return result


def write_env(data: dict) -> None:
    env_path = BASE_DIR / ".env"
    existing = read_env()
    existing.update(data)
    lines = [f"{k}={v}" for k, v in existing.items()]
    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
