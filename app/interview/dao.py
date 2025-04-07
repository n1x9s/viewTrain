from app.dao.base import BaseDAO
from app.interview.models import Question, Interview, UserAnswer
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func
from sqlalchemy.orm import selectinload
import random
from typing import List, Optional, Tuple
from app.services.gigachat import GigaChatService
import logging

logger = logging.getLogger(__name__)

class QuestionDAO(BaseDAO):
    model = Question
    
    @classmethod
    async def get_random_question(cls, session: AsyncSession, exclude_ids: List[int] = None) -> Optional[Question]:
        """Получить случайный вопрос, исключая уже отвеченные"""
        query = select(cls.model)
        
        if exclude_ids and len(exclude_ids) > 0:
            query = query.filter(cls.model.id.not_in(exclude_ids))
            
        # Получаем общее количество вопросов
        count_query = select(func.count()).select_from(query.subquery())
        count = await session.scalar(count_query)
        
        if count == 0:
            return None
            
        # Выбираем случайный вопрос
        offset = random.randint(0, count - 1)
        query = query.offset(offset).limit(1)
        
        result = await session.execute(query)
        return result.scalar_one_or_none()
    
    @classmethod
    async def count_questions(cls, session: AsyncSession) -> int:
        """Подсчитать общее количество вопросов"""
        query = select(func.count()).select_from(cls.model)
        result = await session.execute(query)
        return result.scalar_one()
    
    @classmethod
    async def get_all_questions(
        cls, 
        session: AsyncSession, 
        skip: int = 0, 
        limit: int = 100, 
        tag: Optional[str] = None
    ) -> Tuple[List[Question], int]:
        """
        Получить все вопросы с возможностью пагинации и фильтрации по тегу
        
        Args:
            session: Сессия БД
            skip: Сколько вопросов пропустить (для пагинации)
            limit: Максимальное количество вопросов для возврата
            tag: Фильтр по тегу вопроса
            
        Returns:
            Tuple[List[Question], int]: Список вопросов и общее количество
        """
        # Базовый запрос
        query = select(cls.model)
        
        # Применяем фильтр по тегу, если указан
        if tag:
            query = query.filter(cls.model.tag == tag)
            
        # Запрос на подсчет общего количества с учетом фильтров
        count_query = select(func.count()).select_from(query.subquery())
        total = await session.scalar(count_query)
        
        # Применяем пагинацию
        query = query.offset(skip).limit(limit)
        
        # Выполняем запрос
        result = await session.execute(query)
        questions = result.scalars().all()
        
        return list(questions), total


class InterviewDAO(BaseDAO):
    model = Interview
    
    @classmethod
    async def get_interview_with_answers(cls, session: AsyncSession, interview_id: int) -> Optional[Interview]:
        """Получить интервью со всеми ответами"""
        query = select(cls.model).filter(cls.model.id == interview_id).options(
            # Загружаем связанные ответы
            # Используем selectinload для оптимизации запросов
            # Но в данном случае можно использовать и обычный relationship
            # Так как количество ответов обычно небольшое
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()
    
    @classmethod
    async def calculate_interview_score(cls, session: AsyncSession, interview_id: int) -> float:
        """Рассчитать общую оценку интервью на основе ответов"""
        query = select(func.avg(UserAnswer.score)).filter(UserAnswer.interview_id == interview_id)
        result = await session.execute(query)
        avg_score = result.scalar_one_or_none()
        return avg_score if avg_score is not None else 0.0


class UserAnswerDAO(BaseDAO):
    model = UserAnswer
    
    @classmethod
    async def get_answered_question_ids(cls, session: AsyncSession, interview_id: int) -> List[int]:
        """Получить ID вопросов, на которые уже ответили в данном интервью"""
        query = select(cls.model.question_id).filter(cls.model.interview_id == interview_id)
        result = await session.execute(query)
        return result.scalars().all()
    
    @classmethod
    async def count_answers(cls, session: AsyncSession, interview_id: int) -> int:
        """Подсчитать количество ответов в интервью"""
        query = select(func.count()).filter(cls.model.interview_id == interview_id)
        result = await session.execute(query)
        return result.scalar_one()
    
    @classmethod
    async def evaluate_answer(cls, session: AsyncSession, question: Question, user_answer: str) -> tuple[float, str]:
        """Оценить ответ пользователя с помощью GigaChat"""
        gigachat_service = GigaChatService()
        return await gigachat_service.evaluate_answer(
            question=question.question,
            user_answer=user_answer
        ) 