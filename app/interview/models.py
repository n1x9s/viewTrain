from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, Enum, DateTime
from sqlalchemy.orm import relationship
from app.dao.database import Base
import enum
from datetime import datetime


class InterviewStatus(str, enum.Enum):
    ONGOING = "ongoing"
    COMPLETED = "completed"


class Question(Base):
    __tablename__ = "pythonn"  # Используем существующую таблицу с вопросами

    id = Column(Integer, primary_key=True, index=True)  # Изменено с Float на Integer
    chance = Column(Float, nullable=True)  # double precision
    question = Column(Text, nullable=False)  # Текст вопроса
    tag = Column(Text, nullable=True)  # Тег или категория вопроса
    answer = Column(Text, nullable=False)  # Правильный ответ

    # Связь с ответами пользователей
    user_answers = relationship("UserAnswer", back_populates="question")


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
    question_id = Column(
        Integer, ForeignKey("pythonn.id"), nullable=False
    )  # Изменено с Float на Integer
    user_answer = Column(Text, nullable=False)
    score = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)

    # Связи с другими таблицами
    interview = relationship("Interview", back_populates="answers")
    question = relationship("Question", back_populates="user_answers")
