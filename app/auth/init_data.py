from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.dao import DirectionsDAO, LanguagesDAO
from app.auth.schemas import DirectionCreate, LanguageCreate
from app.auth.models import Direction, Language
import logging

logger = logging.getLogger(__name__)


async def init_directions(session: AsyncSession):
    """Инициализация направлений"""
    directions = [
        DirectionCreate(name="Frontend"),
        DirectionCreate(name="Backend"),
        DirectionCreate(name="DevOps"),
        DirectionCreate(name="Data Science"),
        DirectionCreate(name="Mobile Development"),
        DirectionCreate(name="QA"),
        DirectionCreate(name="UI/UX Design"),
    ]

    for direction_data in directions:
        # Проверяем существование направления
        existing = await DirectionsDAO.find_one_or_none(
            session=session, filters=DirectionCreate(name=direction_data.name)
        )
        if not existing:
            # Создаем новое направление
            direction = Direction(name=direction_data.name)
            await DirectionsDAO.add(session=session, obj=direction)


async def init_languages(session: AsyncSession):
    """Инициализация языков программирования"""
    languages = [
        LanguageCreate(name="Python"),
        LanguageCreate(name="JavaScript"),
        LanguageCreate(name="TypeScript"),
        LanguageCreate(name="Java"),
        LanguageCreate(name="C#"),
        LanguageCreate(name="C++"),
        LanguageCreate(name="Go"),
        LanguageCreate(name="Rust"),
        LanguageCreate(name="PHP"),
        LanguageCreate(name="Swift"),
        LanguageCreate(name="Kotlin"),
    ]

    for language_data in languages:
        # Проверяем существование языка
        existing = await LanguagesDAO.find_one_or_none(
            session=session, filters=LanguageCreate(name=language_data.name)
        )
        if not existing:
            # Создаем новый язык
            language = Language(name=language_data.name)
            await LanguagesDAO.add(session=session, obj=language)


async def init_data(session: AsyncSession):
    """Инициализация начальных данных"""
    try:
        await init_directions(session)
        await init_languages(session)
        await session.commit()
        logger.info("Initial data has been successfully loaded")
    except Exception as e:
        await session.rollback()
        logger.error(f"Error during data initialization: {e}")
        raise
