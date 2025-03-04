from typing import List
import logging
from fastapi import APIRouter, Response, Depends, HTTPException, status
from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.exceptions import UserAlreadyExistsException, IncorrectEmailOrPasswordException
from app.auth.auth import authenticate_user, create_access_token
from app.auth.dao import UsersDAO, DirectionsDAO, LanguagesDAO
from app.auth.schemas import SUserRegister, SUserAuth, EmailModel, SUserAddDB, SUserInfo, SUserUpdate, UserMeResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

from app.dao.session_maker import TransactionSessionDep, SessionDep

router = APIRouter(prefix='/auth', tags=['Auth'])
logger = logging.getLogger(__name__)


class UserUpdateData(BaseModel):
    name: str
    email: str
    direction_ids: List[int]
    language_ids: List[int]


@router.post("/register")
async def register_user(user_data: SUserRegister, session: AsyncSession = SessionDep):
    logger.info(f"Registering new user with email: {user_data.email}")
    
    # Проверяем, существует ли пользователь
    existing_user = await UsersDAO.find_one_or_none(
        session=session,
        filters=EmailModel(email=user_data.email)
    )
    if existing_user:
        logger.warning(f"User with email {user_data.email} already exists")
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    try:
        # Создаем нового пользователя
        new_user = User(
            email=user_data.email,
            name=user_data.name
        )
        logger.info(f"Setting password for new user: {user_data.email}")
        new_user.set_password(user_data.password)
        logger.info("Password has been set")

        # Получаем объекты направлений
        directions = await DirectionsDAO.find_by_ids(session=session, ids=user_data.direction_ids)
        logger.info(f"Found directions: {directions}")

        # Получаем объекты языков
        languages = await LanguagesDAO.find_by_ids(session=session, ids=user_data.language_ids)
        logger.info(f"Found languages: {languages}")

        # Добавляем связи
        new_user.directions.extend(directions)
        new_user.languages.extend(languages)

        # Сохраняем пользователя
        await UsersDAO.add(session, new_user)
        await session.commit()
        
        logger.info(f"User successfully registered: {new_user}")
        return {"message": "User registered successfully"}

    except Exception as e:
        logger.error(f"Error during user registration: {e}", exc_info=True)
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail="Error during registration"
        )


@router.post("/login/")
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
async def logout_user(response: Response):
    response.delete_cookie(key="users_access_token")
    return {'message': 'Logout is successful!'}


@router.get("/me/")
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
