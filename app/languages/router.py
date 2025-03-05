from typing import List
from fastapi import APIRouter, Response, Depends, HTTPException, status
from app.auth.dependencies import get_current_user
from app.auth.models import User, Language
from app.auth.dao import LanguagesDAO
from app.auth.schemas import LanguageSchema, LanguageCreate
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.dao.session_maker import TransactionSessionDep, SessionDep

router = APIRouter(prefix='/languages', tags=['Languages'])


class IdModel(BaseModel):
    id: int


@router.get("/", response_model=List[LanguageSchema])
async def get_languages(session: AsyncSession = SessionDep):
    languages = await LanguagesDAO.find_all(session=session, filters=None)
    return languages


@router.post("/", response_model=LanguageSchema)
async def create_language(
    language_data: LanguageCreate,
    session: AsyncSession = TransactionSessionDep
) -> Language:
    """Создание нового языка программирования"""
    # Проверяем, существует ли язык с таким именем
    existing = await LanguagesDAO.find_one_or_none(
        session=session,
        filters=LanguageCreate(name=language_data.name)
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Language with this name already exists"
        )

    # Создаем новый язык
    new_language = Language(name=language_data.name)
    await LanguagesDAO.add(session=session, obj=new_language)
    await session.commit()
    
    return new_language


@router.delete("/{language_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_language(
    language_id: int,
    session: AsyncSession = TransactionSessionDep,
    current_user: User = Depends(get_current_user)
):
    # Проверяем, существует ли язык
    language = await LanguagesDAO.find_one_or_none_by_id(data_id=language_id, session=session)
    if not language:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Language with ID {language_id} not found"
        )
    
    # Удаляем язык
    await LanguagesDAO.delete(session=session, obj=language)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT) 