<div align="center">

# BookingEngine

**Комплексная SaaS-платформа для онлайн-записи и управления встречами —
ваш собственный Calendly под полным контролем.**

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.x-092E20?style=for-the-badge&logo=django&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-5.3-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-5-37814A?style=for-the-badge&logo=celery&logoColor=white)
![Stripe](https://img.shields.io/badge/Stripe-Payments-635BFF?style=for-the-badge&logo=stripe&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Nginx](https://img.shields.io/badge/Nginx-Reverse_Proxy-009639?style=for-the-badge&logo=nginx&logoColor=white)
![License](https://img.shields.io/badge/License-Proprietary-FF6B35?style=for-the-badge)

</div>

---

## Содержание

1. [О проекте](#1-о-проекте)
2. [Ключевые возможности](#2-ключевые-возможности)
3. [Технологический стек](#3-технологический-стек)
4. [Структура репозитория](#4-структура-репозитория)
5. [Архитектура и как это работает](#5-архитектура-и-как-это-работает)
6. [Доменная модель (крупными блоками)](#6-доменная-модель-крупными-блоками)
7. [Сервисы в Docker Compose](#7-сервисы-в-docker-compose)
8. [Быстрый старт (локально, Docker)](#8-быстрый-старт-локально-docker)
9. [Основные команды](#9-основные-команды)
10. [Ручной запуск frontend и backend](#10-ручной-запуск-frontend-и-backend)
11. [Конфигурация и переменные окружения](#11-конфигурация-и-переменные-окружения)
12. [API, очереди и интеграции](#12-api-очереди-и-интеграции)
13. [Мониторинг и эксплуатация](#13-мониторинг-и-эксплуатация)
14. [CI/CD](#14-cicd)
15. [Безопасность и приватность данных](#15-безопасность-и-приватность-данных)
16. [Роли компонентов в продакшене](#16-роли-компонентов-в-продакшене)
17. [Лицензия](#17-лицензия)
18. [Поддержка](#18-поддержка)

---

## 1. О проекте

**BookingEngine** — это **продуктовая SaaS-платформа для онлайн-записи**: публичные страницы бронирования, гибкие правила доступности, часовые пояса, буферы, напоминания, оплата Stripe, двусторонняя синхронизация с Google/Outlook Calendar и командное планирование (round-robin, collective). Система рассчитана на конечных пользователей (веб-интерфейс), команды (organizations + teams) и интеграторов (REST API), с возможностью эксплуатации в Docker — от локальной разработки до production.

### Что это за тип системы

По архитектуре BookingEngine — **многосервисная распределённая платформа** (не монолит «в одном процессе»):

| Аспект            | Описание                                                                                       |
|-------------------|------------------------------------------------------------------------------------------------|
| **Продукт**       | B2C/B2B-сервис планирования встреч с биллингом, командами и интеграциями календарей            |
| **Архитектура**   | Многосервисная: Django REST API, React SPA, Celery workers, Celery Beat, Nginx reverse proxy   |
| **Хранилище**     | PostgreSQL (метаданные и события) + Redis (кэш, брокер очередей, locks)                        |
| **Очереди**       | Celery + Redis — напоминания, синхронизация календарей, отправка писем, обработка webhooks     |
| **Интеграции**    | Stripe (платежи), Google Calendar API, Microsoft Graph (Outlook), SMTP/SendGrid (email)        |
| **Frontend**      | React 18 + TypeScript + Vite + Tailwind, Redux Toolkit, react-hook-form                        |
| **Эксплуатация**  | Docker Compose из коробки; production-ready Gunicorn + Nginx + healthchecks                    |

Подходит как **бэкбоун для агентств, клиник, репетиторов, консультантов, барбершопов и SaaS-команд**, которым нужна белая, кастомизируемая альтернатива Calendly / SavvyCal / Cal.com — на собственной инфраструктуре.

---

## 2. Ключевые возможности

### Для конечного пользователя
- **Публичные страницы бронирования** — уникальный slug (`/p/your-name`), кастомные цвета, лого, описание
- **Выбор слота в один клик** — отображение свободного времени в часовом поясе посетителя
- **Кастомные вопросы** — собирайте при бронировании всё, что нужно (телефон, тему, файлы)
- **Подтверждение и отмена** — токенизированные ссылки для invitee без логина
- **Перенос встречи** — invitee может перенести в один клик до начала
- **Оплата при бронировании** — Stripe Checkout / Payment Intents с возвратом и частичной оплатой

### Для владельца календаря
- **Несколько календарей** — рабочий, личный, командный — с отдельными правилами
- **Правила доступности** — недельные расписания, date overrides, blocked time, праздники
- **Буферы и минимальное уведомление** — pre/post-event buffers, минимум за N часов
- **Event types** — длительности (15/30/60 мин), локация (in-person, phone, Zoom, Meet)
- **Часовые пояса** — полный IANA, автоматическая конвертация для invitee
- **Двусторонняя синхронизация** — Google Calendar и Outlook (push + pull, conflict detection)
- **Напоминания** — email/SMS на T-24h, T-1h, T-15min с шаблонами

### Для команд и организаций
- **Workspaces (Organizations)** — единый биллинг, общие шаблоны, единый домен
- **Round-Robin** — равномерное распределение записей между членами команды
- **Collective events** — встречи, требующие нескольких участников одновременно
- **Роли и права** — owner / admin / member, audit log
- **Командная аналитика** — booking rate, no-show rate, доход (Recharts dashboards)

### Для разработчиков и интеграторов
- **REST API** на DRF + JWT, документация через `drf-spectacular` (OpenAPI 3)
- **Webhooks** для бронирований (`booking.created`, `booking.canceled`, `booking.rescheduled`)
- **Embeddable widget** — встраиваемый iframe для сторонних сайтов
- **Rate limiting** через Nginx + DRF throttling

---

## 3. Технологический стек

### Backend
| Компонент             | Технология                                                              |
|-----------------------|-------------------------------------------------------------------------|
| Язык                  | Python 3.12+                                                            |
| Web-фреймворк         | Django 5.1 + Django REST Framework 3.15                                 |
| Аутентификация        | SimpleJWT (access + refresh, blacklist)                                 |
| База данных           | PostgreSQL 16 (через `psycopg2-binary`)                                 |
| Кэш / брокер          | Redis 7 (`django-redis`, `redis-py`)                                    |
| Очереди               | Celery 5.4 + Celery Beat (`django-celery-beat`, `django-celery-results`)|
| Платежи               | Stripe SDK 11.x (Checkout, PaymentIntents, Webhooks)                    |
| Календари             | `google-api-python-client`, `msal` (Microsoft Graph)                    |
| Часовые пояса         | `pytz`, `python-dateutil`                                               |
| API-документация      | `drf-spectacular` (OpenAPI 3, Swagger UI, ReDoc)                        |
| WSGI-сервер           | Gunicorn (4 worker'а, timeout 120s)                                     |
| Статика               | WhiteNoise + Nginx                                                      |
| Тесты                 | pytest, pytest-django, factory-boy, faker, coverage                     |

### Frontend
| Компонент       | Технология                                       |
|-----------------|--------------------------------------------------|
| Framework       | React 18                                         |
| Язык            | TypeScript 5.3                                   |
| Сборщик         | Vite 5                                           |
| Стили           | Tailwind CSS 3 + Headless UI + Heroicons         |
| State           | Redux Toolkit 2 + React-Redux 9                  |
| Формы           | react-hook-form 7                                |
| HTTP            | Axios 1                                          |
| Платежи         | `@stripe/react-stripe-js`, `@stripe/stripe-js`   |
| Даты            | `date-fns` + `date-fns-tz`                       |
| Уведомления     | `react-hot-toast`                                |
| Графики         | Recharts                                         |
| Роутинг         | React Router 6                                   |

### Инфраструктура
| Компонент            | Технология                          |
|----------------------|-------------------------------------|
| Контейнеризация      | Docker + Docker Compose v2          |
| Reverse Proxy        | Nginx (TLS termination, static, gzip)|
| Process Manager      | Gunicorn (sync workers)             |
| Cron-планировщик     | Celery Beat (DatabaseScheduler)     |
| Email               | SMTP (SendGrid / AWS SES совместимы) |

---

## 4. Структура репозитория

```
BookingEngine/
├── backend/                          # Django REST API + Celery
│   ├── apps/
│   │   ├── accounts/                 # Пользователи, организации, команды, JWT
│   │   ├── calendars/                # Календари + правила доступности (services.py)
│   │   ├── event_types/              # Типы встреч (длительности, локации)
│   │   ├── booking_pages/            # Публичные страницы /p/<slug>
│   │   ├── bookings/                 # Брони + signals + tasks (напоминания)
│   │   ├── integrations/             # Google / Outlook calendar sync
│   │   ├── notifications/            # Email/SMS шаблоны + Celery tasks
│   │   └── payments/                 # Stripe (PaymentIntents, webhooks)
│   ├── config/
│   │   ├── settings/
│   │   │   ├── base.py               # Общие настройки
│   │   │   ├── development.py        # DEBUG=True, locmem cache
│   │   │   └── production.py         # SECURE_*, Sentry, S3
│   │   ├── celery.py                 # Celery app (autodiscover_tasks)
│   │   ├── urls.py                   # Root URLs + DRF + drf-spectacular
│   │   └── wsgi.py
│   ├── utils/                        # exceptions, pagination, timezone_utils
│   ├── manage.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/                         # React 18 + TypeScript + Vite
│   ├── src/
│   │   ├── api/                      # axios-инстанс, сервисы по доменам
│   │   ├── components/               # переиспользуемые UI-компоненты
│   │   ├── hooks/                    # useAuth, useBookings, useTimezone
│   │   ├── pages/                    # Login, Dashboard, BookingPage, Settings
│   │   ├── store/                    # Redux Toolkit slices
│   │   ├── styles/                   # Tailwind globals
│   │   └── utils/                    # форматтеры, тайм-зоны, валидация
│   ├── public/
│   ├── package.json
│   ├── tsconfig.json
│   └── Dockerfile
│
├── nginx/
│   └── nginx.conf                    # reverse proxy, gzip, статика, /api -> backend
│
├── docker-compose.yml                # 6 сервисов: db, redis, backend, worker, beat, frontend, nginx
├── .env.example                      # шаблон переменных окружения
└── README.md
```

---

## 5. Архитектура и как это работает

```
                              ┌──────────────────────┐
                              │      Пользователь    │
                              │  (Browser / Invitee) │
                              └──────────┬───────────┘
                                         │  HTTPS (443)
                              ┌──────────▼───────────┐
                              │   Nginx (Reverse     │
                              │      Proxy + TLS)    │
                              └─────┬──────────┬─────┘
                                    │          │
                       /  /static   │          │  /api/*
                                    │          │
                         ┌──────────▼───┐  ┌───▼────────────┐
                         │  React SPA   │  │  Django REST   │
                         │  (Vite build)│  │  (Gunicorn x4) │
                         └──────────────┘  └───┬────────┬───┘
                                               │        │
                                ┌──────────────┘        └────────────────┐
                                │                                        │
                       ┌────────▼─────────┐                  ┌──────────▼─────────┐
                       │   PostgreSQL 16  │                  │      Redis 7       │
                       │  (метаданные,    │                  │  (cache, broker,   │
                       │   брони, юзеры)  │                  │   locks, sessions) │
                       └──────────────────┘                  └───────┬────────────┘
                                                                     │
                                            ┌────────────────────────┴───────────────┐
                                            │                                        │
                                  ┌─────────▼──────────┐                  ┌──────────▼─────────┐
                                  │  Celery Worker(s)  │                  │    Celery Beat     │
                                  │  (concurrency=4)   │                  │ (DB scheduler)     │
                                  └─────────┬──────────┘                  └────────────────────┘
                                            │
                          ┌─────────────────┼──────────────────────────────┐
                          │                 │                              │
                   ┌──────▼──────┐   ┌──────▼──────┐               ┌───────▼───────┐
                   │   Stripe    │   │   Google /  │               │  SMTP / SES   │
                   │   API       │   │  Outlook    │               │  (email)      │
                   └─────────────┘   └─────────────┘               └───────────────┘
```

### Жизненный цикл бронирования

1. **Invitee** открывает `/p/<slug>` → React SPA загружает страницу
2. SPA запрашивает `GET /api/p/<slug>/available-slots/?date=YYYY-MM-DD&tz=Europe/Tashkent`
3. Django считает свободные слоты: `availability rules` − `existing bookings` − `buffers` − `external calendar busy`
4. Invitee выбирает слот → `POST /api/p/<slug>/book/` с данными
5. Django создаёт `Booking` в статусе `PENDING_PAYMENT` (если платный) или `CONFIRMED`
6. Срабатывает `signals.py` → ставятся Celery-таски:
   - `send_confirmation_email.delay()`
   - `sync_to_google_calendar.delay()`
   - `schedule_reminders.apply_async(eta=...)`
7. Celery Beat периодически проверяет напоминания и календарные изменения
8. По Stripe webhook → `payments.views.webhook` → переводит бронь в `CONFIRMED`

---

## 6. Доменная модель (крупными блоками)

| Блок                   | Что в нём живёт                                                                                            |
|------------------------|------------------------------------------------------------------------------------------------------------|
| **Accounts**           | `User`, `Organization`, `Membership` (роль: owner/admin/member), JWT-токены, OAuth-токены интеграций       |
| **Calendars**          | `Calendar`, `AvailabilityRule` (день недели + интервалы), `DateOverride`, `BlockedTime`                    |
| **Event Types**        | `EventType` (длительность, локация, цена, буферы, кастомные вопросы)                                       |
| **Booking Pages**      | `BookingPage` (slug, бренд, цвет, описание, привязка к Calendar или Team)                                  |
| **Bookings**           | `Booking` (status: pending/confirmed/canceled/completed/no_show), `BookingAnswer`, `RescheduleHistory`     |
| **Integrations**       | `CalendarIntegration` (provider, токены, sync-state), `ExternalEvent` (импортированные busy-слоты)         |
| **Notifications**      | `NotificationTemplate`, `ScheduledNotification`, `NotificationLog`                                         |
| **Payments**           | `Payment`, `Refund`, `StripeWebhookEvent` (идемпотентность)                                                |

Все доменные сущности связаны через `Organization` для multi-tenancy. Доступ строго ограничен через DRF-permissions и фильтрацию по `request.user.organization`.

---

## 7. Сервисы в Docker Compose

`docker-compose.yml` поднимает **7 сервисов**:

| Сервис           | Образ / Build              | Порт           | Назначение                                                  |
|------------------|----------------------------|----------------|-------------------------------------------------------------|
| `db`             | `postgres:16-alpine`       | `5432`         | Основная БД, healthcheck через `pg_isready`                 |
| `redis`          | `redis:7-alpine`           | `6379`         | Кэш, брокер очередей, healthcheck через `redis-cli ping`    |
| `backend`        | `./backend/Dockerfile`     | `8000`         | Django + Gunicorn (4 worker'а, timeout 120s)                |
| `celery_worker`  | `./backend/Dockerfile`     | —              | Celery worker (concurrency=4) — бизнес-задачи               |
| `celery_beat`    | `./backend/Dockerfile`     | —              | Celery Beat (DatabaseScheduler) — периодические задачи      |
| `frontend`       | `./frontend/Dockerfile`    | `3000`         | Vite dev / built React SPA                                  |
| `nginx`          | `nginx:alpine`             | `80`, `443`    | Reverse proxy, статика, TLS termination                     |

Volumes:
- `postgres_data` — данные Postgres
- `redis_data` — RDB снепшоты Redis
- `static_volume` — Django staticfiles (для Nginx)
- `media_volume` — пользовательские загрузки

---

## 8. Быстрый старт (локально, Docker)

### Требования
- Docker 24+ и Docker Compose v2
- Git
- 4 ГБ свободной RAM, 5 ГБ диска

### 1. Клонирование и конфигурация
```bash
git clone https://github.com/NodirOdilov/BookingEngine.git
cd BookingEngine
cp .env.example .env
# Откройте .env и заполните минимум: SECRET_KEY, STRIPE_*, EMAIL_*
```

### 2. Запуск стека
```bash
docker compose up --build -d
```
Compose поднимет всё, прогонит миграции и соберёт статику.

### 3. Создание суперпользователя
```bash
docker compose exec backend python manage.py createsuperuser
```

### 4. Открываем в браузере
| URL                                   | Что там                               |
|---------------------------------------|---------------------------------------|
| `http://localhost`                    | Главная (через Nginx)                 |
| `http://localhost:3000`               | React SPA (dev)                       |
| `http://localhost:8000/api/`          | DRF Browsable API                     |
| `http://localhost:8000/api/schema/`   | OpenAPI 3.0 schema (`drf-spectacular`)|
| `http://localhost:8000/api/docs/`     | Swagger UI                            |
| `http://localhost:8000/admin/`        | Django Admin                          |

### 5. Остановка
```bash
docker compose down            # сохранить данные
docker compose down -v         # удалить volumes (полная очистка)
```

---

## 9. Основные команды

### Backend (внутри контейнера)
```bash
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py makemigrations
docker compose exec backend python manage.py createsuperuser
docker compose exec backend python manage.py collectstatic --noinput
docker compose exec backend python manage.py shell_plus       # django-extensions
docker compose exec backend pytest --cov=apps                  # тесты + coverage
```

### Celery
```bash
docker compose logs -f celery_worker
docker compose logs -f celery_beat
docker compose exec backend celery -A config inspect active    # активные задачи
docker compose exec backend celery -A config purge             # очистить очередь
```

### Frontend
```bash
docker compose exec frontend npm run dev      # vite dev server
docker compose exec frontend npm run build    # production build
docker compose exec frontend npm run lint     # ESLint
```

### База данных
```bash
docker compose exec db psql -U bookingengine -d bookingengine
docker compose exec db pg_dump -U bookingengine bookingengine > backup.sql
```

---

## 10. Ручной запуск frontend и backend

Если хочется запускать сервисы напрямую (без Docker для backend/frontend), но с Docker для PostgreSQL и Redis:

### Backend
```bash
docker compose up -d db redis

cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

### Celery (в отдельных терминалах)
```bash
celery -A config worker -l info --concurrency=4
celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# http://localhost:5173
```

---

## 11. Конфигурация и переменные окружения

Все переменные читаются через `django-environ` из `.env`.

### Обязательные
| Переменная                   | Описание                                  | Пример                                      |
|------------------------------|-------------------------------------------|---------------------------------------------|
| `SECRET_KEY`                 | Django secret key                         | `django-insecure-...`                       |
| `DEBUG`                      | Режим отладки                             | `True` / `False`                            |
| `ALLOWED_HOSTS`              | Разрешённые хосты                         | `localhost,127.0.0.1,booking.example.com`   |
| `DATABASE_URL`               | Postgres DSN                              | `postgres://user:pass@db:5432/bookingengine`|
| `REDIS_URL`                  | Redis DSN (кэш)                           | `redis://redis:6379/0`                      |
| `CELERY_BROKER_URL`          | Redis DSN (брокер)                        | `redis://redis:6379/1`                      |
| `STRIPE_SECRET_KEY`          | Stripe секрет                             | `sk_test_...`                               |
| `STRIPE_PUBLISHABLE_KEY`     | Stripe публичный                          | `pk_test_...`                               |
| `STRIPE_WEBHOOK_SECRET`      | Stripe webhook signing                    | `whsec_...`                                 |

### Email / SMTP
| Переменная                   | По умолчанию                                  |
|------------------------------|-----------------------------------------------|
| `EMAIL_HOST`                 | `smtp.gmail.com`                              |
| `EMAIL_PORT`                 | `587`                                         |
| `EMAIL_USE_TLS`              | `True`                                        |
| `EMAIL_HOST_USER`            | —                                             |
| `EMAIL_HOST_PASSWORD`        | —                                             |
| `DEFAULT_FROM_EMAIL`         | `noreply@bookingengine.com`                   |

### Интеграции календарей
| Переменная                   | Описание                                |
|------------------------------|-----------------------------------------|
| `GOOGLE_CLIENT_ID`           | Google OAuth Client ID                  |
| `GOOGLE_CLIENT_SECRET`       | Google OAuth Client Secret              |
| `GOOGLE_REDIRECT_URI`        | `https://your.app/api/integrations/google/callback/` |
| `OUTLOOK_CLIENT_ID`          | Microsoft App Client ID                 |
| `OUTLOOK_CLIENT_SECRET`      | Microsoft App Client Secret             |
| `OUTLOOK_REDIRECT_URI`       | `https://your.app/api/integrations/outlook/callback/` |

### Frontend
| Переменная                   | Описание                                |
|------------------------------|-----------------------------------------|
| `REACT_APP_API_URL`          | URL backend API                         |
| `REACT_APP_STRIPE_KEY`       | Stripe publishable key                  |

---

## 12. API, очереди и интеграции

### Аутентификация (JWT)
```http
POST /api/auth/register/        — регистрация
POST /api/auth/token/           — получить access + refresh
POST /api/auth/token/refresh/   — обновить access
POST /api/auth/token/blacklist/ — выйти
```

В заголовках: `Authorization: Bearer <access_token>`

### Основные эндпоинты
| Метод     | URL                                           | Назначение                       |
|-----------|-----------------------------------------------|----------------------------------|
| `GET/POST`| `/api/calendars/`                             | Календари                        |
| `GET/POST`| `/api/calendars/{id}/availability-rules/`     | Правила доступности              |
| `GET/POST`| `/api/event-types/`                           | Типы встреч                      |
| `GET/POST`| `/api/booking-pages/`                         | Страницы бронирования            |
| `GET`     | `/api/p/{slug}/`                              | **Публичная** страница           |
| `GET`     | `/api/p/{slug}/available-slots/`              | **Публичные** свободные слоты    |
| `POST`    | `/api/p/{slug}/book/`                         | **Публичное** бронирование       |
| `GET/POST`| `/api/bookings/`                              | Брони (auth)                     |
| `POST`    | `/api/bookings/{id}/cancel/`                  | Отменить                         |
| `POST`    | `/api/bookings/{id}/reschedule/`              | Перенести                        |
| `GET/POST`| `/api/integrations/`                          | Подключённые календари           |
| `GET`     | `/api/integrations/google/connect/`           | OAuth start (Google)             |
| `GET`     | `/api/integrations/outlook/connect/`          | OAuth start (Outlook)            |
| `POST`    | `/api/payments/create-intent/`                | Stripe PaymentIntent             |
| `POST`    | `/api/payments/webhook/`                      | Stripe webhook receiver          |

Полная спецификация — **Swagger UI**: `/api/docs/` (OpenAPI 3.0).

### Очереди Celery

| Задача                              | Когда выполняется                                 |
|-------------------------------------|---------------------------------------------------|
| `notifications.send_confirmation`   | Сразу после создания брони                        |
| `notifications.send_reminder`       | По расписанию (Beat) — T-24h, T-1h                |
| `integrations.sync_calendar`        | Каждые 10 минут на подключённый календарь         |
| `integrations.push_to_external`     | После create/reschedule/cancel                    |
| `bookings.mark_no_shows`            | Каждый час: брони, прошедшие без отметки complete |
| `payments.reconcile_stripe`         | Каждую ночь: сверка с Stripe                      |

---

## 13. Мониторинг и эксплуатация

### Healthchecks
- **Postgres**: `pg_isready` (compose healthcheck)
- **Redis**: `redis-cli ping` (compose healthcheck)
- **Backend**: `GET /api/health/` — отвечает 200 OK, проверяет БД и Redis

### Логи
```bash
docker compose logs -f backend
docker compose logs -f celery_worker
docker compose logs -f nginx
```

Рекомендуется направлять логи в централизованную систему: **Sentry** (исключения), **Loki/ELK** (агрегация).

### Метрики (рекомендация)
- `django-prometheus` → `/metrics` → Prometheus → Grafana
- Базовые дашборды: request latency, error rate, Celery queue depth, DB connections

---

## 14. CI/CD

Рекомендованный pipeline (GitHub Actions):

| Этап              | Что делает                                                            |
|-------------------|------------------------------------------------------------------------|
| **Lint**          | `ruff` / `black --check` (backend), `eslint` (frontend), `tsc --noEmit`|
| **Test**          | `pytest --cov=apps` в Postgres-сервисе                                |
| **Build**         | `docker build` для backend и frontend, push в registry                |
| **Deploy (stg)**  | `docker compose pull && docker compose up -d` на staging              |
| **Smoke**         | Проверка `/api/health/`, базовые E2E                                  |
| **Deploy (prod)** | По approval — на production                                           |

Артефакты: Docker-образы (теги по commit SHA), coverage report, OpenAPI schema.

---

## 15. Безопасность и приватность данных

| Что защищается              | Как                                                                              |
|-----------------------------|----------------------------------------------------------------------------------|
| Пароли                      | Django PBKDF2 (по умолчанию), опционально argon2                                 |
| Токены интеграций           | Шифруются `cryptography.Fernet` перед сохранением в БД                           |
| JWT-токены                  | access TTL 15 минут, refresh TTL 7 дней, blacklist при logout                    |
| Stripe webhooks             | Проверка подписи `STRIPE_WEBHOOK_SECRET`, идемпотентность по event ID            |
| CSRF                        | Включён для admin и сессионных запросов                                          |
| CORS                        | Whitelist через `CORS_ALLOWED_ORIGINS`                                           |
| Rate limiting               | DRF throttling + Nginx `limit_req_zone`                                          |
| SQL Injection               | Django ORM (параметризованные запросы)                                           |
| XSS                         | React (автоэкранирование), Django templates (autoescape)                         |
| Secret management           | `.env` не коммитится; продакшен — Vault / AWS Secrets Manager / Docker secrets   |
| HTTPS                       | TLS termination в Nginx + HSTS в production-настройках                           |
| Multi-tenancy isolation     | Все queries фильтруются по `request.user.organization`                           |
| PII                         | Минимальный объём; ретеншн настраивается; soft-delete + cron на полное удаление  |

---

## 16. Роли компонентов в продакшене

| Компонент       | Роль в production                                                                          |
|-----------------|--------------------------------------------------------------------------------------------|
| **Nginx**       | Принимает HTTPS, делает TLS termination, раздаёт `/static` и `/media`, проксирует `/api`   |
| **Gunicorn**    | WSGI-сервер для Django, 4 sync-worker'а, timeout 120s                                      |
| **Django**      | Бизнес-логика, ORM, аутентификация, валидация, сериализация                                |
| **Celery**      | Асинхронные задачи: email, sync календарей, напоминания, webhooks                          |
| **Celery Beat** | Периодические задачи (cron-like), хранит расписание в БД                                   |
| **PostgreSQL**  | Источник правды: пользователи, брони, события, аудит                                       |
| **Redis**       | Кэш, очереди Celery, distributed locks (для рассинхронизаций между worker'ами)             |
| **React SPA**   | Клиентский интерфейс, рендерится в браузере, общается только через `/api`                  |
| **Stripe**      | Внешний платёжный провайдер, синхронизация через webhooks                                  |
| **Google/MS**   | Внешние календари, синхронизация через OAuth + REST API                                    |

---

## 17. Лицензия

**Proprietary software**. Все права защищены © 2026 Nodir Odilov.

Для коммерческого использования, форка, или внедрения в собственный продукт — свяжитесь с автором.

---

## 18. Поддержка

- **Issues**: [GitHub Issues](https://github.com/NodirOdilov/BookingEngine/issues)
- **Email**: см. профиль автора
- **Telegram**: см. профиль автора

---

<div align="center">

**BookingEngine** — built with care for teams that respect their customers' time.

⭐ Если проект пригодился — поставьте звезду на GitHub.

</div>
