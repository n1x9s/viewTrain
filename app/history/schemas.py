from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime
from app.interview.schemas import UserAnswer


class InterviewHistoryItem(BaseModel):
    id: int = Field(description="ID интервью для пользователя")
    date: datetime = Field(description="Дата прохождения интервью")
    score: float = Field(description="Итоговая оценка в процентах")
    
    model_config = ConfigDict(from_attributes=True)


class InterviewHistoryList(BaseModel):
    history: List[InterviewHistoryItem] = Field(description="Список пройденных интервью")


class InterviewHistoryDetail(InterviewHistoryItem):
    feedback: str = Field(description="Обратная связь по интервью")
    answers: List[UserAnswer] = Field(description="Список ответов на вопросы") 