FROM python:3.12.10-slim

# Установка curl для healthcheck и ffmpeg для обработки видео
RUN apt-get update && apt-get install -y \
    curl \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /video_postprocess_service

# Копируем зависимости отдельно для лучшего кэширования
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Копируем остальной код
COPY . .

EXPOSE 8090

CMD ["python3", "main.py"]