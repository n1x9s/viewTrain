from app.dao.base import BaseDAO
from app.interview.models import Interview, UserAnswer, Question
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, case, Float, and_, text
from sqlalchemy.orm import selectinload
from typing import List, Dict, Tuple, Any, Optional


class StatisticsDAO(BaseDAO):
    
    @classmethod
    async def get_interview_statistics(cls, session: AsyncSession, user_id: int) -> Dict[str, float]:
        """Получить статистику по всем интервью пользователя"""
        # Получаем общее количество завершенных интервью
        query_total = select(func.count(Interview.id)).where(
            Interview.user_id == user_id,
            Interview.status == "completed"
        )
        result_total = await session.execute(query_total)
        total_interviews = result_total.scalar() or 0
        
        if total_interviews == 0:
            return {
                "total_interviews": 0,
                "successful_percent": 0.0,
                "unsuccessful_percent": 0.0
            }
        
        # Считаем количество успешных интервью (с оценкой >= 0.6)
        query_successful = select(func.count(Interview.id)).where(
            Interview.user_id == user_id,
            Interview.status == "completed",
            Interview.total_score >= 0.6
        )
        result_successful = await session.execute(query_successful)
        successful_interviews = result_successful.scalar() or 0
        
        # Вычисляем проценты
        successful_percent = round((successful_interviews / total_interviews) * 100, 2)
        unsuccessful_percent = round(100 - successful_percent, 2)
        
        return {
            "total_interviews": total_interviews,
            "successful_percent": successful_percent,
            "unsuccessful_percent": unsuccessful_percent
        }
    
    @classmethod
    async def get_questions_statistics(cls, session: AsyncSession, user_id: int) -> Dict[str, float]:
        """Получить статистику по ответам на вопросы"""
        # Получаем все ответы пользователя через его интервью
        query = select(UserAnswer).join(
            Interview, UserAnswer.interview_id == Interview.id
        ).where(
            Interview.user_id == user_id,
            Interview.status == "completed"
        )
        
        result = await session.execute(query)
        answers = result.scalars().all()
        
        total_questions = len(answers)
        
        if total_questions == 0:
            return {
                "total_questions": 0,
                "successful_percent": 0.0,
                "unsuccessful_percent": 0.0,
                "skipped_percent": 0.0
            }
        
        # Считаем успешные ответы (с оценкой >= 0.6)
        successful_answers = sum(1 for answer in answers if answer.score and answer.score >= 0.6)
        
        # Считаем пропущенные вопросы (тексты ответов пустые или содержат фразу о пропуске)
        skipped_answers = sum(1 for answer in answers if 
                             not answer.user_answer or 
                             answer.user_answer.strip().lower() in ['skip', 'пропустить', 'не знаю'])
        
        # Неуспешные - это оставшиеся
        unsuccessful_answers = total_questions - successful_answers - skipped_answers
        
        # Вычисляем проценты
        successful_percent = round((successful_answers / total_questions) * 100, 2)
        unsuccessful_percent = round((unsuccessful_answers / total_questions) * 100, 2)
        skipped_percent = round((skipped_answers / total_questions) * 100, 2)
        
        return {
            "total_questions": total_questions,
            "successful_percent": successful_percent,
            "unsuccessful_percent": unsuccessful_percent,
            "skipped_percent": skipped_percent
        }
    
    @classmethod
    async def get_top_successful_questions(cls, session: AsyncSession, user_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """Получить топ-5 самых успешных вопросов"""
        return await cls._get_top_questions(session, user_id, limit, is_successful=True)
    
    @classmethod
    async def get_top_unsuccessful_questions(cls, session: AsyncSession, user_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """Получить топ-5 самых неуспешных вопросов"""
        return await cls._get_top_questions(session, user_id, limit, is_successful=False)
    
    @classmethod
    async def _get_top_questions(
        cls, 
        session: AsyncSession, 
        user_id: int, 
        limit: int = 5, 
        is_successful: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Получить топ вопросов по успешности/неуспешности
        
        Args:
            session: Сессия БД
            user_id: ID пользователя
            limit: Количество вопросов в выборке
            is_successful: True для успешных, False для неуспешных
        """
        # Подзапрос для получения статистики по каждому вопросу
        subquery = select(
            UserAnswer.question_id,
            func.count(UserAnswer.id).label('answer_count'),
            func.avg(
                case(
                    (UserAnswer.score >= 0.6, 1.0),
                    else_=0.0
                )
            ).label('success_rate')
        ).join(
            Interview, UserAnswer.interview_id == Interview.id
        ).where(
            Interview.user_id == user_id,
            Interview.status == "completed"
        ).group_by(
            UserAnswer.question_id
        ).having(
            func.count(UserAnswer.id) > 0
        ).subquery()
        
        # Запрос для получения полной информации о вопросах
        query = select(
            Question.id.label('question_id'),
            Question.question.label('question_text'),
            Question.tag,
            subquery.c.success_rate,
            subquery.c.answer_count
        ).join(
            subquery, Question.id == subquery.c.question_id
        )
        
        # Сортировка в зависимости от того, ищем ли успешные или неуспешные вопросы
        if is_successful:
            query = query.order_by(subquery.c.success_rate.desc())
        else:
            query = query.order_by(subquery.c.success_rate.asc())
        
        query = query.limit(limit)
        
        result = await session.execute(query)
        questions = result.mappings().all()
        
        # Преобразуем результат в список словарей
        return [
            {
                "question_id": q['question_id'],
                "question_text": q['question_text'],
                "tag": q['tag'],
                "success_rate": round(float(q['success_rate']) * 100, 2),
                "answer_count": q['answer_count']
            } 
            for q in questions
        ] 