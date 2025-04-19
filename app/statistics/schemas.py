from pydantic import BaseModel, Field
from typing import List, Dict


class InterviewStatistics(BaseModel):
    """Статистика по всем интервью пользователя"""
    total_interviews: int = Field(..., description="Общее количество интервью")
    successful_percent: float = Field(..., description="Процент успешных интервью")
    unsuccessful_percent: float = Field(..., description="Процент неуспешных интервью")


class QuestionsStatistics(BaseModel):
    """Статистика по ответам на вопросы"""
    total_questions: int = Field(..., description="Общее количество отвеченных вопросов")
    successful_percent: float = Field(..., description="Процент успешных ответов")
    unsuccessful_percent: float = Field(..., description="Процент неуспешных ответов")
    skipped_percent: float = Field(..., description="Процент пропущенных вопросов")


class QuestionStatItem(BaseModel):
    """Статистика по конкретному вопросу"""
    question_id: int = Field(..., description="ID вопроса")
    question_text: str = Field(..., description="Текст вопроса")
    tag: str = Field(None, description="Тег/категория вопроса")
    success_rate: float = Field(..., description="Процент успешных ответов")
    answer_count: int = Field(..., description="Количество ответов на вопрос")


class TopQuestionsStatistics(BaseModel):
    """Топ-5 вопросов по успешности/неуспешности"""
    questions: List[QuestionStatItem] = Field(..., description="Список вопросов с статистикой") 