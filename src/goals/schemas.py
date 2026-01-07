from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class CreateGoalSchema(BaseModel):
    parent_id: Optional[int] = Field(None, description="ID родительской цели (для подцели)")
    title: str = Field(..., min_length=1, max_length=200, description="Название цели")
    description: Optional[str] = Field(None, max_length=1000, description="Подробное описание")
    category: str = Field(..., max_length=50, description="Категория: books, travel, health и т.д.")
    target_value: Optional[int] = Field(
        None, ge=0, description="Целевое значение (количество). None — для качественной цели"
    )
    unit: Optional[str] = Field(None, max_length=50, description="Единица измерения: книг, стран, км")
    end_date: Optional[date] = Field(None, description="Дата завершения цели (YYYY-MM-DD)")

    class Config:
        from_attributes = True
        extra = "forbid"  # запрещаем лишние поля


class GetGoalSchema(CreateGoalSchema):
    current_value: int
    is_completed: bool
    completed_at: date | None
    created_at: datetime
    updated_at: datetime


class UpdateGoalSchema(BaseModel):
    parent_id: Optional[int] = Field(None, description="Новый родитель (если меняем)")
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    category: Optional[str] = Field(None, max_length=50)
    target_value: Optional[int] = Field(None, ge=0)
    unit: Optional[str] = Field(None, max_length=50)
    end_date: Optional[date] = Field(None)

    class Config:
        from_attributes = True
        extra = "forbid"
