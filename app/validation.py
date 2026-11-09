import re
from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# Первая буква заглавная, дальше строчные. Только кириллица, без цифр и спецсимволов.
CYRILLIC_NAME = re.compile(r"^[А-ЯЁ][а-яё]+$")
EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")
PHONE_SEPARATORS = re.compile(r"[\s()\-]")


class AppealReason(str, Enum):
    """Допустимые причины обращения."""

    NO_EMAILS = "не приходят письма"
    NO_NETWORK = "нет доступа к сети"
    PHONE_BROKEN = "не работает телефон"


def _validate_cyrillic_name(value: str, field_title: str) -> str:
    cleaned = value.strip()
    if not CYRILLIC_NAME.fullmatch(cleaned):
        raise ValueError(
            f"{field_title}: значение должно начинаться с заглавной буквы "
            "и содержать только кириллицу, без цифр и спецсимволов"
        )
    return cleaned


class SubscriberAppeal(BaseModel):
    """Обращение абонента. Все поля проверяются валидаторами Pydantic."""

    model_config = ConfigDict(populate_by_name=True)

    last_name: str = Field(..., alias="фамилия", examples=["Иванов"])
    first_name: str = Field(..., alias="имя", examples=["Иван"])
    birth_date: date = Field(..., alias="дата_рождения", examples=["1990-05-15"])
    phone: str = Field(..., alias="телефон", examples=["+79001234567"])
    email: str = Field(..., alias="email", examples=["ivan@example.com"])
    reasons: list[AppealReason] = Field(
        ...,
        alias="причины",
        min_length=1,
        examples=[["не приходят письма", "нет доступа к сети"]],
    )
    discovered_at: datetime = Field(
        ...,
        alias="дата_время_обнаружения",
        examples=["2026-11-01T14:30:00"],
    )

    @field_validator("last_name")
    @classmethod
    def validate_last_name(cls, value: str) -> str:
        return _validate_cyrillic_name(value, "Фамилия")

    @field_validator("first_name")
    @classmethod
    def validate_first_name(cls, value: str) -> str:
        return _validate_cyrillic_name(value, "Имя")

    @field_validator("birth_date", mode="before")
    @classmethod
    def parse_birth_date(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        text = value.strip()
        for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
            try:
                return datetime.strptime(text, fmt).date()
            except ValueError:
                continue
        raise ValueError("Дата рождения должна быть в формате ГГГГ-ММ-ДД или ДД.ММ.ГГГГ")

    @field_validator("birth_date")
    @classmethod
    def validate_birth_date(cls, value: date) -> date:
        today = date.today()
        if value > today:
            raise ValueError("Дата рождения не может быть в будущем")
        age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
        if age > 120:
            raise ValueError("Дата рождения указана некорректно: возраст больше 120 лет")
        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        compact = PHONE_SEPARATORS.sub("", value.strip())
        if compact.startswith("8") and len(compact) == 11:
            compact = "+7" + compact[1:]
        if not re.fullmatch(r"\+7\d{10}", compact):
            raise ValueError(
                "Номер телефона должен содержать 11 цифр и начинаться с +7 или 8, "
                "например +79001234567"
            )
        return compact

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        cleaned = value.strip()
        if not EMAIL_PATTERN.fullmatch(cleaned):
            raise ValueError("Некорректный e-mail")
        return cleaned

    @field_validator("discovered_at", mode="before")
    @classmethod
    def parse_discovered_at(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        text = value.strip()
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%d.%m.%Y %H:%M:%S", "%d.%m.%Y %H:%M"):
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                continue
        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError(
                "Дата и время обнаружения должны быть в формате "
                "ГГГГ-ММ-ДДTЧЧ:ММ:СС или ДД.ММ.ГГГГ ЧЧ:ММ"
            ) from None

    @field_validator("discovered_at")
    @classmethod
    def validate_discovered_at(cls, value: datetime) -> datetime:
        now = datetime.now(value.tzinfo) if value.tzinfo else datetime.now()
        if value > now:
            raise ValueError("Дата и время обнаружения проблемы не могут быть в будущем")
        return value

    @field_validator("reasons")
    @classmethod
    def validate_reasons(cls, value: list[AppealReason]) -> list[AppealReason]:
        if len(value) != len(set(value)):
            raise ValueError("Причины обращения не должны повторяться")
        return value

    @model_validator(mode="after")
    def problem_not_before_birth(self) -> "SubscriberAppeal":
        discovered_day = self.discovered_at.date()
        if discovered_day < self.birth_date:
            raise ValueError("Проблема не может быть обнаружена раньше даты рождения")
        return self
