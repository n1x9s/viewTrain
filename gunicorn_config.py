import multiprocessing

# Количество воркеров
workers = multiprocessing.cpu_count() * 2 + 1

# Путь к приложению
bind = "0.0.0.0:8000"

# Таймауты
timeout = 120
keepalive = 5

# Логирование
accesslog = "logs/access.log"
errorlog = "logs/error.log"
loglevel = "info"

# Перезапуск при ошибках
max_requests = 1000
max_requests_jitter = 50 