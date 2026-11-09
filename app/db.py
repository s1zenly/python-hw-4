import json
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_APPEALS_FILE = BASE_DIR / "data" / "appeals.json"


def appeals_path() -> Path:
    return Path(os.environ.get("APPEALS_FILE", DEFAULT_APPEALS_FILE))


def read_appeals() -> list[dict]:
    """Читает сохранённые обращения из JSON-файла."""
    path = appeals_path()
    if not path.exists():
        return []
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return []
    loaded = json.loads(raw)
    if isinstance(loaded, list):
        return loaded
    if isinstance(loaded, dict):
        return [loaded]
    return []


def write_appeals(appeals: list[dict]) -> Path:
    """Полностью перезаписывает JSON-файл списком обращений."""
    path = appeals_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(appeals, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)
    return path
