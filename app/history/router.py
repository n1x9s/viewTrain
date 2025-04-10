from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.dao.session_maker import SessionDep
from app.history.schemas import (
    InterviewHistoryList,
    InterviewHistoryDetail,
    InterviewHistoryItem,
)
from app.history.dao import InterviewHistoryDAO
from app.auth.dependencies import get_current_user
from app.auth.models import User
from fastapi_versioning import version


router = APIRouter(prefix="/history", tags=["history"])


@router.get("", response_model=InterviewHistoryList)
@version(1)
async def get_interview_history(
    current_user: User = Depends(get_current_user), session: AsyncSession = SessionDep
):
    """Получить историю интервью пользователя"""
    interviews = await InterviewHistoryDAO.get_user_interview_history(
        session, current_user.id
    )

    history_items = [
        InterviewHistoryItem(
            id=interview.user_interview_id,
            date=interview.created_at,
            score=int(interview.total_score * 100) if interview.total_score else 0,
        )
        for interview in interviews
    ]

    return InterviewHistoryList(history=history_items)


@router.get("/{interview_id}", response_model=InterviewHistoryDetail)
@version(1)
async def get_interview_detail(
    interview_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = SessionDep,
):
    """Получить детальную информацию об интервью"""
    interview = await InterviewHistoryDAO.get_user_interview_detail(
        session, current_user.id, interview_id
    )

    if not interview:
        raise HTTPException(
            status_code=404,
            detail="Интервью не найдено или не принадлежит текущему пользователю",
        )

    return InterviewHistoryDetail(
        id=interview.user_interview_id,
        date=interview.created_at,
        score=int(interview.total_score * 100) if interview.total_score else 0,
        feedback=interview.feedback,
        answers=interview.answers,
    )
