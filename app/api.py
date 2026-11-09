from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, ConfigDict, Field

from app.logic import list_appeals, save_appeal
from app.validation import SubscriberAppeal


class AppealCreated(BaseModel):
    message: str = Field("Обращение сохранено", alias="сообщение")
    file: str = Field(..., alias="файл")
    appeal: SubscriberAppeal = Field(..., alias="обращение")

    model_config = ConfigDict(populate_by_name=True)


app = FastAPI(
    title="Сервис обращений абонентов",
    description=(
        "Принимает обращение абонента, проверяет поля моделью Pydantic "
        "и сохраняет результат в JSON-файл."
    ),
    version="1.0.0",
)


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/docs")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/appeals", response_model=AppealCreated, status_code=201)
def create_appeal(appeal: SubscriberAppeal) -> AppealCreated:
    path = save_appeal(appeal)
    return AppealCreated(file=str(path), appeal=appeal)


@app.get("/appeals")
def get_appeals() -> dict[str, list[dict]]:
    return {"обращения": list_appeals()}
