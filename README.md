# TaskFlow

A self-hosted Kanban board for personal and small-team task management. Multi-user, with drag-and-drop, JWT authentication, and a SQLite-backed REST API.

## Features

- **Auth** — register, login, password hashing (bcrypt), JWT-based sessions
- **Boards** — create multiple boards per user
- **Columns** — customizable, ordered columns per board (default: Todo / Doing / Done)
- **Cards** — title, description, priority, due date, ordered within a column
- **Drag-and-drop** — reorder cards within a column, move cards between columns
- **REST API** — fully documented at `/docs` via FastAPI's automatic OpenAPI
- **Self-hosted** — one docker-compose command and you're running

## Stack

| Layer | Choice |
|------|--------|
| Backend | Python 3.11+, FastAPI, SQLAlchemy 2.x, Pydantic v2 |
| Database | SQLite (default) — swap to Postgres via `DATABASE_URL` |
| Auth | Bcrypt + JWT (`python-jose`) |
| Frontend | Vanilla HTML/CSS/JS + SortableJS for drag-and-drop |
| Container | Docker + docker-compose |
| CI | GitHub Actions (tests on 3.10 / 3.11 / 3.12 + Docker smoke test) |

## Quick start (Docker)

```bash
docker compose up --build
# open http://localhost:8000
```

The frontend is served from the same origin as the API.

## Local development

```bash
make install    # install backend deps
make serve      # run with reload
make test       # run pytest
```

## API

Once running, see `http://localhost:8000/docs` for the full interactive API.

Highlights:

```
POST /api/auth/register   { "email", "password" }
POST /api/auth/login      { "email", "password" }  → { "access_token" }

GET    /api/boards
POST   /api/boards        { "name" }
DELETE /api/boards/{id}

POST   /api/boards/{id}/columns
POST   /api/columns/{id}/cards
PATCH  /api/cards/{id}/move   { "column_id", "position" }
```

All endpoints other than `/api/auth/*` require `Authorization: Bearer <token>`.

## License

MIT
