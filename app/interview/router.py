from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.dao.session_maker import SessionDep, TransactionSessionDep
from app.interview.schemas import (
    InterviewStart,
    QuestionResponse,
    AnswerRequest,
    AnswerResponse,
    InterviewStatus,
    InterviewFinish,
    InterviewCreate,
    UserAnswerCreate,
    QuestionListResponse,
)
from app.interview.dao import QuestionDAO, InterviewDAO, UserAnswerDAO
from app.interview.models import (
    Interview,
    UserAnswer,
    InterviewStatus as InterviewStatusEnum,
)
from app.auth.dependencies import get_current_user
from app.auth.models import User
import logging
from sqlalchemy import text
import random
from typing import Optional, List

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/interview", tags=["interview"])

# Константа для количества вопросов в интервью
QUESTIONS_PER_INTERVIEW = 10


@router.get("/start", response_model=InterviewStart)
async def start_interview(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = TransactionSessionDep,
):
    """Начать новое интервью"""
    # Получаем количество интервью у текущего пользователя
    query = await session.execute(
        text("SELECT COUNT(*) FROM interviews WHERE user_id = :user_id"),
        {"user_id": current_user.id},
    )
    user_interview_count = query.scalar_one() + 1  # Новый ID интервью для пользователя

    # Определяем тип вопросов в зависимости от языка и направления пользователя
    question_type = QuestionDAO.get_question_type_for_user(current_user)

    # Создаем новое интервью
    new_interview = Interview(
        user_id=current_user.id,
        status=InterviewStatusEnum.ONGOING,
        user_interview_id=user_interview_count,  # Добавляем ID интервью для пользователя
        question_type=question_type,  # Сохраняем тип вопросов
    )

    # Добавляем в базу данных
    session.add(new_interview)
    await session.flush()

    # Получаем все вопросы соответствующего типа
    query = await session.execute(
        text(f"SELECT id FROM {question_type}")
    )
    all_question_ids = query.scalars().all()

    # Выбираем 10 случайных вопросов, если их больше 10
    if len(all_question_ids) > QUESTIONS_PER_INTERVIEW:
        selected_question_ids = random.sample(all_question_ids, QUESTIONS_PER_INTERVIEW)
    else:
        selected_question_ids = all_question_ids

    # Сохраняем выбранные вопросы в атрибуте интервью
    await session.execute(
        text("UPDATE interviews SET question_ids = :question_ids WHERE id = :id"),
        {
            "question_ids": ",".join(map(str, selected_question_ids)),
            "id": new_interview.id,
        },
    )

    return InterviewStart(
        interview_id=user_interview_count,  # Возвращаем ID интервью для пользователя
        status="ongoing",
        message="Interview started",
    )


@router.get("/question", response_model=QuestionResponse)
async def get_question(
    current_user: User = Depends(get_current_user), session: AsyncSession = SessionDep
):
    """Получить следующий вопрос для текущего интервью"""
    # Находим активное интервью пользователя
    query = await session.execute(
        text(
            "SELECT id, question_ids, user_interview_id, question_type FROM interviews WHERE user_id = :user_id AND status = :status ORDER BY id DESC LIMIT 1"
        ),
        {"user_id": current_user.id, "status": InterviewStatusEnum.ONGOING},
    )
    result = query.fetchone()

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Активное интервью не найдено. Начните новое интервью.",
        )

    interview_id, question_ids, user_interview_id, question_type = result

    # Получаем ID вопросов, выбранных для этого интервью
    if question_ids:
        # Convert to int by first parsing as float for values like "295.0"
        selected_question_ids = [int(float(id_str)) for id_str in question_ids.split(",")]
    else:
        # Если question_ids пуста, получаем все вопросы соответствующего типа
        query = await session.execute(
            text(f"SELECT id FROM {question_type}")
        )
        all_question_ids = query.scalars().all()

        # Выбираем 10 случайных вопросов, если их больше 10
        if len(all_question_ids) > QUESTIONS_PER_INTERVIEW:
            selected_question_ids = random.sample(
                all_question_ids, QUESTIONS_PER_INTERVIEW
            )
        else:
            selected_question_ids = all_question_ids

        # Сохраняем выбранные вопросы
        await session.execute(
            text("UPDATE interviews SET question_ids = :question_ids WHERE id = :id"),
            {
                "question_ids": ",".join(map(str, selected_question_ids)),
                "id": interview_id,
            },
        )

    # Получаем ID вопросов, на которые уже ответили
    answered_question_ids = await UserAnswerDAO.get_answered_question_ids(
        session, interview_id
    )

    # Находим вопросы, на которые еще не ответили
    unanswered_question_ids = [
        qid for qid in selected_question_ids if qid not in answered_question_ids
    ]

    if not unanswered_question_ids:
        # Если все вопросы отвечены, завершаем интервью
        interview = await InterviewDAO.find_one_or_none_by_id(interview_id, session)
        if interview:
            interview.status = InterviewStatusEnum.COMPLETED
            await session.flush()
        raise HTTPException(
            status_code=404, detail="Все вопросы уже отвечены. Интервью завершено."
        )

    # Выбираем случайный вопрос из оставшихся
    random_question_id = random.choice(unanswered_question_ids)

    # Получаем вопрос соответствующего типа
    question = await QuestionDAO.find_one_or_none_by_id(
        random_question_id, session, question_type=question_type
    )

    if not question:
        raise HTTPException(status_code=404, detail="Вопрос не найден")

    return QuestionResponse(
        question_id=question.id, question_text=question.question, tag=question.tag
    )


