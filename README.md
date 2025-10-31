
# simple_videohosting

**simple_videohosting** — это минималистичный сервис для загрузки и хранения видеофайлов, разработанный в рамках хакатона.



## Стек технологий

- Go 
- Python
- MinIO
- RabbitMQ
- Docker

---

## Как запустить проект

Для запуска проекта используется `docker-compose`.

### Шаги:

1. Клонируйте репозиторий:

```bash
git clone https://github.com/Eglant1ne/simple_videohosting.git
cd simple_videohosting
```

2. Создайте файл `.env` на основе `.env.example`:

```bash
cp .env.example .env
```

3. Соберите и запустите проект через Docker Compose:

```bash
docker-compose up --build
```

---


### Разработчик:
- **Eglant1ne**

