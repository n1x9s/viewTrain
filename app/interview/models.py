from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    ForeignKey,
    Text,
    Enum,
    DateTime,
    and_,
)
from sqlalchemy.orm import relationship
from app.dao.database import Base
import enum
from datetime import datetime


class InterviewStatus(str, enum.Enum):
    ONGOING = "ongoing"
    COMPLETED = "completed"


class PythonQuestion(Base):
    """Модель для вопросов по Python"""

    __tablename__ = "pythonn"

    id = Column(Integer, primary_key=True, index=True)
    chance = Column(Float, nullable=True)  # double precision
    question = Column(Text, nullable=False)  # Текст вопроса
    tag = Column(Text, nullable=True)  # Тег или категория вопроса
    answer = Column(Text, nullable=False)  # Правильный ответ


class GolangQuestion(Base):
    """Модель для вопросов по Go"""

    __tablename__ = "golangquestions"

    id = Column(Integer, primary_key=True, index=True)
    chance = Column(Float, nullable=True)  # double precision
    question = Column(Text, nullable=False)  # Текст вопроса
    tag = Column(Text, nullable=True)  # Тег или категория вопроса
    answer = Column(Text, nullable=False)  # Правильный ответ


class Interview(Base):
    __tablename__ = "interviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String, default=InterviewStatus.ONGOING, nullable=False)
    total_score = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)
    question_ids = Column(
        Text, nullable=True
    )  # Для хранения списка ID выбранных вопросов
    question_type = Column(
        String, nullable=False, default="pythonn"
    )  # Тип вопросов (pythonn или golangquestions)
    user_interview_id = Column(
        Integer, nullable=True
    )  # ID интервью для конкретного пользователя
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Связи с другими таблицами
    user = relationship("User", back_populates="interviews")
    answers = relationship("UserAnswer", back_populates="interview")


class UserAnswer(Base):
    __tablename__ = "user_answers"

    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"), nullable=False)
    question_id = Column(Integer, nullable=False)  # ID вопроса
    question_type = Column(
        String, nullable=False, default="pythonn"
    )  # Тип вопроса (pythonn или golangquestions)
    user_answer = Column(Text, nullable=False)
    score = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)

    # Связь с интервью
    interview = relationship("Interview", back_populates="answers")

    async def get_question(self, session):
        """
        Получить связанный вопрос в зависимости от типа

        Args:
            session: Сессия БД

        Returns:
            Объект вопроса (PythonQuestion или GolangQuestion)
        """
        from sqlalchemy.future import select

        if self.question_type == "pythonn":
            query = select(PythonQuestion).filter(PythonQuestion.id == self.question_id)
        else:
            query = select(GolangQuestion).filter(GolangQuestion.id == self.question_id)

        result = await session.execute(query)
        return result.scalar_one_or_none()
