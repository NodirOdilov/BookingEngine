# BookingEngine - Appointment Scheduling SaaS

A production-grade appointment scheduling platform similar to Calendly, built with Django, React, PostgreSQL, Redis, and Celery. Supports calendar management, booking pages, availability rules, time zones, buffer times, payment collection, reminders, calendar integrations (Google/Outlook), and team scheduling.

## Architecture Overview

```
                    +-------------------+
                    |   Nginx (Proxy)   |
                    +--------+----------+
                             |
              +--------------+--------------+
              |                             |
     +--------v--------+         +---------v--------+
     | React Frontend  |         | Django API       |
     | (Port 3000)     |         | (Port 8000)      |
     +-----------------+         +--------+---------+
                                          |
                        +-----------------+-----------------+
                        |                 |                 |
               +--------v---+    +--------v---+    +-------v-------+
               | PostgreSQL |    |   Redis    |    | Celery Worker |
               | (Port 5432)|    | (Port 6379)|    | (Beat + Worker)|
               +------------+    +------------+    +---------------+
```

## Features

- **Calendar Management**: Create and manage multiple calendars with customizable availability rules
- **Booking Pages**: Public booking pages with custom branding, slugs, and embedded widgets
- **Availability Rules**: Flexible weekly schedules, date overrides, blocked times, and buffer management
- **Time Zone Support**: Full IANA timezone support with automatic conversion for invitees
- **Buffer Times**: Configurable pre/post-event buffers and minimum scheduling notice
- **Payment Collection**: Stripe integration for paid appointments with refund support
- **Reminders & Notifications**: Email/SMS reminders via Celery with customizable templates
- **Calendar Integrations**: Two-way sync with Google Calendar and Microsoft Outlook
- **Team Scheduling**: Organizations, team members, round-robin and collective event types
- **Event Types**: Multiple durations, locations (in-person, phone, video), custom questions

## Tech Stack

| Component       | Technology                          |
|-----------------|-------------------------------------|
| Backend API     | Django 5.x + Django REST Framework  |
| Frontend        | React 18 + Redux Toolkit           |
| Database        | PostgreSQL 16                       |
| Cache/Broker    | Redis 7                             |
| Task Queue      | Celery 5.x + Celery Beat           |
| Reverse Proxy   | Nginx                               |
| Containerization| Docker + Docker Compose             |
| Payments        | Stripe API                          |
| Email           | SMTP (SendGrid/SES compatible)      |

## Prerequisites

- Docker and Docker Compose v2+
- Git
- (Optional) Node.js 20+ and Python 3.12+ for local development

## Quick Start

### 1. Clone and configure

```bash
git clone <repository-url>
cd BookingEngine
cp .env.example .env
# Edit .env with your actual values (see Configuration section below)
```

### 2. Start with Docker Compose

```bash
docker compose up --build -d
```

This starts all services:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/api/
- **Admin Panel**: http://localhost:8000/admin/

### 3. Run initial setup

```bash
# Apply database migrations
docker compose exec backend python manage.py migrate

# Create superuser
docker compose exec backend python manage.py createsuperuser

# (Optional) Load sample data
docker compose exec backend python manage.py loaddata sample_data
```

## Configuration

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key | `your-secret-key-here` |
| `DATABASE_URL` | PostgreSQL connection string | `postgres://user:pass@db:5432/bookingengine` |
| `REDIS_URL` | Redis connection string | `redis://redis:6379/0` |
| `STRIPE_SECRET_KEY` | Stripe API secret key | `sk_test_...` |
| `STRIPE_PUBLISHABLE_KEY` | Stripe publishable key | `pk_test_...` |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret | `whsec_...` |

### Optional Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_CLIENT_ID` | Google OAuth client ID | - |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret | - |
| `OUTLOOK_CLIENT_ID` | Microsoft OAuth client ID | - |
| `OUTLOOK_CLIENT_SECRET` | Microsoft OAuth client secret | - |
| `EMAIL_HOST` | SMTP host | `smtp.gmail.com` |
| `EMAIL_PORT` | SMTP port | `587` |
| `DEFAULT_FROM_EMAIL` | Sender email address | `noreply@bookingengine.com` |
| `FRONTEND_URL` | Frontend base URL | `http://localhost:3000` |

