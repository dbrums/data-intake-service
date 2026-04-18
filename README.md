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
# Create and activate a virtual environment (Python 3.13+ required)
python3.13 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

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

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=app --cov-report=term-missing

# Run specific test file
pytest tests/unit/services/test_job_service.py -v

# Run tests matching a pattern
pytest tests/ -k "test_job" -v
```

### Code Quality Checks

This project uses [pre-commit](https://pre-commit.com/) to enforce code quality. Hooks run automatically on `git commit`.

**Automatic checks on commit:**
- Trailing whitespace removal
- End-of-file fixes
- Black code formatting
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
# Format code with Black
black app/ tests/

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

The CI workflow runs on Python 3.13.

#### Coverage Reports

Coverage reports are automatically posted as comments on pull requests, showing:
- Overall coverage percentage
- Coverage changes introduced by the PR
- Line-by-line coverage details

#### Status Checks

All checks must pass before code can be merged. Failed checks will block merging.

See [.github/workflows/README.md](.github/workflows/README.md) for more details about the CI workflow.
