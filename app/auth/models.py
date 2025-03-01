from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.dao.database import Base

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
    password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    
    # Связи с другими таблицами
    directions = relationship("Direction", secondary=user_direction, back_populates="users")
    languages = relationship("Language", secondary=user_language, back_populates="users")

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