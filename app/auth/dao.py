from app.dao.base import BaseDAO
from app.auth.models import User, Direction, Language
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload


class UsersDAO(BaseDAO):
    model = User

    @classmethod
    async def add(cls, session: AsyncSession, obj: User) -> None:
        session.add(obj)
        await session.flush()
        
    @classmethod
    async def find_user_with_relations(cls, session: AsyncSession, user_id: int):
        """Найти пользователя с загрузкой languages и directions"""
        query = (
            select(cls.model)
            .options(
                selectinload(cls.model.languages),
                selectinload(cls.model.directions)
            )
            .filter_by(id=user_id)
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()


class DirectionsDAO(BaseDAO):
    model = Direction


class LanguagesDAO(BaseDAO):
    model = Language
