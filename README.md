# Booking Service

REST API для записи на встречи. Принимает бронирования через HTTP, ставит задачу в очередь, воркер асинхронно подтверждает запись.

## Быстрый старт

```bash
cp .env.example .env
docker compose up --build -d
```

Миграции применяются автоматически контейнером `migrate` при старте стека. После этого API доступен на `http://localhost:8000`, документация — на `http://localhost:8000/docs`.

Для запуска через Makefile можно использовать:

```bash
make dev
```

## Запуск тестов

Тесты работают без Docker — используется SQLite in-memory вместо Postgres.

```bash
cd backend
pip install -r requirements.txt
pip install aiosqlite
pytest tests/ -v
```

Или одной командой из корня:

```bash
make test
```

## Структура проекта

```
backend/
  app/
    core/
      config.py          # настройки через pydantic-settings
      db/                # движок и сессия SQLAlchemy
      dependencies.py    # DI-зависимости FastAPI
      logging/           # JSON-логирование
      rate_limit.py      # sliding window rate limiting через Redis
    models/              # SQLAlchemy модели
    repositories/        # слой доступа к данным
    routers/             # FastAPI роутеры
    schemas/             # Pydantic схемы запросов/ответов
    services/            # бизнес-логика
    workers/
      celery_app.py      # конфигурация Celery
      tasks.py           # задача подтверждения брони
  migrations/            # Alembic
  tests/
    conftest.py          # фикстуры
    test_bookings_api.py # тесты API
    test_worker.py       # тесты воркера
```

## API

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/bookings` | Создать бронь |
| GET | `/bookings/{id}` | Статус брони |
| GET | `/bookings?status=pending&page=1&size=20` | Список броней |
| DELETE | `/bookings/{id}` | Отменить бронь |
| GET | `/health` | Healthcheck |

## Технические решения

**FastAPI + SQLAlchemy async.** Выбор очевидный для async-first сервиса.

**Архитектура Repository + Service.** Repository изолирует работу с БД, Service содержит бизнес-логику. Роутер только маршрутизирует — никакой логики. Это даёт чистое разделение ответственности и упрощает тестирование: в тестах подменяем только сессию БД, а не перекрываем целые слои.

**Celery + Redis.** Celery запускается как отдельный контейнер с той же кодовой базой. В `tasks.py` используется синхронный движок SQLAlchemy — Celery не async, и прокидывать туда asyncpg было бы усложнением без выгоды. Задача получает `booking_id`, а не объект Booking, чтобы сериализация в JSON была тривиальной.

**Идемпотентность.** Задача в начале проверяет текущий статус брони. Если он не `pending` — просто возвращает `skipped`. Это защищает от двойного выполнения при retry и ручном перезапуске.

**Retry с exponential backoff.** При ошибке внешнего сервиса (15% вероятность) задача уходит в повтор через `autoretry_for` с `retry_backoff=True`. После исчерпания попыток статус становится `failed`. Параметры: 3 попытки, backoff до 60 секунд с jitter.

**Rate limiting.** Sliding window через Redis sorted set на эндпоинте `POST /bookings`. По умолчанию 10 запросов в 60 секунд с одного IP. Настраивается через `.env`.

**Structured logging.** `python-json-logger` форматирует все логи в JSON. Все события воркера (подтверждение, ошибка, retry, idempotent skip) логируются с контекстом через `extra={}`.

**Тесты без Docker.** Вместо тест-контейнера с Postgres используется SQLite in-memory через aiosqlite. Это делает тесты быстрыми и портативными. Celery в тестах мокается — `confirm_booking.delay` подменяется, чтобы не требовать Redis.

**Alembic.** Миграции версионированы. В docker-compose отдельный контейнер `migrate` применяет `alembic upgrade head` до старта API, что гарантирует консистентность схемы.