@router.post("/answer", response_model=AnswerResponse)
async def submit_answer(
    answer_data: AnswerRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = TransactionSessionDep,
):
    """Отправить ответ на вопрос"""
    # Находим активное интервью пользователя
    query = await session.execute(
        text(
            "SELECT id, question_ids, user_interview_id, question_type FROM interviews WHERE user_id = :user_id AND status = :status ORDER BY id DESC LIMIT 1"
        ),
        {"user_id": current_user.id, "status": InterviewStatusEnum.ONGOING},
    )
    result = query.fetchone()

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Активное интервью не найдено. Начните новое интервью.",
        )

    interview_id, question_ids, user_interview_id, question_type = result

    # Проверяем, что вопрос существует
    question = await QuestionDAO.find_one_or_none_by_id(
        answer_data.question_id, session, question_type=question_type
    )
    if not question:
        raise HTTPException(status_code=404, detail="Вопрос не найден")

    # Проверяем, что вопрос входит в выбранные для этого интервью
    if question_ids:
        selected_question_ids = list(map(int, question_ids.split(",")))
        if answer_data.question_id not in selected_question_ids:
            raise HTTPException(
                status_code=400, detail="Этот вопрос не входит в текущее интервью"
            )

    # Проверяем, не отвечал ли пользователь уже на этот вопрос
    existing_answer = await UserAnswerDAO.find_one_or_none(
        session, 
        interview_id=interview_id, 
        question_id=answer_data.question_id,
        question_type=question_type
    )

    if existing_answer:
        raise HTTPException(status_code=400, detail="Вы уже ответили на этот вопрос")

    # Оцениваем ответ
    score, feedback = await UserAnswerDAO.evaluate_answer(
        session, question, answer_data.user_answer
    )

    # Сохраняем ответ
    user_answer = UserAnswer(
        interview_id=interview_id,
        question_id=answer_data.question_id,
        question_type=question_type,
        user_answer=answer_data.user_answer,
        score=score,
        feedback=feedback,
    )

    session.add(user_answer)
    await session.flush()

    # Проверяем количество отвеченных вопросов
    answered_questions = await UserAnswerDAO.count_answers(session, interview_id)

    # Если ответили на все вопросы, завершаем интервью и возвращаем результат
    if answered_questions >= QUESTIONS_PER_INTERVIEW:
        # Получаем интервью
        interview = await InterviewDAO.find_one_or_none_by_id(interview_id, session)

        # Рассчитываем итоговую оценку
        total_score = await InterviewDAO.calculate_interview_score(
            session, interview_id
        )
        score_percentage = int(total_score * 100)

        # Формируем обратную связь
        if total_score > 0.8:
            final_feedback = "Отличный результат! Вы хорошо знаете материал."
        elif total_score > 0.6:
            final_feedback = (
                "Хороший результат! Подтяните некоторые темы для улучшения."
            )
        elif total_score > 0.4:
            final_feedback = "Средний результат. Рекомендуем повторить основные темы."
        else:
            final_feedback = "Результат ниже среднего. Рекомендуем дополнительное изучение материала."

        # Обновляем интервью
        interview.status = InterviewStatusEnum.COMPLETED
        interview.total_score = total_score
        interview.feedback = final_feedback

        await session.flush()

        # Возвращаем результат последнего ответа и итоговый результат
        return AnswerResponse(
            score=score,
            feedback=feedback,
            interview_completed=True,
            final_score=score_percentage,
            final_feedback=final_feedback,
        )

    return AnswerResponse(score=score, feedback=feedback, interview_completed=False)


