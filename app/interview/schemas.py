from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime


class InterviewStart(BaseModel):
    interview_id: int = Field(description="ID интервью")
    status: str = Field(description="Статус интервью")
    message: str = Field(description="Сообщение о начале интервью")


class QuestionResponse(BaseModel):
    question_id: int = Field(description="ID вопроса")
    question_text: str = Field(description="Текст вопроса")
    tag: Optional[str] = Field(None, description="Тег или категория вопроса")


class AnswerRequest(BaseModel):
    question_id: int = Field(description="ID вопроса")
    user_answer: str = Field(description="Ответ пользователя")


class AnswerResponse(BaseModel):
    score: float = Field(description="Оценка ответа")
    feedback: str = Field(description="Обратная связь по ответу")
    interview_completed: bool = Field(description="Флаг завершения интервью")
    final_score: Optional[float] = Field(
        None, description="Итоговая оценка интервью (если завершено)"
    )
    final_feedback: Optional[str] = Field(
        None, description="Итоговая обратная связь по интервью (если завершено)"
    )


class InterviewStatus(BaseModel):
    interview_id: int = Field(description="ID интервью")
    answered_questions: int = Field(description="Количество отвеченных вопросов")
    total_questions: int = Field(description="Общее количество вопросов")
    progress: str = Field(description="Прогресс в процентах")


class InterviewFinish(BaseModel):
    interview_id: int = Field(description="ID интервью")
    score: float = Field(description="Итоговая оценка")
    feedback: str = Field(description="Обратная связь по интервью")


class QuestionBase(BaseModel):
    question: str = Field(description="Текст вопроса")
    answer: str = Field(description="Правильный ответ")
    chance: Optional[float] = Field(
        None, description="Вероятность или сложность вопроса"
    )
    tag: Optional[str] = Field(None, description="Тег или категория вопроса")

    model_config = ConfigDict(from_attributes=True)


class QuestionCreate(QuestionBase):
    pass


class Question(QuestionBase):
    id: float = Field(description="ID вопроса")

    model_config = ConfigDict(from_attributes=True)


class UserAnswerBase(BaseModel):
    question_id: int = Field(description="ID вопроса")
    user_answer: str = Field(description="Ответ пользователя")

    model_config = ConfigDict(from_attributes=True)


class UserAnswerCreate(UserAnswerBase):
    interview_id: int = Field(description="ID интервью")


class UserAnswer(UserAnswerBase):
    id: int = Field(description="ID ответа")
    interview_id: int = Field(description="ID интервью")
    score: Optional[float] = Field(None, description="Оценка ответа")
    feedback: Optional[str] = Field(None, description="Обратная связь по ответу")

    model_config = ConfigDict(from_attributes=True)


class InterviewBase(BaseModel):
    user_id: int = Field(description="ID пользователя")
    status: str = Field(description="Статус интервью")

    model_config = ConfigDict(from_attributes=True)


class InterviewCreate(InterviewBase):
    pass


class Interview(InterviewBase):
    id: int = Field(description="ID интервью")
    total_score: Optional[float] = Field(None, description="Итоговая оценка")
    feedback: Optional[str] = Field(None, description="Обратная связь по интервью")
    answers: List[UserAnswer] = Field(
        default_factory=list, description="Ответы пользователя"
    )

    model_config = ConfigDict(from_attributes=True)


class QuestionListResponse(BaseModel):
    """Ответ с пагинацией списка вопросов"""

    items: List[Question] = Field(description="Список вопросов")
    total: int = Field(description="Общее количество вопросов")
    page: int = Field(description="Текущая страница")
    pages: int = Field(description="Общее количество страниц")
    limit: int = Field(description="Количество вопросов на странице")

    model_config = ConfigDict(from_attributes=True)
