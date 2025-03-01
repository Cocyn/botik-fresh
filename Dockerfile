# Базовый образ с Python 3.12
FROM python:3.12-slim

# Установка FFmpeg и зависимостей
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean

# Установка рабочей директории
WORKDIR /app

# Копирование файлов проекта
COPY . .

# Установка Python-зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Команда для запуска бота
CMD ["python", "bot.py"]