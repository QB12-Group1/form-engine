# Form Engine

Dynamic form builder written with Django REST Framework.

## Docker development stack

The Docker Compose stack includes Django running on Uvicorn, Nginx, PostgreSQL,
Redis, a Celery worker, Flower, and Swagger UI. Copy `.env.example` to `.env`
and update the secret and credentials before starting it.

```sh
docker compose up --build
```

- Application, Django admin, and Swagger UI: `http://localhost:8080`
- OpenAPI schema: `http://localhost:8080/api/schema/`
- Swagger UI: `http://localhost:8080/api/schema/swagger-ui/`
- Flower: `http://localhost:5555` (bound to localhost only)

The `web` service applies migrations and collects static files at startup. Use
`docker compose down` to stop the stack; add `-v` only when you intentionally
want to delete the PostgreSQL, Redis, and static-file volumes.

## Production-oriented Docker stack

`compose.production.yaml` is a separate deployment stack with non-root Django
containers, internal-only PostgreSQL and Redis, password-protected Redis,
restart policies, health checks, a separate migration job, and hardened Nginx.
It expects TLS to be terminated by an upstream load balancer or reverse proxy.

```sh
cp .env.production.example .env.production
# Set unique, strong values in .env.production.
docker compose --env-file .env.production -f compose.production.yaml up -d postgres redis
docker compose --env-file .env.production -f compose.production.yaml run --rm migrate
docker compose --env-file .env.production -f compose.production.yaml up -d --build
```

Flower is intentionally not started by default. It is bound to localhost and
requires `FLOWER_BASIC_AUTH` when explicitly enabled:

```sh
docker compose --env-file .env.production -f compose.production.yaml --profile observability up -d flower
```

Before public deployment, configure HTTPS at the upstream proxy, set
`DJANGO_ALLOWED_HOSTS` and `DJANGO_CORS_ALLOWED_ORIGINS` to real HTTPS domains,
and establish tested PostgreSQL backups.