## API Documentation

### Authentication

The API uses JWT token authentication. Obtain tokens via:

```
POST /api/auth/token/
{
    "email": "user@example.com",
    "password": "password"
}
```

Include the access token in subsequent requests:
```
Authorization: Bearer <access_token>
```

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register/` | Register new user |
| POST | `/api/auth/token/` | Obtain JWT tokens |
| POST | `/api/auth/token/refresh/` | Refresh access token |
| GET/POST | `/api/calendars/` | List/create calendars |
| GET/PUT/DELETE | `/api/calendars/{id}/` | Calendar detail |
| GET/POST | `/api/calendars/{id}/availability-rules/` | Availability rules |
| GET/POST | `/api/event-types/` | List/create event types |
| GET/PUT/DELETE | `/api/event-types/{id}/` | Event type detail |
| GET/POST | `/api/bookings/` | List/create bookings |
| GET/PUT/DELETE | `/api/bookings/{id}/` | Booking detail |
| POST | `/api/bookings/{id}/cancel/` | Cancel booking |
| POST | `/api/bookings/{id}/reschedule/` | Reschedule booking |
| GET | `/api/booking-pages/` | List booking pages |
| GET | `/api/p/{slug}/` | Public booking page |
| GET | `/api/p/{slug}/available-slots/` | Available time slots |
| POST | `/api/p/{slug}/book/` | Create public booking |
| GET/POST | `/api/integrations/` | Calendar integrations |
| POST | `/api/payments/create-intent/` | Create payment intent |
| POST | `/api/payments/webhook/` | Stripe webhook |

## Development

### Backend (without Docker)

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Frontend (without Docker)

```bash
cd frontend
npm install
npm start
```

### Running Celery workers locally

```bash
cd backend
celery -A config worker -l info
celery -A config beat -l info
```

### Running Tests

```bash
# Backend tests
docker compose exec backend python manage.py test

# Frontend tests
docker compose exec frontend npm test
```

## Deployment

### Production Checklist

- [ ] Set `DEBUG=False` in production environment
- [ ] Configure a strong `SECRET_KEY`
- [ ] Set up SSL/TLS certificates in Nginx
- [ ] Configure proper `ALLOWED_HOSTS` and `CORS_ALLOWED_ORIGINS`
- [ ] Set up database backups for PostgreSQL
- [ ] Configure monitoring (Sentry, Prometheus, etc.)
- [ ] Set up log aggregation
- [ ] Configure rate limiting in Nginx
- [ ] Enable Stripe live mode keys
- [ ] Set up email delivery service (SendGrid, AWS SES)
- [ ] Configure Google/Outlook OAuth credentials for production

## Project Structure

```
BookingEngine/
├── backend/
│   ├── apps/
│   │   ├── accounts/        # User auth, organizations, teams
│   │   ├── bookings/        # Booking management
│   │   ├── booking_pages/   # Public booking page customization
│   │   ├── calendars/       # Calendar and availability
│   │   ├── event_types/     # Event type configuration
│   │   ├── integrations/    # Google/Outlook calendar sync
│   │   ├── notifications/   # Email/SMS notifications
│   │   └── payments/        # Stripe payment processing
│   ├── config/
│   │   ├── settings/        # Split settings (base/dev/prod)
│   │   ├── celery.py        # Celery configuration
│   │   ├── urls.py          # Root URL configuration
│   │   └── wsgi.py          # WSGI entry point
│   ├── utils/               # Shared utilities
│   ├── manage.py
│   └── requirements.txt
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── api/             # API client and service modules
│   │   ├── components/      # Reusable React components
│   │   ├── hooks/           # Custom React hooks
│   │   ├── pages/           # Page-level components
│   │   ├── store/           # Redux store and slices
│   │   └── styles/          # Global styles
│   └── package.json
├── nginx/
│   └── nginx.conf
├── docker-compose.yml
├── .env.example
└── .gitignore
```

## License

This project is proprietary software. All rights reserved.
