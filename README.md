# Data Intake Service

[![CI](https://github.com/dbrums/data-intake-service/actions/workflows/ci.yml/badge.svg)](https://github.com/dbrums/data-intake-service/actions/workflows/ci.yml)
[![pre-commit](https://github.com/dbrums/data-intake-service/actions/workflows/pre-commit.yml/badge.svg)](https://github.com/dbrums/data-intake-service/actions/workflows/pre-commit.yml)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-yellow.svg)](https://conventionalcommits.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

> **Note:** This is a personal project for practicing production-ready Python backend development and data engineering API design. The service itself is intentionally over-engineered—any reasonably experienced data engineer would simply use existing cloud tooling (AWS Glue, GCP Dataflow, Azure Data Factory, etc.) rather than building a custom data intake service. The goal here is to demonstrate solid software engineering practices, not to solve a real-world problem.

A FastAPI service that accepts dataset uploads or pull requests, validates them
against declared schemas and business rules, stores results, and exposes job
status and validation reports through an API.

## Table of Contents

- [Job Lifecycle](#job-lifecycle)
- [Project Structure](#project-structure)
- [Docker Setup (Recommended)](#docker-setup-recommended)
  - [VS Code Devcontainer](#vs-code-devcontainer-recommended-for-vs-code-users)
  - [Quick Start](#quick-start-without-devcontainer)
  - [Common Docker Commands](#common-docker-commands)
  - [Development Workflow](#development-workflow)
- [Native Setup (Alternative)](#native-setup-alternative)
- [Development](#development)
  - [Running Tests](#running-tests)
  - [Code Quality Checks](#code-quality-checks)
  - [Commit Message Convention](#commit-message-convention)
  - [CI/CD](#cicd)
- [Additional Documentation](#additional-documentation)

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

## Docker Setup (Recommended)

The fastest way to get started is using Docker Compose, which runs the FastAPI app and PostgreSQL together.

### Prerequisites
- Docker and Docker Compose installed
- (Optional) VS Code for devcontainer support

### VS Code Devcontainer (Recommended for VS Code users)

If you're using VS Code, you can develop inside the container with full IDE integration:

1. Install the "Dev Containers" extension in VS Code
2. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
3. Open the project in VS Code
4. Click "Reopen in Container" when prompted (or run "Dev Containers: Reopen in Container" from the command palette)
5. VS Code will build and start the containers, then connect you to the development environment
6. Your terminal, debugger, and IntelliSense will all run inside the container

With devcontainer:
- No need for `docker-compose exec` - your terminal is already inside the container
- Run commands directly: `pytest`, `alembic upgrade head`, `uvicorn app.main:app --reload`
- Debug FastAPI directly with VS Code breakpoints
- Extensions (Ruff, mypy, Python) install automatically

**Git configuration:**
Git user configuration is set at the repository level (not mounted from host). After cloning, set your git identity:

```bash
git config user.name "Your Name"
git config user.email "your.email@example.com"
```

The devcontainer automatically strips macOS-specific SSH options (`UseKeychain`, `AddKeysToAgent`) from your mounted SSH config to ensure compatibility with Linux.

### Quick Start (without devcontainer)

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

   By default, this configures the application to use PostgreSQL. You can optionally change `DATABASE_URL` in `.env` to use SQLite for local development:
   ```bash
   # PostgreSQL (default, recommended)
   DATABASE_URL=postgresql://postgres:postgres@db:5432/data_intake

   # Or SQLite (no Docker required)
   DATABASE_URL=sqlite:///./data_intake.db
   ```

2. Start the services:
   ```bash
   docker-compose up
   ```

3. The API will be available at `http://localhost:8000`
4. PostgreSQL will be available at `localhost:5432`

### Common Docker Commands

```bash
# Start services in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services (preserves data)
docker-compose down

# Stop services and remove volumes (fresh start)
docker-compose down -v

# Rebuild after dependency changes
docker-compose up --build

# Run tests
docker-compose exec web pytest

# Create a migration
docker-compose exec web alembic revision --autogenerate -m "description"

# Access PostgreSQL directly
docker-compose exec db psql -U postgres -d data_intake

# Run any command in the web container
docker-compose exec web <command>
```

### Development Workflow

- Edit code on your host machine
- Changes are automatically reflected (hot reload enabled)
- PostgreSQL data persists in a Docker volume across restarts

## Native Setup (Alternative)

If you prefer to run without Docker, you can use a Python virtual environment.

```bash
# Create and activate a virtual environment (Python 3.13+ required)
python3.13 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Copy and configure environment file
cp .env.example .env

# Configure DATABASE_URL in .env:
#   - For PostgreSQL: postgresql://postgres:postgres@localhost:5432/data_intake
#     (requires PostgreSQL installed and running locally)
#   - For SQLite: sqlite:///./data_intake.db
#     (no external database needed)

# Install pre-commit hooks (enforces code quality and conventional commits)
pre-commit install
pre-commit install --hook-type commit-msg

# Run database migrations
alembic upgrade head

# Start the dev server
uvicorn app.main:app --reload
```

## Development

### Running Tests

Tests can run against **SQLite** (fast, default) or **PostgreSQL** (production parity).

> **Note:** Test database is configured via `TEST_DATABASE_URL` environment variable, separate from the application runtime database (`DATABASE_URL` in `.env`).

```bash
# Run all tests (SQLite in-memory by default - fast)
pytest tests/

# Run with coverage
pytest tests/ --cov=app --cov-report=term-missing

# Run specific test file
pytest tests/unit/services/test_job_service.py -v

# Run tests matching a pattern
pytest tests/ -k "test_job" -v

# Run against PostgreSQL (requires docker-compose up -d db)
TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/data_intake pytest tests/
```

#### Test Database Configuration

| Database | Speed | Use Case | Configuration |
|----------|-------|----------|---------------|
| **SQLite** (default) | ⚡ ~0.15s | Local TDD, fast feedback | None needed |
| **PostgreSQL** | 🐢 ~0.5s | Pre-deploy validation, CI reproduction | `TEST_DATABASE_URL=postgresql://...` |

**When to use PostgreSQL:**
- Before pushing to catch dialect-specific bugs
- To reproduce CI failures locally
- When testing Postgres-specific features (JSONB, arrays, etc.)

**CI always uses PostgreSQL** to ensure production parity. See [.github/workflows/ci.yml](.github/workflows/ci.yml) for details.

### Code Quality Checks

This project uses [pre-commit](https://pre-commit.com/) to enforce code quality. Hooks run automatically on `git commit`.

**Automatic checks on commit:**
- Trailing whitespace removal
- End-of-file fixes
- Ruff linting and formatting
- mypy type checking
- Conventional commit message format

**Run all checks manually:**
```bash
# Run all pre-commit hooks on all files
pre-commit run --all-files

# Run on staged files only
pre-commit run

# Skip hooks for a commit (not recommended)
git commit --no-verify
```

**Individual tools (if needed):**
```bash
# Lint and format code with Ruff
ruff check . --fix
ruff format .

# Type checking with mypy
mypy app/

# Security audit
pip-audit
```

### Commit Message Convention

This project follows [Conventional Commits](https://www.conventionalcommits.org/) specification. All commit messages must be in the format:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Allowed types:** `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`, `ci`, `build`, `revert`

**Scopes:** `api`, `db`, `service`, `repo`, `test`, `ci`, `deps`, `config`

**Examples:**
- `feat(api): add user authentication`
- `fix(db): handle null response from endpoint`
- `docs: update README with setup instructions`
- `refactor(api)!: change API response structure` (breaking change)

**Creating commits:**

If using Claude Code, you can use the `/commit` skill for guided commit creation:
```
/commit
```

This will:
1. Review your staged changes
2. Generate a properly formatted conventional commit message
3. Ask for your approval or edits
4. Create the commit

Or commit manually:
```bash
git commit -m "feat(api): add something"
```

**Enforcement:**
- Pre-commit hook validates commit messages locally
- CI validates all commits in pull requests via pre-commit

### CI/CD

This project uses GitHub Actions for continuous integration. On every pull request, the following checks are performed:

1. **pre-commit**: Runs all pre-commit hooks (formatting, type checking, conventional commits, etc.)
2. **Tests**: pytest runs the full test suite with coverage reporting
3. **Coverage**: Minimum 70% coverage required (enforced)
4. **Security**: pip-audit scans for known vulnerabilities in dependencies

The CI workflow runs on Python 3.13 and **always uses PostgreSQL** to ensure production parity. Local development defaults to SQLite for speed.

#### Coverage Reports

Coverage reports are automatically posted as comments on pull requests, showing:
- Overall coverage percentage
- Coverage changes introduced by the PR
- Line-by-line coverage details

#### Status Checks

All checks must pass before code can be merged. Failed checks will block merging.

See [.github/workflows/README.md](.github/workflows/README.md) for more details about the CI workflow.

## Additional Documentation

- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines and development workflow
- **[.github/workflows/README.md](.github/workflows/README.md)** - CI/CD pipeline documentation
