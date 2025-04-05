from typing import List
import logging
from fastapi import APIRouter, Response, Depends, HTTPException, status
from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.exceptions import UserAlreadyExistsException, IncorrectEmailOrPasswordException
from app.auth.auth import authenticate_user, create_access_token
from app.auth.dao import UsersDAO, DirectionsDAO, LanguagesDAO
from app.auth.schemas import (
    SUserRegisterSimple, SUserAuth, EmailModel, SUserAddDB, 
    SUserInfo, SUserUpdate, UserMeResponse, DirectionSelectionRequest,
    LanguageSelectionRequest, DirectionSelectionResponse, LanguageSelectionResponse,
    EmailCheckRequest, EmailCheckResponse
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from fastapi_versioning import version

from app.dao.session_maker import TransactionSessionDep, SessionDep

router = APIRouter(prefix='/auth', tags=['Auth'])
logger = logging.getLogger(__name__)


class UserUpdateData(BaseModel):
    name: str
    email: str
    direction_ids: List[int]
    language_ids: List[int]


@router.post("/register")
async def register_user(user_data: SUserRegisterSimple, response: Response, session: AsyncSession = SessionDep):
    logger.info(f"Registering new user with data: {user_data.model_dump()}")
    
    try:
        # Проверяем, существует ли пользователь
        existing_user = await UsersDAO.find_one_or_none(
            session=session,
            filters=EmailModel(email=user_data.email)
        )
        if existing_user:
            logger.info(f"User with email {user_data.email} already exists, attempting authentication")
            # Проверяем пароль
            if not existing_user.verify_password(user_data.password):
                logger.warning(f"Invalid password for existing user: {user_data.email}")
                raise IncorrectEmailOrPasswordException
            
            # Создаем токен и устанавливаем cookie
            access_token = create_access_token({"sub": str(existing_user.id)})
            response.set_cookie(key="users_access_token", value=access_token, httponly=True)
            logger.info(f"Successfully authenticated existing user: {user_data.email}")
            return {'ok': True, 'access_token': access_token, 'message': 'User already exists, successfully logged in!'}

        # Создаем нового пользователя
        new_user = User(
            email=user_data.email,
            name=user_data.name,
            phone=user_data.phone
        )
        logger.info(f"Setting password for new user: {user_data.email}")
        new_user.set_password(user_data.password)
        logger.info("Password has been set")

        # Сохраняем пользователя
        await UsersDAO.add(session, new_user)
        await session.commit()
        
        # Создаем токен и устанавливаем cookie для нового пользователя
        access_token = create_access_token({"sub": str(new_user.id)})
        response.set_cookie(key="users_access_token", value=access_token, httponly=True)
        
        logger.info(f"User successfully registered: {new_user}")
        return {'ok': True, 'access_token': access_token, 'message': 'User registered successfully'}

    except Exception as e:
        logger.error(f"Error during user registration: {e}", exc_info=True)
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.post("/login/")
@version(1)
async def auth_user(response: Response, user_data: SUserAuth, session: AsyncSession = SessionDep):
    logger.info(f"Login attempt for user: {user_data.email}")
    check = await authenticate_user(session=session, email=user_data.email, password=user_data.password)
    logger.info(f"Authentication result: {check}")
    if check is None:
        logger.warning(f"Authentication failed for user: {user_data.email}")
        raise IncorrectEmailOrPasswordException
    access_token = create_access_token({"sub": str(check.id)})
    response.set_cookie(key="users_access_token", value=access_token, httponly=True)
    logger.info(f"Successfully authenticated user: {user_data.email}")
    return {'ok': True, 'access_token': access_token, 'message': 'Authorization is successful!'}


@router.post("/logout/")
@version(1)
async def logout_user(response: Response):
    response.delete_cookie(key="users_access_token")
    return {'message': 'Logout is successful!'}


@router.get("/me/")
@version(1)
async def get_me(
    session: AsyncSession = SessionDep,
    current_user: User = Depends(get_current_user)
) -> UserMeResponse:
    # Загружаем пользователя со всеми связями
    stmt = select(User).where(User.id == current_user.id).options(
        selectinload(User.directions),
        selectinload(User.languages)
    )
    result = await session.execute(stmt)
    user = result.scalar_one()
    
    return UserMeResponse(
        name=user.name,
        email=user.email,
        direction_ids=[d.id for d in user.directions],
        language_ids=[l.id for l in user.languages]
    )


@router.put("/me/", response_model=SUserInfo)
@version(1)
async def update_me(
    user_data: UserUpdateData,
    session: AsyncSession = TransactionSessionDep,
    current_user: User = Depends(get_current_user)
) -> SUserInfo:
    """
    Полное обновление данных пользователя.
    Все поля обязательны для заполнения.
    """
    try:
        # Загружаем пользователя со всеми связями
        stmt = select(User).where(User.id == current_user.id).options(
            selectinload(User.directions),
            selectinload(User.languages)
        )
        result = await session.execute(stmt)
        user = result.scalar_one()
        
        # Проверяем, не занят ли email другим пользователем
        if user_data.email != user.email:
            existing_user = await UsersDAO.find_one_or_none(
                session=session, 
                filters=EmailModel(email=user_data.email)
            )
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email is already taken"
                )
        
        # Загружаем новые направления и языки
        directions = await DirectionsDAO.find_by_ids(session=session, ids=user_data.direction_ids)
        if len(directions) != len(user_data.direction_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more selected directions do not exist"
            )
        
        languages = await LanguagesDAO.find_by_ids(session=session, ids=user_data.language_ids)
        if len(languages) != len(user_data.language_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more selected languages do not exist"
            )
        
        # Обновляем основные данные и связи
        user.name = user_data.name
        user.email = user_data.email
        user.directions = directions
        user.languages = languages
        
        await session.commit()
        return SUserInfo.model_validate(user)
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating user data"
        ) from e


