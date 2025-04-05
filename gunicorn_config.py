import multiprocessing
import logging

# Количество воркеров
workers = 2

# Используем правильный worker class для FastAPI
worker_class = "uvicorn.workers.UvicornWorker"

# Слушаем на всех интерфейсах
bind = "0.0.0.0:8000"

# Таймауты
timeout = 120
keepalive = 5

# Логирование
loglevel = "debug"
accesslog = "-"
errorlog = "-"
capture_output = True
enable_stdio_inheritance = True
