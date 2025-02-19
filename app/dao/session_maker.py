from contextlib import asynccontextmanager
from typing import Callable, Optional, AsyncGenerator
from fastapi import Depends
from loguru import logger
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from sqlalchemy import text
from functools import wraps

from app.dao.database import async_session_maker


class DatabaseSessionManager:

    def __init__(self, session_maker: async_sessionmaker[AsyncSession]):
        self.session_maker = session_maker

    @asynccontextmanager
    async def create_session(self) -> AsyncGenerator[AsyncSession, None]:

        async with self.session_maker() as session:
            try:
                yield session
            except Exception as e:
                logger.error(f"Ошибка при создании сессии базы данных: {e}")
                raise
            finally:
                await session.close()

    @asynccontextmanager
    async def transaction(self, session: AsyncSession) -> AsyncGenerator[None, None]:

        try:
            yield
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.exception(f"Ошибка транзакции: {e}")
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
                async with self.session_maker() as session:
                    try:
                        if isolation_level:
                            await session.execute(text(f"SET TRANSACTION ISOLATION LEVEL {isolation_level}"))

                        result = await method(*args, session=session, **kwargs)

                        if commit:
                            await session.commit()

                        return result
                    except Exception as e:
                        await session.rollback()
                        logger.error(f"Ошибка при выполнении транзакции: {e}")
                        raise
                    finally:
                        await session.close()

            return wrapper

        return decorator

    @property
    def session_dependency(self) -> Callable:
        return Depends(self.get_session)

    @property
    def transaction_session_dependency(self) -> Callable:
        return Depends(self.get_transaction_session)


session_manager = DatabaseSessionManager(async_session_maker)

SessionDep = session_manager.session_dependency
TransactionSessionDep = session_manager.transaction_session_dependency

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
