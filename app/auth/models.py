from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.dao.database import Base
import bcrypt
import logging

logger = logging.getLogger(__name__)

# Таблица связи между пользователями и направлениями
user_direction = Table(
    'user_direction',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('direction_id', Integer, ForeignKey('directions.id'))
)

# Таблица связи между пользователями и языками
user_language = Table(
    'user_language',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('language_id', Integer, ForeignKey('languages.id'))
)

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    
    # Связи с другими таблицами
    directions = relationship("Direction", secondary=user_direction, back_populates="users")
    languages = relationship("Language", secondary=user_language, back_populates="users")

    def set_password(self, password: str) -> None:
        """Синхронный метод для установки пароля"""
        logger.info("Hashing password")
        self.hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        logger.info(f"Hashed password: {self.hashed_password}")

    def verify_password(self, password: str) -> bool:
        """Синхронный метод для проверки пароля"""
        logger.info("Verifying password")
        logger.info(f"Stored hashed password: {self.hashed_password}")
        logger.info(f"Input password: {password}")
        try:
            result = bcrypt.checkpw(password.encode(), self.hashed_password.encode())
            logger.info(f"Password verification result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error verifying password: {str(e)}")
            return False

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id}, email={self.email})"
    

class Direction(Base):
    __tablename__ = 'directions'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    
    # Связь с пользователями
    users = relationship("User", secondary=user_direction, back_populates="directions")
    

class Language(Base):
    __tablename__ = 'languages'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    
    # Связь с пользователями
    users = relationship("User", secondary=user_language, back_populates="languages")