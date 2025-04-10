from contextlib import asynccontextmanager
from typing import Callable, Optional, AsyncGenerator
from fastapi import Depends
from loguru import logger
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine
from sqlalchemy import text
from functools import wraps
from sqlalchemy.orm import DeclarativeBase
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Создаем асинхронный движок
engine = create_async_engine(settings.DATABASE_URL, echo=False, pool_pre_ping=True)

# Создаем фабрику сессий
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class DatabaseSessionManager:
    def __init__(self, session_maker: async_sessionmaker[AsyncSession]):
        self.session_maker = session_maker

    @asynccontextmanager
    async def create_session(self) -> AsyncGenerator[AsyncSession, None]:
        async with self.session_maker() as session:
            try:
                yield session
            except Exception as e:
                await session.rollback()
                logger.error(f"Session rollback because of exception: {e}")
                raise
            finally:
                await session.close()

    @asynccontextmanager
    async def transaction(self, session: AsyncSession) -> AsyncGenerator[None, None]:
        try:
            await session.begin()
            yield
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Transaction rollback because of exception: {e}")
            raise

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        async with self.create_session() as session:
            yield session

    async def get_transaction_session(self) -> AsyncGenerator[AsyncSession, None]:
        async with self.create_session() as session:
            async with self.transaction(session):
                yield session

    def connection(self, isolation_level: Optional[str] = None, commit: bool = True):
        def decorator(method):
            @wraps(method)
            async def wrapper(*args, **kwargs):
                async with self.create_session() as session:
                    if isolation_level:
                        await session.execute(
                            text(f"SET TRANSACTION ISOLATION LEVEL {isolation_level}")
                        )

                    if commit:
                        async with self.transaction(session):
                            return await method(*args, session=session, **kwargs)
                    else:
                        return await method(*args, session=session, **kwargs)

            return wrapper

    @property
    def session_dependency(self) -> Callable:
        return Depends(self.get_session)

    @property
    def transaction_session_dependency(self) -> Callable:
        return Depends(self.get_transaction_session)


session_manager = DatabaseSessionManager(async_session_maker)
SessionDep = session_manager.session_dependency
TransactionSessionDep = session_manager.transaction_session_dependency


# Функция для получения сессии для инициализации данных
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Session rollback because of exception: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()


# Пример использования декоратора
# @session_manager.connection(isolation_level="SERIALIZABLE", commit=True)
# async def example_method(*args, session: AsyncSession, **kwargs):
#     # Логика метода
#     pass


# Пример использования зависимости
# @router.post("/register/")
# async def register_user(user_data: SUserRegister, session: AsyncSession = TransactionSessionDep):
#     # Логика эндпоинта
#     pass
