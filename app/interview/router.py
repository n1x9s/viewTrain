from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.dao.session_maker import SessionDep, TransactionSessionDep
from app.interview.schemas import (
    InterviewStart, QuestionResponse, AnswerRequest, 
    AnswerResponse, InterviewStatus, InterviewFinish,
    InterviewCreate, UserAnswerCreate
)
from app.interview.dao import QuestionDAO, InterviewDAO, UserAnswerDAO
from app.interview.models import Interview, UserAnswer, InterviewStatus as InterviewStatusEnum
from app.auth.dependencies import get_current_user
from app.auth.models import User
import logging
from sqlalchemy import text

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/interview", tags=["interview"])


@router.get("/start", response_model=InterviewStart)
async def start_interview(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = TransactionSessionDep
):
    """Начать новое интервью"""
    # Создаем новое интервью
    new_interview = Interview(
        user_id=current_user.id,
        status=InterviewStatusEnum.ONGOING
    )
    
    # Добавляем в базу данных
    session.add(new_interview)
    await session.flush()
    
    return InterviewStart(
        interview_id=new_interview.id,
        status="ongoing",
        message="Interview started"
    )


@router.get("/question", response_model=QuestionResponse)
async def get_question(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = SessionDep
):
    """Получить следующий вопрос для текущего интервью"""
    # Находим активное интервью пользователя
    query = await session.execute(
        text("SELECT id FROM interviews WHERE user_id = :user_id AND status = :status ORDER BY id DESC LIMIT 1"),
        {"user_id": current_user.id, "status": InterviewStatusEnum.ONGOING}
    )
    interview_id = query.scalar_one_or_none()
    
    if not interview_id:
        raise HTTPException(status_code=404, detail="Активное интервью не найдено. Начните новое интервью.")
    
    # Получаем ID вопросов, на которые уже ответили
    answered_question_ids = await UserAnswerDAO.get_answered_question_ids(session, interview_id)
    
    # Получаем случайный вопрос, исключая уже отвеченные
    question = await QuestionDAO.get_random_question(session, exclude_ids=answered_question_ids)
    
    if not question:
        # Если все вопросы отвечены, завершаем интервью
        interview = await InterviewDAO.find_one_or_none_by_id(interview_id, session)
        if interview:
            interview.status = InterviewStatusEnum.COMPLETED
            await session.flush()
        raise HTTPException(status_code=404, detail="Все вопросы уже отвечены. Интервью завершено.")
    
    return QuestionResponse(
        question_id=question.id,
        question_text=question.question,
        tag=question.tag
    )


@router.post("/answer", response_model=AnswerResponse)
async def submit_answer(
    answer_data: AnswerRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = TransactionSessionDep
):
    """Отправить ответ на вопрос"""
    # Находим активное интервью пользователя
    query = await session.execute(
        text("SELECT id FROM interviews WHERE user_id = :user_id AND status = :status ORDER BY id DESC LIMIT 1"),
        {"user_id": current_user.id, "status": InterviewStatusEnum.ONGOING}
    )
    interview_id = query.scalar_one_or_none()
    
    if not interview_id:
        raise HTTPException(status_code=404, detail="Активное интервью не найдено. Начните новое интервью.")
    
    # Проверяем, что вопрос существует
    question = await QuestionDAO.find_one_or_none_by_id(answer_data.question_id, session)
    if not question:
        raise HTTPException(status_code=404, detail="Вопрос не найден")
    
    # Проверяем, не отвечал ли пользователь уже на этот вопрос
    existing_answer = await UserAnswerDAO.find_one_or_none(
        session, 
        interview_id=interview_id, 
        question_id=answer_data.question_id
    )
    
    if existing_answer:
        raise HTTPException(status_code=400, detail="Вы уже ответили на этот вопрос")
    
    # Оцениваем ответ
    score, feedback = await UserAnswerDAO.evaluate_answer(session, question, answer_data.user_answer)
    
    # Сохраняем ответ
    user_answer = UserAnswer(
        interview_id=interview_id,
        question_id=answer_data.question_id,
        user_answer=answer_data.user_answer,
        score=score,
        feedback=feedback
    )
    
    session.add(user_answer)
    await session.flush()
    
    return AnswerResponse(
        score=score,
        feedback=feedback
    )


@router.get("/status", response_model=InterviewStatus)
async def get_interview_status(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = SessionDep
):
    """Получить статус текущего интервью"""
    # Находим активное интервью пользователя
    query = await session.execute(
        text("SELECT id FROM interviews WHERE user_id = :user_id AND status = :status ORDER BY id DESC LIMIT 1"),
        {"user_id": current_user.id, "status": InterviewStatusEnum.ONGOING}
    )
    interview_id = query.scalar_one_or_none()
    
    if not interview_id:
        raise HTTPException(status_code=404, detail="Активное интервью не найдено. Начните новое интервью.")
    
    # Подсчитываем количество отвеченных вопросов
    answered_questions = await UserAnswerDAO.count_answers(session, interview_id)
    
    # Получаем общее количество вопросов
    total_questions = await QuestionDAO.count_questions(session)
    
    # Вычисляем прогресс
    progress = f"{int(answered_questions / total_questions * 100)}%" if total_questions > 0 else "0%"
    
    return InterviewStatus(
        interview_id=interview_id,
        answered_questions=answered_questions,
        total_questions=total_questions,
        progress=progress
    )


@router.get("/finish", response_model=InterviewFinish)
async def finish_interview(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = TransactionSessionDep
):
    """Завершить текущее интервью"""
    # Находим активное интервью пользователя
    query = await session.execute(
        text("SELECT id FROM interviews WHERE user_id = :user_id AND status = :status ORDER BY id DESC LIMIT 1"),
        {"user_id": current_user.id, "status": InterviewStatusEnum.ONGOING}
    )
    interview_id = query.scalar_one_or_none()
    
    if not interview_id:
        raise HTTPException(status_code=404, detail="Активное интервью не найдено. Начните новое интервью.")
    
    # Получаем интервью
    interview = await InterviewDAO.find_one_or_none_by_id(interview_id, session)
    
    # Рассчитываем итоговую оценку
    score = await InterviewDAO.calculate_interview_score(session, interview_id)
    score_percentage = int(score * 100)
    
    # Формируем обратную связь
    if score > 0.8:
        feedback = "Отличный результат! Вы хорошо знаете материал."
    elif score > 0.6:
        feedback = "Хороший результат! Подтяните некоторые темы для улучшения."
    elif score > 0.4:
        feedback = "Средний результат. Рекомендуем повторить основные темы."
    else:
        feedback = "Результат ниже среднего. Рекомендуем дополнительное изучение материала."
    
    # Обновляем интервью
    interview.status = InterviewStatusEnum.COMPLETED
    interview.total_score = score
    interview.feedback = feedback
    
    await session.flush()
    
    return InterviewFinish(
        interview_id=interview_id,
        score=score_percentage,
        feedback=feedback
    )
