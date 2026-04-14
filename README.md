# Data Intake Service

A FastAPI service that accepts dataset uploads or pull requests, validates them
against declared schemas and business rules, stores results, and exposes job
status and validation reports through an API.

## Job Lifecycle

Jobs follow an explicit state machine. Transitions are validated — arbitrary
status updates are not allowed.

```
queued ──▶ running ──▶ succeeded
              │
              ▼
           failed ──▶ retry_scheduled ──▶ queued
              │
              ▼
          cancelled
```

### States

| State | Meaning |
|---|---|
| `queued` | Job accepted, waiting for a worker |
| `running` | Worker is actively processing |
| `succeeded` | Validation completed successfully |
| `failed` | Validation or processing failed |
| `cancelled` | Job was cancelled |
| `retry_scheduled` | Retry requested, will re-enter queue |

## Project Structure

```
app/
├── main.py              # FastAPI application entrypoint
├── api/                 # API layer: routers, dependencies, exception handlers
│   ├── deps.py          # Shared dependencies (DB sessions, auth, etc.)
│   ├── exception_handlers.py  # Maps app exceptions to HTTP responses
│   ├── router.py        # Top-level router aggregating all versions
│   └── v1/
│       ├── router.py    # V1 router aggregating v1 endpoints
│       └── endpoints/   # Individual endpoint modules
├── services/            # Business logic layer
├── repositories/        # Data access layer
├── schemas/             # Pydantic request/response schemas
│   ├── jobs.py          # Job-related schemas
│   ├── validation.py    # Validation result schemas
│   ├── datasets.py      # Dataset schema schemas
│   └── common.py        # Shared types: pagination, errors, enums
├── db/                  # Database engine, session, base model
│   ├── session.py       # Session factory (shared by API and workers)
│   └── models/          # SQLAlchemy ORM models
├── core/                # App configuration and shared utilities
│   ├── config.py        # Pydantic Settings loaded from .env
│   ├── exceptions.py    # Application-level exception classes
│   └── logging.py       # Logging configuration
├── workers/             # Background / async task workers
└── clients/             # External HTTP / SDK clients
tests/                   # Test suite
├── api/                 # API endpoint tests
├── services/            # Service layer tests
├── repositories/        # Repository layer tests
└── workers/             # Worker tests
alembic/                 # Alembic migration environment
```

### Dependency direction

```
api/     ─┐
           ├──▶ services/ ──▶ repositories/ ──▶ db/
workers/ ─┘
```

`api/` and `workers/` are siblings. They must never import from each other.
Services, repositories, and database code must never import from `api/` or
`workers/`.

## Getting Started

```bash
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Run database migrations
alembic upgrade head

# Start the dev server
uvicorn app.main:app --reload
```