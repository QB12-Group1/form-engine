# Form Engine

A multi-tenant, team-based dynamic form builder built with Django and Django REST Framework.
Users organize their work inside **Workspaces**, build **Surveys** made of typed **Questions**
inside those workspaces, and collect **Responses** from respondents — all through a fully
documented REST API.

---

## Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Domain Model](#domain-model)
- [Features](#features)
  - [Authentication (`accounts`)](#authentication-accounts)
  - [Workspaces (`workspaces`)](#workspaces-workspaces)
  - [Surveys & Questions (`surveys`)](#surveys--questions-surveys)
  - [Responses (`responses`)](#responses-responses)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Production Deployment](#production-deployment)
- [Testing](#testing)
- [Code Quality](#code-quality)
- [Project Structure](#project-structure)
- [Documentation](#documentation)

---

## Overview

Form Engine lets a user:

1. Create a **Workspace** and invite teammates to collaborate in it via a shareable invite link
   (with an optional password).
2. Build any number of **Surveys** inside a workspace, each made of **Questions** with one of
   several supported types (Text, Single Choice, Multiple Choice, Dropdown, Rating), each type
   carrying its own validated configuration (character limits, option lists, selection bounds,
   rating ranges, etc.).
3. Publish a survey and collect **Responses** from respondents — no respondent account required.

The API is authenticated with JWT, fully documented through an interactive Swagger UI, and ships
with a Docker-based development and production stack.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language / Runtime | Python 3.12 |
| Web framework | Django 6.1 |
| API framework | Django REST Framework |
| Authentication | `djangorestframework-simplejwt` (JWT, with refresh rotation & blacklisting) |
| Social login | Google OAuth (`google-auth`) |
| API documentation | `drf-spectacular` (OpenAPI schema + Swagger UI) |
| Nested routing | `drf-nested-routers` |
| Database | PostgreSQL |
| Cache & message broker | Redis |
| Background tasks | Celery (+ Flower for monitoring) |
| ASGI server | Uvicorn |
| Reverse proxy | Nginx |
| Dependency management | [uv](https://docs.astral.sh/uv/) |
| Linting / formatting | Ruff |
| Type checking | Pyright |
| Containerization | Docker / Docker Compose |

---

## Domain Model

```
User ──owner──► Workspace ◄──members── User (many-to-many)
                    │
                    │ workspace
                    ▼
                  Survey
                    │
          ┌─────────┴─────────┐
          │ survey             │ survey
          ▼                    ▼
       Question          ResponseSession
          │                    │
          │ question           │ session
          └───────► Answer ◄───┘
```

- A **User** owns zero or more Workspaces and can also be a **member** of Workspaces owned by
  others.
- A **Workspace** groups Surveys together and controls who may access them (owner + members).
- A **Survey** belongs to exactly one Workspace and has a lifecycle status: `Draft` → `Published`
  → `Closed`.
- A **Question** belongs to exactly one Survey, has a type, and a type-specific `properties`
  payload.
- A **ResponseSession** represents one respondent's attempt at filling out a Survey.
- An **Answer** is one respondent's answer to one Question within one ResponseSession.

---

## Features

### Authentication (`accounts`)

The platform supports two distinct kinds of accounts on the same `User` model:

- **End users** — identified by email only, with no password. They authenticate via a one-time
  code (OTP) sent to their email, or via Google sign-in.
- **Staff/admin users** — identified by username and password, for access to the Django admin
  panel.

**Passwordless sign-up & sign-in (unified flow):**
- `POST /api/auth/otp/request/` — generates a short-lived, single-use verification code and
  queues its delivery by email through a Celery background task. The code is hashed before
  storage and rate-limited per email address.
- `POST /api/auth/otp/verify/` — validates the code; an unrecognized email is automatically
  registered, so sign-up and sign-in share one flow. Returns a JWT access/refresh token pair.

**Social sign-in:**
- `POST /api/auth/google/` — verifies a Google ID token server-side and signs the user in,
  resolving to the same account as the email/OTP flow when the email matches.

**Session management:**
- `GET /api/auth/me/`, `PATCH /api/auth/me/` — view and update the current user's profile.
- `POST /api/auth/token/refresh/` — exchanges a refresh token for a new access/refresh pair
  (refresh tokens rotate and the previous one is blacklisted).
- `POST /api/auth/token/blacklist/` — explicitly invalidates a refresh token (sign-out).

### Workspaces (`workspaces`)

A Workspace is a shared space with an owner, an optional password, and a list of members.

- Full CRUD on workspaces (only the owner may update or delete).
- `POST /api/workspaces/join/` — join a workspace using its invite token and, if the workspace is
  password-protected, its password.
- `POST /api/workspaces/{id}/refresh-invite-token/` — rotate the invite link.
- `GET /api/workspaces/{id}/members/` — list members.
- `GET /api/workspaces/{id}/members/{user_id}/`, `DELETE .../members/{user_id}/` — view or remove
  a member (a member may remove themselves; the owner cannot be removed).

### Surveys & Questions (`surveys`)

**Surveys** live inside a workspace and move through a simple lifecycle:

- `GET/POST /api/workspaces/{workspace_id}/surveys/` — list or create surveys in a workspace.
- `GET/PUT/PATCH/DELETE /api/surveys/{id}/` — manage a single survey.
- `POST /api/surveys/{id}/publish/`, `POST /api/surveys/{id}/close/` — transition its status.

**Questions** live inside a survey and support five types, each with its own validated
configuration schema:

| Type | Configuration options |
|---|---|
| Text | `placeholder`, `min_length`, `max_length` |
| Single Choice | `options` (2+), `allow_other` |
| Multiple Choice | `options` (2+), `min_selections`, `max_selections`, `allow_other` |
| Dropdown | `options` (2+), `placeholder`, `allow_other` |
| Rating | `min_value`, `max_value`, `min_label`, `max_label` |

Each type's configuration is validated by a dedicated serializer (e.g. ensuring
`min_selections` never exceeds `max_selections`, or that a rating's `max_value` is strictly
greater than its `min_value`) before the question is saved.

- `GET/POST /api/surveys/{survey_id}/questions/` — list or create questions in a survey.
- `GET/PUT/PATCH/DELETE /api/questions/{id}/` — manage a single question.
- `POST /api/surveys/{survey_id}/questions/reorder/` — reorder every question in a survey in one
  request by supplying the full, ordered list of question IDs.

Access to a survey or question is governed by membership in its parent workspace (owner or
member).

### Responses (`responses`)

The response-collection domain models a respondent's visit to a survey:

- **ResponseSession** — one respondent's session against a survey, tracking IP address, user
  agent, completion status, and submission time.
- **Answer** — one answer to one question within a response session, stored as free-form JSON to
  accommodate any question type's value shape.

---

## Getting Started

### Prerequisites

- Docker and Docker Compose

### Run the development stack

```sh
cp .env.example .env
# edit .env: set a real DJANGO_SECRET_KEY and review the other values
docker compose up --build
```

The `web` service applies database migrations and collects static files automatically on
startup.

| Service | URL |
|---|---|
| API / Django admin / Swagger UI | `http://localhost:8080` |
| Swagger UI | `http://localhost:8080/api/schema/swagger-ui/` |
| OpenAPI schema | `http://localhost:8080/api/schema/` |
| Flower (Celery monitoring) | `http://localhost:5555` (bound to localhost only) |

Stop the stack with `docker compose down`. Add `-v` only when you intentionally want to delete
the PostgreSQL, Redis, and static-file volumes.

### Creating an admin account

Staff/admin accounts use the classic username + password flow and can be created with:

```sh
docker compose exec web python manage.py createsuperuser
```

---

## Environment Variables

All environment-dependent configuration is read from a `.env` file (see `.env.example` for the
full list), covering:

- `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CORS_ALLOWED_ORIGINS`
- Database connection (`DATABASE_URL` or discrete `POSTGRES_*` variables)
- Cache and Celery broker (`CACHE_URL`, `CELERY_BROKER_URL`)
- Email delivery (`DJANGO_EMAIL_USE_SMTP` and standard SMTP settings, or the console backend for
  local development)
- `GOOGLE_CLIENT_ID` for verifying Google sign-in tokens

Keeping configuration outside the codebase means the same code runs correctly across local
development, CI, and production simply by changing environment values.

---

## Production Deployment

`compose.production.yaml` is a separate, hardened stack:

- Non-root application containers
- Internal-only PostgreSQL and Redis, with a password-protected Redis instance
- Restart policies and health checks on every service
- A dedicated one-off `migrate` job instead of running migrations from the web container
- Hardened Nginx configuration (security headers, static file caching)

```sh
cp .env.production.example .env.production
# set unique, strong values in .env.production
docker compose --env-file .env.production -f compose.production.yaml up -d postgres redis
docker compose --env-file .env.production -f compose.production.yaml run --rm migrate
docker compose --env-file .env.production -f compose.production.yaml up -d --build
```

Flower is disabled by default in production and must be explicitly enabled with
`FLOWER_BASIC_AUTH` set:

```sh
docker compose --env-file .env.production -f compose.production.yaml --profile observability up -d flower
```

Before exposing the stack publicly: terminate TLS at an upstream load balancer or proxy, set
`DJANGO_ALLOWED_HOSTS` and `DJANGO_CORS_ALLOWED_ORIGINS` to the real HTTPS domains, and configure
tested PostgreSQL backups.

---

## Testing

Tests are written with Django's built-in test framework (`django.test.TestCase`).

```sh
docker compose exec web python manage.py test
# or a single app:
docker compose exec web python manage.py test accounts
```

---

## Code Quality

- **Ruff** — linting and formatting, run automatically via pre-commit.
- **Pyright** — static type checking.
- **pre-commit** — runs Ruff, Pyright, and general hygiene checks (trailing whitespace, merge
  conflict markers, YAML/TOML validity, etc.) before every commit.

```sh
uv run pre-commit install
```

---

## Project Structure

```
backend/
├── accounts/     # Custom user model, OTP service, Google auth, JWT endpoints
├── workspaces/   # Workspace model, membership, invite links
├── surveys/      # Survey and Question models, per-type config validation
├── responses/    # ResponseSession and Answer models
├── config/       # Django settings, URL routing, Celery app and tasks
└── manage.py

docker/nginx/     # Nginx configuration (development and production)
documents/        # ERD, API contract, and other project documentation
compose.yaml                 # Development Docker Compose stack
compose.production.yaml      # Production Docker Compose stack
```

---

## Documentation

Supplementary design documents live in `documents/`:

- `erd.dbml` / `erd.pdf` — entity-relationship diagram of the data model
- `schema.yaml` — the project's OpenAPI schema, describing every endpoint, request, and response
