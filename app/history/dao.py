from app.dao.base import BaseDAO
from app.interview.models import Interview
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import List, Optional


class InterviewHistoryDAO(BaseDAO):
    model = Interview
    
    @classmethod
    async def get_user_interview_history(cls, session: AsyncSession, user_id: int) -> List[Interview]:
        """Получить историю интервью пользователя"""
        query = (
            select(cls.model)
            .filter(
                cls.model.user_id == user_id,
                cls.model.status == "completed"
            )
            .order_by(cls.model.created_at.desc())
        )
        result = await session.execute(query)
        return result.scalars().all()
    
    @classmethod
    async def get_user_interview_detail(
        cls, 
        session: AsyncSession, 
        user_id: int, 
        user_interview_id: int
    ) -> Optional[Interview]:
        """Получить детальную информацию об интервью пользователя"""
        query = (
            select(cls.model)
            .filter(
                cls.model.user_id == user_id,
                cls.model.user_interview_id == user_interview_id,
                cls.model.status == "completed"
            )
            .options(selectinload(cls.model.answers))
        )
        result = await session.execute(query)
        return result.scalar_one_or_none() 