@router.get("/status", response_model=InterviewStatus)
async def get_interview_status(
    current_user: User = Depends(get_current_user), session: AsyncSession = SessionDep
):
    """Получить статус текущего интервью"""
    # Находим активное интервью пользователя
    query = await session.execute(
        text(
            "SELECT id, question_ids, user_interview_id FROM interviews WHERE user_id = :user_id AND status = :status ORDER BY id DESC LIMIT 1"
        ),
        {"user_id": current_user.id, "status": InterviewStatusEnum.ONGOING},
    )
    result = query.fetchone()

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Активное интервью не найдено. Начните новое интервью.",
        )

    interview_id, question_ids, user_interview_id = result

    # Получаем количество выбранных вопросов
    if question_ids:
        selected_question_ids = question_ids.split(",")
        total_questions = len(selected_question_ids)
    else:
        total_questions = QUESTIONS_PER_INTERVIEW

    # Подсчитываем количество отвеченных вопросов
    answered_questions = await UserAnswerDAO.count_answers(session, interview_id)

    # Вычисляем прогресс
    progress = (
        f"{int(answered_questions / total_questions * 100)}%"
        if total_questions > 0
        else "0%"
    )

    return InterviewStatus(
        interview_id=user_interview_id,  # Используем ID интервью для пользователя
        answered_questions=answered_questions,
        total_questions=total_questions,
        progress=progress,
    )


@router.get("/finish", response_model=InterviewFinish)
async def finish_interview(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = TransactionSessionDep,
):
    """Завершить текущее интервью"""
    # Находим активное интервью пользователя
    query = await session.execute(
        text(
            "SELECT id, user_interview_id FROM interviews WHERE user_id = :user_id AND status = :status ORDER BY id DESC LIMIT 1"
        ),
        {"user_id": current_user.id, "status": InterviewStatusEnum.ONGOING},
    )
    result = query.fetchone()

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Активное интервью не найдено. Начните новое интервью.",
        )

    interview_id, user_interview_id = result

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
        feedback = (
            "Результат ниже среднего. Рекомендуем дополнительное изучение материала."
        )

    # Обновляем интервью
    interview.status = InterviewStatusEnum.COMPLETED
    interview.total_score = score
    interview.feedback = feedback

    await session.flush()

    return InterviewFinish(
        interview_id=user_interview_id,  # Используем ID интервью для пользователя
        score=score_percentage,
        feedback=feedback,
    )


@router.get("/questions", response_model=QuestionListResponse)
async def get_all_questions(
    page: int = Query(1, ge=1, description="Номер страницы"),
    limit: int = Query(50, ge=1, le=100, description="Количество вопросов на странице"),
    tag: Optional[str] = Query(None, description="Фильтр по тегу вопроса"),
    question_type: Optional[str] = Query(None, description="Тип вопросов (pythonn или golangquestions)"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = SessionDep,
):
    """
    Получить список всех вопросов с пагинацией и возможностью фильтрации по тегу.

    - **page**: Номер страницы (начиная с 1)
    - **limit**: Максимальное количество вопросов на странице
    - **tag**: Опциональный фильтр по тегу вопроса
    - **question_type**: Опциональный тип вопросов (если не указан, определяется по языку и направлению пользователя)
    """
    # Вычисляем значение skip на основе номера страницы
    skip = (page - 1) * limit
    
    # Если тип вопросов не указан, определяем его на основе языка и направления пользователя
    if not question_type:
        question_type = QuestionDAO.get_question_type_for_user(current_user)

    questions, total = await QuestionDAO.get_all_questions(
        session=session, skip=skip, limit=limit, tag=tag, question_type=question_type
    )

    # Вычисляем общее количество страниц
    pages = (total + limit - 1) // limit

    return QuestionListResponse(
        items=questions, total=total, page=page, pages=pages, limit=limit
    )