@router.delete("/me/", status_code=status.HTTP_204_NO_CONTENT)
@version(1)
async def delete_account(
    session: AsyncSession = TransactionSessionDep,
    current_user: User = Depends(get_current_user)
):
    """Удаление аккаунта текущего пользователя"""
    try:
        # Загружаем пользователя со всеми связями
        stmt = select(User).where(User.id == current_user.id).options(
            selectinload(User.directions),
            selectinload(User.languages)
        )
        result = await session.execute(stmt)
        user = result.scalar_one()
        
        # Сначала удаляем все ответы пользователя
        # Находим все интервью пользователя
        from app.interview.models import Interview, UserAnswer
        
        # Получаем ID всех интервью пользователя
        interview_query = await session.execute(
            select(Interview.id).filter(Interview.user_id == user.id)
        )
        interview_ids = interview_query.scalars().all()
        
        if interview_ids:
            # Удаляем все ответы для этих интервью
            await session.execute(
                delete(UserAnswer).where(UserAnswer.interview_id.in_(interview_ids))
            )
            
            # Удаляем все интервью пользователя
            await session.execute(
                delete(Interview).where(Interview.user_id == user.id)
            )
        
        # Очищаем связи
        user.directions.clear()
        user.languages.clear()
        
        # Удаляем пользователя
        await UsersDAO.delete(session=session, obj=user)
        await session.commit()
        
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        logger.error(f"Error during account deletion: {e}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error during account deletion"
        )


@router.post("/directions/", response_model=DirectionSelectionResponse)
@version(1)
async def select_directions(
    direction_data: DirectionSelectionRequest,
    session: AsyncSession = TransactionSessionDep,
    current_user: User = Depends(get_current_user)
) -> DirectionSelectionResponse:
    """
    Выбор направлений для текущего пользователя.
    """
    try:
        # Загружаем пользователя со всеми связями
        stmt = select(User).where(User.id == current_user.id).options(
            selectinload(User.directions),
            selectinload(User.languages)
        )
        result = await session.execute(stmt)
        user = result.scalar_one()
        
        # Загружаем выбранные направления
        directions = await DirectionsDAO.find_by_ids(session=session, ids=direction_data.direction_ids)
        if len(directions) != len(direction_data.direction_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Одно или несколько выбранных направлений не существуют"
            )
        
        # Обновляем направления пользователя
        user.directions = directions
        await session.commit()
        
        return DirectionSelectionResponse(
            message="Направления успешно обновлены",
            selected_directions=directions
        )
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при обновлении направлений"
        ) from e


@router.post("/languages/", response_model=LanguageSelectionResponse)
@version(1)
async def select_languages(
    language_data: LanguageSelectionRequest,
    session: AsyncSession = TransactionSessionDep,
    current_user: User = Depends(get_current_user)
) -> LanguageSelectionResponse:
    """
    Выбор языков программирования для текущего пользователя.
    """
    try:
        # Загружаем пользователя со всеми связями
        stmt = select(User).where(User.id == current_user.id).options(
            selectinload(User.directions),
            selectinload(User.languages)
        )
        result = await session.execute(stmt)
        user = result.scalar_one()
        
        # Загружаем выбранные языки
        languages = await LanguagesDAO.find_by_ids(session=session, ids=language_data.language_ids)
        if len(languages) != len(language_data.language_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Один или несколько выбранных языков не существуют"
            )
        
        # Обновляем языки пользователя
        user.languages = languages
        await session.commit()
        
        return LanguageSelectionResponse(
            message="Языки программирования успешно обновлены",
            selected_languages=languages
        )
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при обновлении языков программирования"
        ) from e


@router.post("/check-email/", response_model=EmailCheckResponse)
@version(1)
async def check_email(email_data: EmailCheckRequest, session: AsyncSession = SessionDep):
    """
    Проверяет существование пользователя с указанным email.
    Возвращает информацию о следующем шаге: логин или регистрация.
    """
    logger.info(f"Проверка существования email: {email_data.email}")
    
    existing_user = await UsersDAO.find_one_or_none(
        session=session,
        filters=EmailModel(email=email_data.email)
    )
    
    if existing_user:
        logger.info(f"Email {email_data.email} уже зарегистрирован")
        return EmailCheckResponse(
            exists=True,
            next_action="login",
            message="Пользователь с таким email уже существует. Перейдите к входу."
        )
    else:
        logger.info(f"Email {email_data.email} не найден, требуется регистрация")
        return EmailCheckResponse(
            exists=False,
            next_action="register",
            message="Пользователь с таким email не найден. Пожалуйста, зарегистрируйтесь."
        )
