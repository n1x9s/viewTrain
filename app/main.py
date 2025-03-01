"""

 __         __                     __                  _______              __         __
|__|.-----.|  |_.-----.----.--.--.|__|.-----.--.--.--.|_     _|.----.---.-.|__|.-----.|__|.-----.
|  ||     ||   _|  -__|   _|  |  ||  ||  -__|  |  |  |  |   |  |   _|  _  ||  ||     ||  ||  _  |
|__||__|__||____|_____|__|  \___/ |__||_____|________|  |___|  |__| |___._||__||__|__||__||___  |
                                                                                          |_____|
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse
import asyncio

from app.auth.router import router as router_auth
from fastapi.staticfiles import StaticFiles
from app.auth.init_data import init_data
from app.dao.session_maker import get_async_session

app = FastAPI()

# Добавляем middleware для CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешаем все источники
    allow_credentials=True,
    allow_methods=["*"],  # Разрешаем все методы
    allow_headers=["*"],  # Разрешаем все заголовки
)

app.mount('/static', StaticFiles(directory='app/static'), name='static')


@app.get("/")
async def root():
    return HTMLResponse("Cваггер <a href='/docs'>тут</a>")


@app.on_event("startup")
async def startup_event():
    """Инициализация данных при запуске приложения"""
    async for session in get_async_session():
        await init_data(session)
        break


app.include_router(router_auth)
