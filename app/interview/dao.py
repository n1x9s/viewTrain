from app.dao.base import BaseDAO
from app.interview.models import PythonQuestion, GolangQuestion, Interview, UserAnswer
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, text, literal_column, and_, union_all
from sqlalchemy.orm import selectinload
import random
from typing import List, Optional, Tuple, Dict, Type, Any, Union
from app.services.gigachat import GigaChatService
import logging

logger = logging.getLogger(__name__)


class QuestionDAO(BaseDAO):
    # Словарь соответствия типов вопросов и моделей
    question_models = {"pythonn": PythonQuestion, "golangquestions": GolangQuestion}

    # Дефолтная модель для совместимости со старым кодом
    model = PythonQuestion

    @classmethod
    def get_model_by_type(cls, question_type: str):
        """Получить модель вопроса по типу"""
        return cls.question_models.get(question_type, cls.model)

    @classmethod
    def get_question_type_for_user(cls, user) -> str:
        """
        Определить тип вопросов для пользователя на основе его языка и направления
        """
        # Безопасно получаем языки и направления пользователя
        if not hasattr(user, "languages") or user.languages is None:
            # Если у пользователя нет атрибута languages или он None
            user_languages = []
        else:
            # Преобразуем языки в строки нижнего регистра
            user_languages = [
                lang.name.lower() for lang in user.languages if hasattr(lang, "name")
            ]

        if not hasattr(user, "directions") or user.directions is None:
            # Если у пользователя нет атрибута directions или он None
            user_directions = []
        else:
            # Преобразуем направления в строки нижнего регистра
            user_directions = [
                direction.name.lower()
                for direction in user.directions
                if hasattr(direction, "name")
            ]

        # Для Go разработчиков
        if (
            any(lang in ["go", "golang"] for lang in user_languages)
            and "backend" in user_directions
        ):
            return "golangquestions"

        # По умолчанию используем Python
        return "pythonn"

    @classmethod
    async def get_random_question(
        cls,
        session: AsyncSession,
        question_type: str = "pythonn",
        exclude_ids: List[int] = None,
    ) -> Optional[Any]:
        """Получить случайный вопрос, исключая уже отвеченные"""
        model = cls.get_model_by_type(question_type)
        query = select(model)

        if exclude_ids and len(exclude_ids) > 0:
            query = query.filter(model.id.not_in(exclude_ids))

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
    async def find_one_or_none_by_id(
        cls, data_id: int, session: AsyncSession, question_type: str = "pythonn"
    ) -> Optional[Any]:
        """Найти вопрос по ID и типу"""
        model = cls.get_model_by_type(question_type)
        query = select(model).filter(model.id == data_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def count_questions(
        cls, session: AsyncSession, question_type: str = "pythonn"
    ) -> int:
        """Подсчитать общее количество вопросов определенного типа"""
        model = cls.get_model_by_type(question_type)
        query = select(func.count()).select_from(model)
        result = await session.execute(query)
        return result.scalar_one()

    @classmethod
    async def get_all_questions(
        cls,
        session: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        tag: Optional[str] = None,
        question_type: str = "pythonn",
    ) -> Tuple[List[Any], int]:
        """
        Получить все вопросы с возможностью пагинации и фильтрации по тегу

        Args:
            session: Сессия БД
            skip: Сколько вопросов пропустить (для пагинации)
            limit: Максимальное количество вопросов для возврата
            tag: Фильтр по тегу вопроса
            question_type: Тип вопросов (pythonn или golangquestions)

        Returns:
            Tuple[List[Any], int]: Список вопросов и общее количество
        """
        # Получаем модель для нужного типа вопросов
        model = cls.get_model_by_type(question_type)

        # Базовый запрос
        query = select(model)

        # Применяем фильтр по тегу, если указан
        if tag:
            query = query.filter(model.tag == tag)

        # Запрос на подсчет общего количества с учетом фильтров
        count_query = select(func.count()).select_from(query.subquery())
        total = await session.scalar(count_query)

        # Применяем пагинацию
        query = query.offset(skip).limit(limit)

        # Выполняем запрос
        result = await session.execute(query)
        questions = result.scalars().all()

        return list(questions), total

    @classmethod
    async def get_questions_by_ids(
        cls,
        session: AsyncSession,
        question_ids: List[int],
        question_type: str = "pythonn",
    ) -> List[Any]:
        """Получить вопросы по списку ID и типу"""
        if not question_ids:
            return []

        model = cls.get_model_by_type(question_type)
        query = select(model).filter(model.id.in_(question_ids))
        result = await session.execute(query)
        return result.scalars().all()

    @classmethod
    async def get_question_by_id_and_type(
        cls, session: AsyncSession, question_id: int, question_type: str
    ) -> Union[PythonQuestion, GolangQuestion, None]:
        """
        Получить вопрос по ID и типу

        Args:
            session: Сессия БД
            question_id: ID вопроса
            question_type: Тип вопроса (pythonn или golangquestions)

        Returns:
            Объект вопроса или None
        """
        model = cls.get_model_by_type(question_type)
        query = select(model).filter(model.id == question_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()


class InterviewDAO(BaseDAO):
    model = Interview

    @classmethod
    async def get_interview_with_answers(
        cls, session: AsyncSession, interview_id: int
    ) -> Optional[Interview]:
        """Получить интервью со всеми ответами"""
        query = (
            select(cls.model)
            .filter(cls.model.id == interview_id)
            .options(selectinload(cls.model.answers))
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def calculate_interview_score(
        cls, session: AsyncSession, interview_id: int
    ) -> float:
        """Рассчитать общую оценку интервью на основе ответов"""
        query = select(func.avg(UserAnswer.score)).filter(
            UserAnswer.interview_id == interview_id
        )
        result = await session.execute(query)
        avg_score = result.scalar_one_or_none()
        return avg_score if avg_score is not None else 0.0


class UserAnswerDAO(BaseDAO):
    model = UserAnswer

    @classmethod
    async def get_answered_question_ids(
        cls, session: AsyncSession, interview_id: int
    ) -> List[int]:
        """Получить ID вопросов, на которые уже ответили в данном интервью"""
        query = select(cls.model.question_id).filter(
            cls.model.interview_id == interview_id
        )
        result = await session.execute(query)
        return result.scalars().all()

    @classmethod
    async def count_answers(cls, session: AsyncSession, interview_id: int) -> int:
        """Подсчитать количество ответов в интервью"""
        query = select(func.count()).filter(cls.model.interview_id == interview_id)
        result = await session.execute(query)
        return result.scalar_one()

    @classmethod
    async def evaluate_answer(
        cls,
        session: AsyncSession,
        question: Union[PythonQuestion, GolangQuestion],
        user_answer: str,
    ) -> tuple[float, str]:
        """Оценить ответ пользователя с помощью GigaChat"""
        gigachat_service = GigaChatService()
        return await gigachat_service.evaluate_answer(
            question=question.question, user_answer=user_answer
        )

    @classmethod
    async def find_one_or_none(
        cls,
        session: AsyncSession,
        interview_id: Optional[int] = None,
        question_id: Optional[int] = None,
        question_type: Optional[str] = None,
        **filter_by,
    ) -> Optional[model]:
        """
        Найти ответ пользователя по заданным параметрам
        """
        filters = []

        if interview_id is not None:
            filters.append(cls.model.interview_id == interview_id)

        if question_id is not None:
            filters.append(cls.model.question_id == question_id)

        if question_type is not None:
            filters.append(cls.model.question_type == question_type)

        if filter_by:
            for key, value in filter_by.items():
                filters.append(getattr(cls.model, key) == value)

        query = select(cls.model)
        for f in filters:
            query = query.filter(f)

        result = await session.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def get_answer_with_question(
        cls, session: AsyncSession, answer_id: int
    ) -> Dict[str, Any]:
        """
        Получить ответ пользователя вместе с соответствующим вопросом

        Args:
            session: Сессия БД
            answer_id: ID ответа

        Returns:
            Словарь с информацией об ответе и вопросе
        """
        # Сначала получаем ответ
        query = select(cls.model).filter(cls.model.id == answer_id)
        result = await session.execute(query)
        answer = result.scalar_one_or_none()

        if not answer:
            return None

        # Получаем вопрос соответствующего типа
        question = await QuestionDAO.get_question_by_id_and_type(
            session, answer.question_id, answer.question_type
        )

        if not question:
            return {"answer": answer, "question": None}

        return {"answer": answer, "question": question}
