from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.dao.session_maker import get_async_session
from app.statistics.dao import StatisticsDAO
from app.statistics.schemas import (
    InterviewStatistics,
    QuestionsStatistics,
    TopQuestionsStatistics,
    QuestionStatItem,
    QuestionBase,
    QuestionDetail
)
from fastapi_versioning import version

router = APIRouter(prefix="/statistics", tags=["statistics"])


@router.get("/interviews", response_model=InterviewStatistics)
@version(1)
async def get_interview_statistics(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Получить статистику по всем интервью пользователя.
    
    Возвращает:
    - общее количество завершенных интервью
    - процент успешных интервью (с оценкой >= 0.6)
    - процент неуспешных интервью (с оценкой < 0.6)
    """
    stats = await StatisticsDAO.get_interview_statistics(session, current_user.id)
    return InterviewStatistics(**stats)


@router.get("/questions", response_model=QuestionsStatistics)
@version(1)
async def get_questions_statistics(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Получить статистику по ответам на вопросы.
    
    Возвращает:
    - общее количество отвеченных вопросов
    - процент успешных ответов (с оценкой >= 0.6)
    - процент неуспешных ответов (с оценкой < 0.6)
    - процент пропущенных вопросов
    """
    stats = await StatisticsDAO.get_questions_statistics(session, current_user.id)
    return QuestionsStatistics(**stats)


@router.get("/questions/top-successful", response_model=TopQuestionsStatistics)
@version(1)
async def get_top_successful_questions(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Получить топ-5 самых успешных вопросов для текущего пользователя.
    
    Возвращает список из 5 вопросов, на которые пользователь 
    чаще всего давал правильные ответы.
    """
    questions = await StatisticsDAO.get_top_successful_questions(session, current_user.id)
    return TopQuestionsStatistics(questions=[QuestionStatItem(**q) for q in questions])


@router.get("/questions/top-unsuccessful", response_model=TopQuestionsStatistics)
@version(1)
async def get_top_unsuccessful_questions(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Получить топ-5 самых неуспешных вопросов для текущего пользователя.
    
    Возвращает список из 5 вопросов, на которые пользователь 
    чаще всего давал неправильные ответы.
    """
    questions = await StatisticsDAO.get_top_unsuccessful_questions(session, current_user.id)
    return TopQuestionsStatistics(questions=[QuestionStatItem(**q) for q in questions])


@router.get("/questions/all", response_model=List[QuestionBase])
@version(1)
async def get_all_questions(
    tag: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Получить список всех вопросов из базы данных.
    
    Параметры:
    - tag: Опциональный фильтр по тегу вопроса
    
    Возвращает список вопросов с ID и текстом.
    """
    questions = await StatisticsDAO.get_all_questions(session, tag)
    return [QuestionBase(**q) for q in questions]


@router.get("/questions/{question_id}", response_model=QuestionDetail)
@version(1)
async def get_question_detail(
    question_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Получить детальную информацию о вопросе по его ID.
    
    Возвращает вопрос с ID, текстом вопроса и правильным ответом.
    """
    question = await StatisticsDAO.get_question_by_id(session, question_id)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Вопрос с ID {question_id} не найден"
        )
    return QuestionDetail(**question) 