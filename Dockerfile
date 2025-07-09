FROM python:3.11-slim

# Установка uv
RUN pip install uv

# Рабочая директория
WORKDIR /app

# Копирование файлов зависимостей
COPY pyproject.toml ./

# Установка зависимостей
RUN uv sync

# Копирование исходного кода
COPY src/ ./src/
COPY data/ ./data/

# Создание папки для логов
RUN mkdir -p logs

# Запуск приложения
CMD ["uv", "run", "python", "src/main.py"] 