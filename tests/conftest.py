import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from httpx import AsyncClient
import asyncio
from typing import AsyncGenerator, Generator
import os
import pytest_asyncio
from app.main import app
from app.dao.database import Base
from app.dao.session_maker import get_async_session
from app.auth.models import User, Direction, Language
from app.auth.dao import UsersDAO, DirectionsDAO, LanguagesDAO
from app.auth.auth import create_access_token

# Используем SQLite для тестов
DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def override_get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session


app.dependency_overrides[get_async_session] = override_get_async_session


@pytest_asyncio.fixture(scope="function")
async def async_session() -> AsyncGenerator[AsyncSession, None]:
    # Создаем таблицы в тестовой БД
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Создаем сессию
    async with TestingSessionLocal() as session:
        yield session
    
    # Очищаем таблицы после теста
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def test_client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture(scope="function")
async def test_user(async_session: AsyncSession) -> User:
    # Создаем тестовое направление
    direction = Direction(name="Test Direction")
    await DirectionsDAO.add(async_session, direction)
    
    # Создаем тестовый язык
    language = Language(name="Test Language")
    await LanguagesDAO.add(async_session, language)
    
    # Создаем тестового пользователя
    user = User(
        email="test@example.com",
        name="Test User",
    )
    await UsersDAO.add(async_session, user)
    
    # Связываем пользователя с направлением и языком
    user.directions.append(direction)
    user.languages.append(language)
    await async_session.commit()
    await async_session.refresh(user)
    
    return user


@pytest_asyncio.fixture(scope="function")
async def auth_headers(test_user: User) -> dict:
    # Создаем токен доступа
    token = create_access_token({"sub": str(test_user.id)})
    return {"Cookie": f"users_access_token={token}"}
