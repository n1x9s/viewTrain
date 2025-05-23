from app.dao.base import BaseDAO
from app.interview.models import Interview, UserAnswer, PythonQuestion, GolangQuestion
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, case, Float, and_, literal_column, text, union_all
from sqlalchemy.orm import selectinload, aliased
from typing import List, Dict, Tuple, Any, Optional
from sqlalchemy.sql.expression import select as select_expr


class StatisticsDAO(BaseDAO):

    @classmethod
    async def get_interview_statistics(
        cls, session: AsyncSession, user_id: int
    ) -> Dict[str, float]:
        """Получить статистику по всем интервью пользователя"""
        # Получаем общее количество завершенных интервью
        query_total = select(func.count(Interview.id)).where(
            Interview.user_id == user_id, Interview.status == "completed"
        )
        result_total = await session.execute(query_total)
        total_interviews = result_total.scalar() or 0

        if total_interviews == 0:
            return {
                "total_interviews": 0,
                "successful_percent": 0.0,
                "unsuccessful_percent": 0.0,
            }

        # Считаем количество успешных интервью (с оценкой >= 0.6)
        query_successful = select(func.count(Interview.id)).where(
            Interview.user_id == user_id,
            Interview.status == "completed",
            Interview.total_score >= 0.6,
        )
        result_successful = await session.execute(query_successful)
        successful_interviews = result_successful.scalar() or 0

        # Вычисляем проценты
        successful_percent = round((successful_interviews / total_interviews) * 100, 2)
        unsuccessful_percent = round(100 - successful_percent, 2)

        return {
            "total_interviews": total_interviews,
            "successful_percent": successful_percent,
            "unsuccessful_percent": unsuccessful_percent,
        }

    @classmethod
    async def get_questions_statistics(
        cls, session: AsyncSession, user_id: int
    ) -> Dict[str, float]:
        """Получить статистику по ответам на вопросы"""
        # Получаем все ответы пользователя через его интервью
        query = (
            select(UserAnswer)
            .join(Interview, UserAnswer.interview_id == Interview.id)
            .where(Interview.user_id == user_id, Interview.status == "completed")
        )

        result = await session.execute(query)
        answers = result.scalars().all()

        total_questions = len(answers)

        if total_questions == 0:
            return {
                "total_questions": 0,
                "successful_percent": 0.0,
                "unsuccessful_percent": 0.0,
                "skipped_percent": 0.0,
            }

        # Считаем успешные ответы (с оценкой >= 0.6)
        successful_answers = sum(
            1 for answer in answers if answer.score and answer.score >= 0.6
        )

        # Считаем пропущенные вопросы (тексты ответов пустые или содержат фразу о пропуске)
        skipped_answers = sum(
            1
            for answer in answers
            if not answer.user_answer
            or answer.user_answer.strip().lower() in ["skip", "пропустить", "не знаю"]
        )

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
            "skipped_percent": skipped_percent,
        }

    @classmethod
    async def get_top_successful_questions(
        cls, session: AsyncSession, user_id: int, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Получить топ-5 самых успешных вопросов"""
        return await cls._get_top_questions(session, user_id, limit, is_successful=True)

    @classmethod
    async def get_top_unsuccessful_questions(
        cls, session: AsyncSession, user_id: int, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Получить топ-5 самых неуспешных вопросов"""
        return await cls._get_top_questions(
            session, user_id, limit, is_successful=False
        )

    @classmethod
    async def _get_top_questions(
        cls,
        session: AsyncSession,
        user_id: int,
        limit: int = 5,
        is_successful: bool = True,
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
        subquery = (
            select(
                UserAnswer.question_id,
                UserAnswer.question_type,
                func.count(UserAnswer.id).label("answer_count"),
                func.avg(case((UserAnswer.score >= 0.6, 1.0), else_=0.0)).label(
                    "success_rate"
                ),
            )
            .join(Interview, UserAnswer.interview_id == Interview.id)
            .where(Interview.user_id == user_id, Interview.status == "completed")
            .group_by(UserAnswer.question_id, UserAnswer.question_type)
            .having(func.count(UserAnswer.id) > 0)
            .subquery()
        )

        # Запрос для получения полной информации о вопросах Python
        python_query = select(
            PythonQuestion.id.label("question_id"),
            PythonQuestion.question.label("question_text"),
            PythonQuestion.tag,
            subquery.c.success_rate,
            subquery.c.answer_count,
            literal_column("'pythonn'").label("question_type"),
        ).join(
            subquery,
            and_(
                PythonQuestion.id == subquery.c.question_id,
                subquery.c.question_type == "pythonn",
            ),
        )

        # Запрос для получения полной информации о вопросах Golang
        golang_query = select(
            GolangQuestion.id.label("question_id"),
            GolangQuestion.question.label("question_text"),
            GolangQuestion.tag,
            subquery.c.success_rate,
            subquery.c.answer_count,
            literal_column("'golangquestions'").label("question_type"),
        ).join(
            subquery,
            and_(
                GolangQuestion.id == subquery.c.question_id,
                subquery.c.question_type == "golangquestions",
            ),
        )

        # Объединяем запросы
        union_query = union_all(python_query, golang_query).alias()

        # Создаем финальный запрос с сортировкой
        query = select(
            union_query.c.question_id,
            union_query.c.question_text,
            union_query.c.tag,
            union_query.c.success_rate,
            union_query.c.answer_count,
            union_query.c.question_type,
        )

        # Сортировка в зависимости от того, ищем ли успешные или неуспешные вопросы
        if is_successful:
            query = query.order_by(union_query.c.success_rate.desc())
        else:
            query = query.order_by(union_query.c.success_rate.asc())

        query = query.limit(limit)

        result = await session.execute(query)
        questions = result.mappings().all()

        # Преобразуем результат в список словарей
        return [
            {
                "question_id": q["question_id"],
                "question_text": q["question_text"],
                "tag": q["tag"],
                "success_rate": round(float(q["success_rate"]) * 100, 2),
                "answer_count": q["answer_count"],
                "question_type": q["question_type"],
            }
            for q in questions
        ]

    @classmethod
    async def get_all_questions(
        cls, session: AsyncSession, tag: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Получить список всех вопросов

        Args:
            session: Сессия БД
            tag: Опциональный фильтр по тегу вопроса

        Returns:
            Список вопросов с ID и текстом
        """
        # Запрос для Python вопросов
        python_query = select(
            PythonQuestion.id,
            PythonQuestion.question,
            PythonQuestion.tag,
            literal_column("'pythonn'").label("question_type"),
        )

        if tag:
            python_query = python_query.where(PythonQuestion.tag == tag)

        # Запрос для Golang вопросов
        golang_query = select(
            GolangQuestion.id,
            GolangQuestion.question,
            GolangQuestion.tag,
            literal_column("'golangquestions'").label("question_type"),
        )

        if tag:
            golang_query = golang_query.where(GolangQuestion.tag == tag)

        # Объединяем запросы
        union_query = union_all(python_query, golang_query).alias()

        # Финальный запрос с сортировкой
        query = select(
            union_query.c.id,
            union_query.c.question,
            union_query.c.tag,
            union_query.c.question_type,
        ).order_by(union_query.c.id)

        result = await session.execute(query)
        questions = result.all()

        return [
            {
                "id": q.id,
                "question": q.question,
                "tag": q.tag,
                "question_type": q.question_type,
            }
            for q in questions
        ]

    @classmethod
    async def get_question_by_id(
        cls, session: AsyncSession, question_id: int, question_type: str = "pythonn"
    ) -> Optional[Dict[str, Any]]:
        """
        Получить детальную информацию о вопросе по его ID

        Args:
            session: Сессия БД
            question_id: ID вопроса
            question_type: Тип вопроса ('pythonn' или 'golangquestions')

        Returns:
            Словарь с информацией о вопросе или None, если вопрос не найден
        """
        if question_type == "pythonn":
            query = select(PythonQuestion).where(PythonQuestion.id == question_id)
        else:
            query = select(GolangQuestion).where(GolangQuestion.id == question_id)

        result = await session.execute(query)
        question = result.scalar_one_or_none()

        if not question:
            return None

        return {
            "id": question.id,
            "question": question.question,
            "tag": question.tag,
            "answer": question.answer,
            "question_type": question_type,
        }
