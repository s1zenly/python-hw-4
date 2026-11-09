import json
from datetime import date, timedelta

from fastapi.testclient import TestClient

import main


def valid_payload(**overrides) -> dict:
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    payload = {
        "фамилия": "Иванов",
        "имя": "Иван",
        "дата_рождения": "1990-05-15",
        "телефон": "+7 (900) 123-45-67",
        "email": "ivan@example.com",
        "причины": ["не приходят письма", "нет доступа к сети"],
        "дата_время_обнаружения": f"{yesterday}T14:30:00",
    }
    payload.update(overrides)
    return payload


def test_saves_valid_appeal(tmp_path, monkeypatch):
    target = tmp_path / "appeals.json"
    monkeypatch.setenv("APPEALS_FILE", str(target))
    client = TestClient(main.app)

    response = client.post("/appeals", json=valid_payload())

    assert response.status_code == 201
    body = response.json()
    assert body["обращение"]["фамилия"] == "Иванов"
    assert body["обращение"]["имя"] == "Иван"
    assert body["обращение"]["телефон"] == "+79001234567"
    assert body["обращение"]["причины"] == ["не приходят письма", "нет доступа к сети"]

    saved = json.loads(target.read_text(encoding="utf-8"))
    assert saved == [body["обращение"]]


def test_appends_several_appeals(tmp_path, monkeypatch):
    target = tmp_path / "appeals.json"
    monkeypatch.setenv("APPEALS_FILE", str(target))
    client = TestClient(main.app)

    first = client.post("/appeals", json=valid_payload())
    second = client.post(
        "/appeals",
        json=valid_payload(фамилия="Петрова", имя="Мария", email="maria@example.com"),
    )

    assert first.status_code == 201
    assert second.status_code == 201
    saved = json.loads(target.read_text(encoding="utf-8"))
    assert [item["фамилия"] for item in saved] == ["Иванов", "Петрова"]

    listed = client.get("/appeals")
    assert listed.status_code == 200
    assert len(listed.json()["обращения"]) == 2


def test_rejects_invalid_names(tmp_path, monkeypatch):
    monkeypatch.setenv("APPEALS_FILE", str(tmp_path / "appeals.json"))
    client = TestClient(main.app)

    for bad_name in ("иванов", "Ivanov", "Иванов1", "Иванов!", "И"):
        response = client.post("/appeals", json=valid_payload(фамилия=bad_name))
        assert response.status_code == 422, bad_name

    response = client.post("/appeals", json=valid_payload(имя="мария"))
    assert response.status_code == 422


def test_rejects_invalid_phone_email_and_dates(tmp_path, monkeypatch):
    monkeypatch.setenv("APPEALS_FILE", str(tmp_path / "appeals.json"))
    client = TestClient(main.app)

    assert client.post("/appeals", json=valid_payload(телефон="12345")).status_code == 422
    assert client.post("/appeals", json=valid_payload(email="not-an-email")).status_code == 422
    assert client.post(
        "/appeals",
        json=valid_payload(дата_рождения="2999-01-01"),
    ).status_code == 422
    assert client.post(
        "/appeals",
        json=valid_payload(дата_время_обнаружения="2999-01-01T00:00:00"),
    ).status_code == 422
    assert client.post(
        "/appeals",
        json=valid_payload(причины=["неизвестная причина"]),
    ).status_code == 422
    assert client.post("/appeals", json=valid_payload(причины=[])).status_code == 422
    assert client.post(
        "/appeals",
        json=valid_payload(дата_время_обнаружения="1980-01-01T00:00:00"),
    ).status_code == 422


def test_accepts_russian_date_formats_and_phone_with_eight(tmp_path, monkeypatch):
    target = tmp_path / "appeals.json"
    monkeypatch.setenv("APPEALS_FILE", str(target))
    client = TestClient(main.app)
    yesterday = (date.today() - timedelta(days=1)).strftime("%d.%m.%Y")

    response = client.post(
        "/appeals",
        json=valid_payload(
            дата_рождения="15.05.1990",
            телефон="89001234567",
            причины=["не работает телефон"],
            дата_время_обнаружения=f"{yesterday} 09:15",
        ),
    )

    assert response.status_code == 201
    appeal = response.json()["обращение"]
    assert appeal["дата_рождения"] == "1990-05-15"
    assert appeal["телефон"] == "+79001234567"
    assert appeal["причины"] == ["не работает телефон"]
