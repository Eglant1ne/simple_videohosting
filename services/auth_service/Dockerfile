FROM python:3.12.10-slim

WORKDIR /auth_service

COPY . .

RUN pip install --no-cache-dir --upgrade -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0" , "--port", "8000", "--workers", "4"]