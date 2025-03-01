from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.dao import DirectionsDAO, LanguagesDAO
from app.auth.models import Direction, Language
from app.auth.schemas import DirectionCreate, LanguageCreate


async def init_directions(session: AsyncSession):
    """Инициализация направлений в базе данных"""
    directions = [
        DirectionCreate(name="Frontend"),
        DirectionCreate(name="Backend"),
        DirectionCreate(name="DevOps"),
        DirectionCreate(name="Data Science"),
        DirectionCreate(name="Mobile Development"),
        DirectionCreate(name="QA"),
        DirectionCreate(name="UI/UX Design"),
    ]
    
    for direction in directions:
        # Проверяем, существует ли уже такое направление
        existing = await DirectionsDAO.find_one_or_none(
            session=session, 
            filters=DirectionCreate(name=direction.name)
        )
        if not existing:
            await DirectionsDAO.add(session=session, values=direction)


async def init_languages(session: AsyncSession):
    """Инициализация языков программирования в базе данных"""
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
    
    for language in languages:
        # Проверяем, существует ли уже такой язык
        existing = await LanguagesDAO.find_one_or_none(
            session=session, 
            filters=LanguageCreate(name=language.name)
        )
        if not existing:
            await LanguagesDAO.add(session=session, values=language)


async def init_data(session: AsyncSession):
    """Инициализация всех начальных данных"""
    await init_directions(session)
    await init_languages(session) 