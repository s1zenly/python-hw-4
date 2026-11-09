from pathlib import Path

from app.db import read_appeals, write_appeals
from app.validation import SubscriberAppeal


def save_appeal(appeal: SubscriberAppeal) -> Path:
    """Добавляет уже проверенное обращение в хранилище."""
    stored = read_appeals()
    stored.append(appeal.model_dump(mode="json", by_alias=True))
    return write_appeals(stored)


def list_appeals() -> list[dict]:
    """Возвращает все сохранённые обращения."""
    return read_appeals()
