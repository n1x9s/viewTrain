from pydantic import EmailStr
from jose import jwt
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from app.auth.schemas import EmailModel
from app.config import settings
from app.auth.dao import UsersDAO
from app.dao.session_maker import SessionDep

logger = logging.getLogger(__name__)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=30)
    to_encode.update({"exp": expire})
    encode_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encode_jwt


async def authenticate_user(email: EmailStr, password: str, session: AsyncSession = SessionDep):
    logger.info(f"Attempting to authenticate user with email: {email}")
    user = await UsersDAO.find_one_or_none(session=session, filters=EmailModel(email=email))
    
    if not user:
        logger.warning(f"User not found: {email}")
        return None
    
    logger.info(f"Found user: {user}")
    logger.info(f"User's hashed password: {user.hashed_password}")
    logger.info(f"Input password: {password}")
    
    is_valid = user.verify_password(password)
    logger.info(f"Password verification result: {is_valid}")
    
    if not is_valid:
        logger.warning(f"Invalid password for user: {email}")
        return None
        
    return user
