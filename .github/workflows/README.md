# GitHub Actions Workflows

## Pre-commit Workflow (`pre-commit.yml`)

Runs on all pull requests and pushes to main.

### Purpose

Enforces code quality standards using [pre-commit](https://pre-commit.com/) hooks.

### What It Checks

**File quality:**
- Trailing whitespace
- End-of-file fixes
- YAML/JSON/TOML syntax
- Large file detection
- Merge conflict markers

**Python code quality:**
- Black code formatting (88 char line length)
- mypy type checking (strict mode)
- Debug statement detection

**Commit messages:**
- Conventional Commits format validation
- Allowed types: feat, fix, docs, style, refactor, test, chore, perf, ci, build, revert

### When It Runs

- On all pull requests
- On push to main branch

### Output

Shows results for each hook:
```
trailing whitespace.............................Passed
fix end of files................................Passed
black...........................................Passed
mypy............................................Passed
conventional-pre-commit.........................Passed
```

### Local Testing

Pre-commit hooks run automatically on `git commit`:

```bash
# Install hooks (one-time setup)
pre-commit install
pre-commit install --hook-type commit-msg

# Hooks run automatically on commit
git commit -m "feat: add something"

# Run manually on all files
pre-commit run --all-files

# Run specific hook
pre-commit run black --all-files
```

---

## CI Workflow (`ci.yml`)

Runs on every push to `main` and on all pull requests.

### Workflow Structure

```
┌──────────┬───────────┐
│   test   │  security │  ← Run in parallel
└─────┬────┴─────┬─────┘
      └──────────┘
           ▼
      ci-success  ← Summary status check
```

Note: Code quality checks (formatting, type checking, conventional commits) are handled by the `pre-commit` workflow.

### Jobs

#### 1. test
- Runs pytest with coverage
- Python 3.13
- Requires 70% minimum coverage
- Uses in-memory SQLite for tests
- Uploads coverage.xml artifact
- **Run locally:** `pytest tests/ --cov=app --cov-report=term-missing --cov-fail-under=70`

#### 2. security
- Runs pip-audit for vulnerability scanning
- Checks all dependencies against OSV database
- Runs on Python 3.13
- **Run locally:** `pip-audit`

#### 3. coverage-comment
- Posts coverage report to PR as comment
- Only runs on pull requests
- Depends on `test` job
- Downloads coverage.xml from test job
- Updates existing comment on subsequent pushes
- Color coding: green >80%, orange 70-80%, red <70%

#### 4. ci-success
- Summary job that depends on all check jobs
- Fails if any required job fails
- Used for branch protection rules

### Caching Strategy

Pip dependencies are cached based on `pyproject.toml` hash:
- Key: `{os}-pip-{hash}`
- Speeds up dependency installation from ~30s to ~10-15s
- Automatically invalidates when `pyproject.toml` changes

### Concurrency & Performance

**Concurrency Control:**
- Automatically cancels in-progress runs when new commits are pushed to the same PR
- Saves CI minutes and provides faster feedback

**Parallel Execution:**
- `test` and `security` jobs run in parallel
- Total workflow time: ~30s (longest job + success)

**Job Dependencies:**
```
test (20s) ──┐
             ├─→ coverage-comment (5s, PR only) ──┐
security (10s)                                    ├─→ ci-success (1s)
                                                  ┘
```
Total: ~26s (test + coverage + success)

### Environment Variables

- `ENV=test`: Sets application to test mode
- `DATABASE_URL=sqlite:///:memory:`: Uses in-memory database for tests
- `PYTHON_VERSION=3.13`: Python version for all jobs

## Troubleshooting

### Pre-commit hooks fail
Run locally to see what failed:
```bash
pre-commit run --all-files
```

Fix issues automatically where possible:
```bash
# Black will auto-format files
# Just re-stage and commit
git add .
git commit -m "your message"
```

For mypy errors, fix the type issues manually.

### Tests fail
Run locally with verbose output:
```bash
pytest tests/ -v
```

Run specific test:
```bash
pytest tests/unit/services/test_job_service.py -v
```

### Coverage below threshold
Run locally to see uncovered lines:
```bash
pytest tests/ --cov=app --cov-report=term-missing
```

The report shows which lines are not covered by tests.

### Security audit fails
Run locally to see vulnerable packages:
```bash
pip-audit
```

Update vulnerable dependencies in `pyproject.toml` and reinstall:
```bash
pip install -e ".[dev]"
```

## Running All Checks Locally

Before pushing, run all checks:

```bash
# Run all pre-commit hooks
pre-commit run --all-files

# Run tests with coverage
pytest tests/ --cov=app --cov-report=term-missing --cov-fail-under=70 -v

# Security audit
pip-audit
```

Individual tools (if needed):
```bash
black app/ tests/      # Format code
mypy app/              # Type check
```

## Branch Protection

Recommended branch protection settings for `main`:

- Require status checks to pass before merging
- Required status checks:
  - `Run pre-commit hooks` (pre-commit.yml)
  - `Tests with coverage`
  - `Security audit`
  - `CI Success`
- Require branches to be up to date before merging

## Summary

The project has two GitHub Actions workflows:

| Workflow | Trigger | Purpose | Duration |
|----------|---------|---------|----------|
| `pre-commit.yml` | PRs + push to main | Code quality & commit validation | ~15s |
| `ci.yml` | PRs + push to main | Tests & security | ~26s |

**Total CI time:** ~30-40s (workflows run in parallel)

All checks must pass before code can be merged to `main`.
