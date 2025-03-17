from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # База данных
    database_url: str = Field(
        ...,
        alias="DATABASE_URL",
        description="URL подключения к базе данных PostgreSQL"
    )
    
    # Безопасность
    secret_key: str = Field(
        ...,
        alias="SECRET_KEY",
        description="Секретный ключ для JWT токенов"
    )
    algorithm: str = Field(
        "HS256",
        alias="ALGORITHM",
        description="Алгоритм для JWT токенов"
    )
    access_token_expire_minutes: int = Field(
        30,
        alias="ACCESS_TOKEN_EXPIRE_MINUTES",
        description="Время жизни токена доступа в минутах"
    )
    
    # Настройки приложения
    questions_per_interview: int = Field(
        10,
        alias="QUESTIONS_PER_INTERVIEW",
        description="Количество вопросов в одном интервью"
    )
    min_score_to_pass: float = Field(
        0.6,
        alias="MIN_SCORE_TO_PASS",
        description="Минимальный балл для прохождения интервью"
    )
    
    # Логирование
    log_level: str = Field(
        "INFO",
        alias="LOG_LEVEL",
        description="Уровень логирования"
    )
    log_file: str = Field(
        "app.log",
        alias="LOG_FILE",
        description="Путь к файлу логов"
    )
    
    # GigaChat API
    gigachat_client_id: str = Field(
        ...,
        alias="GIGACHAT_CLIENT_ID",
        description="Client ID для GigaChat API"
    )
    gigachat_client_secret: str = Field(
        ...,
        alias="GIGACHAT_CLIENT_SECRET",
        description="Client Secret для GigaChat API"
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Создаем глобальный экземпляр настроек
settings = Settings() 