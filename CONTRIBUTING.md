# Contributing to Data Intake Service

Thank you for your interest in contributing!

**Note:** This is a personal learning project focused on practicing production-ready Python backend development and data engineering API patterns. While contributions are welcome, the primary goal is educational rather than building production software. The service is intentionally over-engineered to practice various design patterns and tools—in reality, you'd use existing cloud data tooling instead.

## Getting Started

1. **Fork and clone the repository**

2. **Set up your development environment**
   ```bash
   # Create virtual environment (Python 3.13+ required)
   python3.13 -m venv .venv
   source .venv/bin/activate

   # Install dependencies
   pip install -e ".[dev]"

   # Install pre-commit hooks
   pre-commit install
   pre-commit install --hook-type commit-msg
   ```

3. **Create a feature branch**
   ```bash
   git checkout -b feat/your-feature-name
   ```

## Commit Messages

This project follows [Conventional Commits](https://www.conventionalcommits.org/) specification.

### Format

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, missing semicolons, etc.)
- **refactor**: Code refactoring (neither fixes a bug nor adds a feature)
- **test**: Adding or updating tests
- **chore**: Maintenance tasks (updating dependencies, etc.)
- **perf**: Performance improvements
- **ci**: CI/CD pipeline changes
- **build**: Build system changes (build scripts, package.json, etc.)
- **revert**: Revert a previous commit

### Scopes (optional)

Use scopes to specify which part of the codebase is affected:
- `api` - API endpoints
- `db` - Database models or migrations
- `service` - Service layer
- `repo` - Repository layer
- `test` - Testing infrastructure
- `deps` - Dependencies

### Examples

**Simple commit:**
```
feat: add job status endpoint
```

**Commit with scope:**
```
fix(api): handle null response from validation endpoint
```

**Breaking change:**
```
refactor!: change job status enum values

BREAKING CHANGE: Job status values have changed from snake_case to UPPER_CASE.
Clients must update their integrations.
```

**Commit with body:**
```
feat(db): add job retry tracking

Adds retry_count and last_retry_at fields to the jobs table
to support automatic retry logic for failed jobs.
```

### Validation

Commits are validated both locally and in CI using [pre-commit](https://pre-commit.com/):

**Local validation:**
- Pre-commit hook validates your commit message format before the commit is created
- If validation fails, fix your commit message and try again
- Hooks also check code formatting, type hints, and other quality issues

**CI validation:**
- All commits in a PR are validated by the pre-commit CI workflow
- PRs with invalid commits will be blocked from merging

## Code Quality

This project uses pre-commit hooks to maintain code quality. They run automatically when you commit.

**Run all checks manually:**
```bash
# Run all pre-commit hooks
pre-commit run --all-files

# Run tests with coverage
pytest tests/ --cov=app --cov-report=term-missing --cov-fail-under=70 -v

# Security audit
pip-audit
```

**Pre-commit hooks include:**
- Trailing whitespace removal
- End-of-file fixes
- YAML/JSON/TOML validation
- Ruff linting and formatting
- mypy type checking
- Conventional commit validation
- Debug statement detection

## Pull Request Process

1. **Create your feature branch** from `main`
2. **Make your changes** following the code style and commit conventions
3. **Add tests** for any new functionality
4. **Run the quality checks** locally
5. **Push your branch** to your fork
6. **Open a Pull Request** against the `main` branch

### PR Title

Use conventional commit format for your PR title:
```
feat: add user authentication system
fix(api): resolve validation error handling
docs: update API documentation
```

### PR Description

Include:
- **What**: Brief description of the changes
- **Why**: Why these changes are needed
- **Testing**: How you tested the changes
- **Screenshots**: If applicable (for UI changes)

### CI Checks

All PRs must pass these checks before merging:
- ✅ Pre-commit hooks (formatting, type checking, conventional commits, etc.)
- ✅ Tests with 70% minimum coverage
- ✅ Security audit (no known vulnerabilities)

## Testing

### Running Tests

```bash
# All tests
pytest tests/

# Specific test file
pytest tests/unit/services/test_job_service.py -v

# Tests matching a pattern
pytest tests/ -k "test_job" -v

# With coverage report
pytest tests/ --cov=app --cov-report=html
open htmlcov/index.html  # View coverage report
```

### Writing Tests

- **Unit tests**: Test individual components in isolation (use fakes for dependencies)
- **Integration tests**: Test components working together (use real database)
- **E2E tests**: Test complete user workflows (use TestClient)

Place tests in the appropriate directory:
- `tests/unit/` - Unit tests with mocks/fakes
- `tests/integration/` - Integration tests with real dependencies
- `tests/e2e/` - End-to-end tests

### Test Fixtures

Use fixtures from `tests/conftest.py`

## Code Style

### Python Style

- **Line length**: 88 characters (Ruff default)
- **Type hints**: Use type hints for all function signatures
- **Imports**: Organized by stdlib, third-party, local (handled by Ruff)
- **Naming**:
  - Functions/variables: `snake_case`
  - Classes: `PascalCase`
  - Constants: `UPPER_CASE`

### Architecture

Follow the layered architecture:

```
api/ ──→ services/ ──→ repositories/ ──→ db/
```

- **API layer**: HTTP endpoints, request/response handling
- **Service layer**: Business logic
- **Repository layer**: Data access
- **DB layer**: SQLAlchemy models

**Rules:**
- API and services must never import from each other
- Lower layers must never import from upper layers
- Use dependency injection (pass repositories to services)

## Questions?

If you have questions or need help:
- Check the [README](README.md) for setup instructions
- Review the [workflow documentation](.github/workflows/README.md)
- Open an issue for discussion

Thank you for contributing! 🎉
