FROM python:3.12.10-slim

#для healthcheck
RUN apt-get update  \
    && apt-get install -y curl \
    && rm -rf /var/lib/apt/lists/*


WORKDIR /auth_service

COPY . .

RUN pip install --no-cache-dir --upgrade -r requirements.txt

EXPOSE 8000

CMD ["python3", "main.py"]