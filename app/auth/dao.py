from app.dao.base import BaseDAO
from app.auth.models import User, Direction, Language
from sqlalchemy.ext.asyncio import AsyncSession


class UsersDAO(BaseDAO):
    model = User

    @classmethod
    async def add(cls, session: AsyncSession, obj: User) -> None:
        session.add(obj)
        await session.flush()


class DirectionsDAO(BaseDAO):
    model = Direction


class LanguagesDAO(BaseDAO):
    model = Language
