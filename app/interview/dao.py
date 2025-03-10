from app.dao.base import BaseDAO
from app.interview.models import Question, Interview, UserAnswer
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func
import random
from typing import List, Optional


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
        """Оценить ответ пользователя"""
        # Здесь можно реализовать более сложную логику оценки ответа
        # Например, использовать NLP или другие методы
        # В данном примере используется простая проверка на совпадение ключевых слов
        
        correct_answer = question.answer.lower()
        user_answer_lower = user_answer.lower()
        
        # Простая оценка на основе совпадения ключевых слов
        # В реальном приложении здесь может быть более сложная логика
        keywords = [word.strip() for word in correct_answer.split() if len(word.strip()) > 3]
        matched_keywords = sum(1 for keyword in keywords if keyword in user_answer_lower)
        
        if not keywords:
            score = 1.0 if user_answer_lower == correct_answer else 0.0
        else:
            score = min(1.0, matched_keywords / len(keywords))
        
        # Учитываем сложность вопроса, если она указана
        if question.chance is not None:
            # Если chance - это сложность, то более сложные вопросы дают больше баллов
            # Если chance - это вероятность, то более редкие вопросы дают больше баллов
            # В данном примере предполагаем, что chance - это сложность от 0 до 1
            score = score * (0.5 + 0.5 * question.chance)
        
        # Формируем обратную связь
        if score > 0.8:
            feedback = "Отличный ответ! Вы правильно описали ключевые аспекты."
        elif score > 0.5:
            feedback = "Хороший ответ, но можно было бы упомянуть больше ключевых моментов."
        else:
            feedback = f"Ответ неполный. Правильный ответ должен включать: {correct_answer}"
        
        return score, feedback 