from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.dao.database import Base

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    direction_id = Column(Integer, ForeignKey('directions.id'), nullable=False)
    language_id = Column(Integer, ForeignKey('languages.id'), nullable=False)

    direction = relationship("Direction", back_populates="users")
    language = relationship("Language", back_populates="users")

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id}, email={self.email})"
    

class Direction(Base):
    __tablename__ = 'directions'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    users = relationship("User", back_populates="direction")



class Language(Base):
    __tablename__ = 'languages'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    users = relationship("User", back_populates="language")

