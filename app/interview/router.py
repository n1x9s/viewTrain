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
import random

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/interview", tags=["interview"])

# Константа для количества вопросов в интервью
QUESTIONS_PER_INTERVIEW = 10


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
    
    # Получаем все вопросы
    query = await session.execute(text("SELECT id FROM pythonn"))
    all_question_ids = query.scalars().all()
    
    # Выбираем 10 случайных вопросов, если их больше 10
    if len(all_question_ids) > QUESTIONS_PER_INTERVIEW:
        selected_question_ids = random.sample(all_question_ids, QUESTIONS_PER_INTERVIEW)
    else:
        selected_question_ids = all_question_ids
    
    # Сохраняем выбранные вопросы в атрибуте интервью
    await session.execute(
        text("UPDATE interviews SET question_ids = :question_ids WHERE id = :id"),
        {"question_ids": ','.join(map(str, selected_question_ids)), "id": new_interview.id}
    )
    
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
        text("SELECT id, question_ids FROM interviews WHERE user_id = :user_id AND status = :status ORDER BY id DESC LIMIT 1"),
        {"user_id": current_user.id, "status": InterviewStatusEnum.ONGOING}
    )
    result = query.fetchone()
    
    if not result:
        raise HTTPException(status_code=404, detail="Активное интервью не найдено. Начните новое интервью.")
    
    interview_id, question_ids = result
    
    # Получаем ID вопросов, выбранных для этого интервью
    if question_ids:
        selected_question_ids = list(map(float, question_ids.split(',')))
    else:
        # Если question_ids пуста, получаем все вопросы
        query = await session.execute(text("SELECT id FROM pythonn"))
        all_question_ids = query.scalars().all()
        
        # Выбираем 10 случайных вопросов, если их больше 10
        if len(all_question_ids) > QUESTIONS_PER_INTERVIEW:
            selected_question_ids = random.sample(all_question_ids, QUESTIONS_PER_INTERVIEW)
        else:
            selected_question_ids = all_question_ids
        
        # Сохраняем выбранные вопросы
        await session.execute(
            text("UPDATE interviews SET question_ids = :question_ids WHERE id = :id"),
            {"question_ids": ','.join(map(str, selected_question_ids)), "id": interview_id}
        )
    
    # Получаем ID вопросов, на которые уже ответили
    answered_question_ids = await UserAnswerDAO.get_answered_question_ids(session, interview_id)
    
    # Находим вопросы, на которые еще не ответили
    unanswered_question_ids = [qid for qid in selected_question_ids if qid not in answered_question_ids]
    
    if not unanswered_question_ids:
        # Если все вопросы отвечены, завершаем интервью
        interview = await InterviewDAO.find_one_or_none_by_id(interview_id, session)
        if interview:
            interview.status = InterviewStatusEnum.COMPLETED
            await session.flush()
        raise HTTPException(status_code=404, detail="Все вопросы уже отвечены. Интервью завершено.")
    
    # Выбираем случайный вопрос из оставшихся
    random_question_id = random.choice(unanswered_question_ids)
    
    # Получаем вопрос
    question = await QuestionDAO.find_one_or_none_by_id(random_question_id, session)
    
    if not question:
        raise HTTPException(status_code=404, detail="Вопрос не найден")
    
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
        text("SELECT id, question_ids FROM interviews WHERE user_id = :user_id AND status = :status ORDER BY id DESC LIMIT 1"),
        {"user_id": current_user.id, "status": InterviewStatusEnum.ONGOING}
    )
    result = query.fetchone()
    
    if not result:
        raise HTTPException(status_code=404, detail="Активное интервью не найдено. Начните новое интервью.")
    
    interview_id, question_ids = result
    
    # Проверяем, что вопрос существует
    question = await QuestionDAO.find_one_or_none_by_id(answer_data.question_id, session)
    if not question:
        raise HTTPException(status_code=404, detail="Вопрос не найден")
    
    # Проверяем, что вопрос входит в выбранные для этого интервью
    if question_ids:
        selected_question_ids = list(map(float, question_ids.split(',')))
        if answer_data.question_id not in selected_question_ids:
            raise HTTPException(status_code=400, detail="Этот вопрос не входит в текущее интервью")
    
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
        text("SELECT id, question_ids FROM interviews WHERE user_id = :user_id AND status = :status ORDER BY id DESC LIMIT 1"),
        {"user_id": current_user.id, "status": InterviewStatusEnum.ONGOING}
    )
    result = query.fetchone()
    
    if not result:
        raise HTTPException(status_code=404, detail="Активное интервью не найдено. Начните новое интервью.")
    
    interview_id, question_ids = result
    
    # Получаем количество выбранных вопросов
    if question_ids:
        selected_question_ids = question_ids.split(',')
        total_questions = len(selected_question_ids)
    else:
        total_questions = QUESTIONS_PER_INTERVIEW
    
    # Подсчитываем количество отвеченных вопросов
    answered_questions = await UserAnswerDAO.count_answers(session, interview_id)
    
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
