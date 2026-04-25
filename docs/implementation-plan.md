# Data Intake Service: Learning-Focused Multi-Phase Plan

## Context

This project is a **learning-first FastAPI service** for dataset validation. The goal is to master production-grade backend engineering concepts through building a real system from scratch.

### Project Vision
Build a production-ready API service that:
- Accepts dataset validation requests via REST API
- Processes validation jobs asynchronously in background workers
- Fetches data from URLs and validates against schemas
- Tracks job state through a complete lifecycle
- Provides authentication, observability, and production-grade features

### Learning Goals (Prioritized)
1. **RESTful API design** (CRUD, state transitions, pagination, filtering, idempotency)
2. **TDD discipline** (strict red-green-refactor throughout)
3. **Clean architecture** (domain models, repository pattern, service layer)
4. **Background processing** (RQ or Celery - pick one)
5. **Async workflow & state machines** (implement full job lifecycle)
6. **DDD patterns** (pragmatic application)
7. **Authentication** (API keys, user attribution)
8. **Observability** (structured logging, metrics + dashboards)
9. **Performance** (caching strategies)
10. **API protection** (rate limiting)
11. **Production readiness** (deployment, health checks)

---

## 12-Phase Approach

**Pace**: Fast iterations (1-2 days per phase)
**Approach**: Sequential phases, each delivering working software
**Testing**: Strict TDD (red-green-refactor) + integration test patterns
**Timeline**: 20-25 days total

Each phase follows this template:
1. **Learning Goal**: What concept you're mastering
2. **Deliverables**: Concrete features to build
3. **Testing Strategy**: How to validate the work
4. **Success Criteria**: What "done" looks like

---

## Phase 1: Foundation (Project Setup & Basic API)

**Duration**: 1-2 days
**Learning Goal**: FastAPI basics, clean architecture setup, testing infrastructure

### Why This Phase
Establish the project foundation with proper structure, tooling, and initial API endpoints.

### Deliverables
1. **Project structure**:
   - Create clean architecture folders: `app/api`, `app/domains`, `app/services`, `app/repositories`, `app/db`, `app/schemas`
   - Set up `pyproject.toml` with dependencies (FastAPI, SQLAlchemy, Alembic, pytest, etc.)
   - Configure `pytest` with coverage enforcement (70% minimum)

2. **Database setup**:
   - PostgreSQL with Docker Compose
   - Alembic for migrations
   - Initial Job model (id, dataset_type, source_uri, status, created_at, updated_at)

3. **Domain model**:
   - Create `app/domains/job.py` - Job entity with basic state machine
   - States: QUEUED, RUNNING, SUCCEEDED, FAILED, RETRY_SCHEDULED, CANCELLED
   - Basic state transition validation

4. **Repository pattern**:
   - `app/repositories/job_repository.py` - Abstract interface
   - `app/repositories/sqlalchemy_job_repository.py` - SQLAlchemy implementation
   - `tests/fakes/fake_job_repository.py` - In-memory fake for testing

5. **Service layer**:
   - `app/services/job_service.py` - Business logic for job creation and retrieval
   - Dependency injection of repository

6. **Initial API endpoints**:
   - `POST /api/v1/jobs` - Create new validation job
   - `GET /api/v1/jobs` - List all jobs
   - `GET /api/v1/jobs/{job_id}` - Get specific job

7. **Infrastructure**:
   - `docker-compose.yml` with PostgreSQL service
   - `.env` configuration
   - GitHub Actions CI/CD (run tests, check coverage)

### Testing Strategy (TDD)
1. **Unit tests** (write tests FIRST):
   - Domain: Test Job creation and basic state transitions
   - Service: Test business logic with fake repository
   - Repository: Test SQLAlchemy operations against test database

2. **Integration tests**:
   - API: Test all three endpoints end-to-end
   - Database: Test migrations can run forward and rollback

### Success Criteria
- [ ] Project structure follows clean architecture
- [ ] All 3 basic endpoints implemented and tested
- [ ] Database migrations work
- [ ] CI pipeline runs successfully
- [ ] Test coverage ≥70%
- [ ] Can create and retrieve jobs via API

### Files Created
- `pyproject.toml`, `docker-compose.yml`, `.github/workflows/ci.yml`
- `app/domains/job.py`
- `app/db/models/job.py`
- `app/repositories/job_repository.py` (abstract + SQLAlchemy)
- `app/services/job_service.py`
- `app/api/v1/endpoints/jobs.py`
- `app/schemas/job.py`
- `alembic/versions/001_initial_job_table.py`
- `tests/unit/`, `tests/integration/`, `tests/fakes/`

---

## Phase 2: Structured Logging & Observability Foundation

**Duration**: 1 day
**Learning Goal**: Structured logging, request context, observability patterns

### Why This Phase
Before building complex features, establish logging patterns that will be essential for debugging async workflows later.

### Deliverables
1. **JSON structured logging**:
   - Configure `structlog` for JSON output
   - Log format: timestamp, level, message, context fields
   - Environment-based configuration (pretty for local, JSON for production)

2. **Request context**:
   - Middleware to generate request_id for each API request
   - Add request_id to all logs within that request
   - Include in API responses as header `X-Request-ID`

3. **Job context**:
   - Add job_id to logging context when processing jobs
   - Log key events: job created, state transitions

4. **Log filtering**:
   - Configure log levels by module
   - Suppress noisy third-party logs (uvicorn access logs)

### Testing Strategy (TDD)
1. **Integration tests**:
   - Assert request_id appears in logs
   - Assert log format is valid JSON
   - Test log context propagation

### Success Criteria
- [ ] All logs output as JSON (except local development)
- [ ] Each API request has unique request_id
- [ ] Logs include relevant context (request_id, job_id)
- [ ] Logging tested in integration tests

### Files Created/Modified
- `app/core/logging.py` - Logging configuration
- `app/middleware/logging_middleware.py` - Request context middleware
- `app/main.py` - Apply middleware
- `tests/integration/test_logging.py`

---

## Phase 3: Complete the Job Lifecycle (API State Transitions)

**Duration**: 1-2 days
**Learning Goal**: RESTful design for state changes, idempotency patterns

### Why This Phase
Jobs can be created but never transition states. You need to manually control state for testing and prepare for worker automation.

### Deliverables
1. **New endpoints** (admin-only operational tools - auth added in Phase 5):
   - `PATCH /api/v1/jobs/{job_id}/start` - Transition QUEUED → RUNNING
   - `PATCH /api/v1/jobs/{job_id}/complete` - Transition RUNNING → SUCCEEDED (with optional validation result payload)
   - `PATCH /api/v1/jobs/{job_id}/fail` - Transition RUNNING → FAILED (with error details)
   - `POST /api/v1/jobs/{job_id}/retry` - Transition FAILED → RETRY_SCHEDULED → QUEUED
   - `DELETE /api/v1/jobs/{job_id}` - Transition any state → CANCELLED

   **Note**: These are operational/debugging tools for admins (manual intervention, incident response). Build without auth in this phase (needed for testing), restrict to admin role in Phase 7. Regular users only access: POST /jobs (create), GET /jobs (list), GET /jobs/{id} (view).

2. **Domain enhancements**:
   - Add `error_code` and `error_message` fields to Job domain model
   - Add `retry_count` field (track retry attempts)
   - Add `started_at` and `finished_at` timestamps
   - Enforce state machine rules in `Job.transition_to()`

3. **Service layer**:
   - `JobService.start_job(job_id)` → validates QUEUED, transitions to RUNNING
   - `JobService.complete_job(job_id, results)` → validates RUNNING, transitions to SUCCEEDED
   - `JobService.fail_job(job_id, error)` → transitions to FAILED, records error
   - `JobService.retry_job(job_id)` → validates FAILED, increments retry_count, transitions to RETRY_SCHEDULED then QUEUED
   - `JobService.cancel_job(job_id)` → transitions to CANCELLED

4. **Idempotency**:
   - Add `idempotency_key` field to Job (nullable for now)
   - In `JobService.create_job()`, check if job with same key exists
   - If exists and terminal state (SUCCEEDED/FAILED/CANCELLED), reject with 409 Conflict
   - If exists and non-terminal state, return existing job (idempotent create)

5. **Database migration**:
   - Alembic migration adding new columns: `error_code`, `error_message`, `retry_count`, `started_at`, `finished_at`, `idempotency_key`

### Testing Strategy (TDD)
1. **Unit tests** (write tests FIRST):
   - Domain: Test all state transitions (valid + invalid)
   - Service: Test each service method with mocked repository
   - Test idempotency logic in service

2. **Integration tests**:
   - API: Test each endpoint's happy path + error cases
   - Test full lifecycle: create → start → complete
   - Test retry flow: create → start → fail → retry → start → complete
   - Test idempotency: duplicate POST with same key returns same job

3. **Contract tests** (NEW):
   - Define expected request/response schemas for each endpoint
   - Validate using Pydantic schemas as contracts

### Success Criteria
- [ ] All 5 new endpoints implemented and tested
- [ ] State machine enforces valid transitions, rejects invalid ones
- [ ] Idempotency prevents duplicate job creation
- [ ] Full test coverage (unit + integration) for new code
- [ ] Manual testing: use curl/httpie to walk through full job lifecycle

### Files Modified
- `app/domains/job.py` - Add fields, enhance transition logic
- `app/db/models/job.py` - Add columns
- `app/schemas/job.py` - Add request/response schemas for new endpoints
- `app/services/job_service.py` - Add 5 new service methods
- `app/api/v1/endpoints/jobs.py` - Add 5 new route handlers
- `alembic/versions/` - New migration
- `tests/unit/domains/test_job.py` - State transition tests
- `tests/unit/services/test_job_service.py` - Service logic tests
- `tests/integration/api/test_jobs_routes.py` - API endpoint tests

---

## Phase 4: Background Workers (Choose: RQ or Celery)

**Duration**: 1-2 days
**Learning Goal**: Async job processing fundamentals, message queue patterns

### Why This Phase
Jobs are manually transitioned. Now automate execution with background workers to learn async patterns.

### Framework Choice
**Option A: RQ (Recommended for first project)**
- Simpler, fewer concepts, easier to debug
- Good for learning async fundamentals
- Faster to get working

**Option B: Celery**
- More features (scheduling, canvas, monitoring)
- Industry standard
- Better if you want production-grade from start

**Pick one** - don't implement both (that's a separate learning exercise for later projects).

### Deliverables (Using RQ - adjust if using Celery)

1. **Infrastructure**:
   - Add Redis to `docker-compose.yml`
   - Install RQ: `pip install rq`
   - Create `app/workers/job_worker.py` - RQ worker process

2. **Job execution**:
   - Create `app/workers/tasks.py`:
     - `execute_validation_job(job_id)` - Main task
     - Fetches job from DB
     - Calls `JobService.start_job()`
     - Performs mock validation (just sleep for now)
     - Calls `JobService.complete_job()` or `JobService.fail_job()`

3. **Queue integration**:
   - Modify `JobService.create_job()` to enqueue job after persistence:
     ```python
     job = self._repo.create(domain_job)
     enqueue_validation_job(job.id)  # NEW
     return job
     ```
   - Create `app/workers/queue.py` - RQ queue initialization

4. **Worker management**:
   - Add worker service to `docker-compose.yml`:
     ```yaml
     worker:
       build: .
       command: rq worker --with-scheduler
       depends_on: [redis, db]
     ```
   - Document how to run worker locally

5. **Observability**:
   - Add job_id to logging context in worker
   - Log task start/completion/failure
   - Workers use same JSON logging as API

### Testing Strategy (TDD)
1. **Unit tests**:
   - Test `execute_validation_job()` task logic (mock DB/service calls)
   - Test queue enqueuing logic

2. **Integration tests**:
   - Create job via API, wait for worker to process it
   - Assert job transitions QUEUED → RUNNING → SUCCEEDED
   - Test worker failure handling (job transitions to FAILED)

3. **Manual testing**:
   - Start redis, db, worker, api
   - POST /jobs, watch logs for worker execution
   - Verify job status changes

### Success Criteria
- [ ] Redis + RQ/Celery integrated into Docker Compose
- [ ] Worker process can pick up jobs from queue
- [ ] Jobs automatically transition through states
- [ ] Worker failures are caught and job transitions to FAILED
- [ ] Logs show job execution in worker context
- [ ] Tests prove end-to-end async workflow

### Files Created/Modified
- `docker-compose.yml` - Add redis + worker services
- `app/workers/queue.py` - Queue setup
- `app/workers/tasks.py` - Task definitions
- `app/workers/job_worker.py` - Worker entry point
- `app/services/job_service.py` - Add enqueue call
- `tests/integration/workers/test_job_worker.py` - Worker integration tests
- `pyproject.toml` - Add rq or celery dependency

---

## Phase 5: Data Fetching and Schema Validation

**Duration**: 1-2 days
**Learning Goal**: External HTTP clients, schema-driven validation, file handling

### Why This Phase
Workers execute but don't validate data. Add the core business logic: fetch data from URL and validate against schemas.

### Deliverables
1. **Schema registry**:
   - Create `app/domains/schema.py` - Schema domain model
   - Create `app/db/models/schema.py` - Schema ORM model
   - Create `app/repositories/schema_repository.py` - Schema persistence
   - Add schemas table migration (dataset_type, version, definition_json, is_active, created_at)
   - Seed database with example schema (student_enrollment v1)

2. **HTTP client** (NEW):
   - Create `app/clients/http_client.py` - httpx-based data fetcher
   - `fetch_data_from_url(url) -> bytes` - Download file with timeout/retry
   - Configure timeouts, max file size, retries
   - Log download metrics (size, duration)

3. **Validation engine** (NEW):
   - Create `app/services/validation_service.py`:
     - `validate_dataset(data_bytes, schema) -> ValidationResult`
     - Parse CSV (pandas or csv module)
     - Check required columns exist
     - Check data types match schema
     - Check row count > 0
     - Record validation errors per row
   - Create `app/domains/validation_result.py` - ValidationResult domain model
   - Create `app/db/models/validation_result.py` - ValidationResult ORM model

4. **Worker enhancement**:
   - Update `execute_validation_job()`:
     - Fetch schema from registry
     - Call `http_client.fetch_data_from_url(job.source_uri)`
     - Call `validation_service.validate_dataset(data, schema)`
     - Persist ValidationResult to DB
     - Complete job with summary

5. **API endpoints**:
   - `GET /api/v1/jobs/{job_id}/results` - Retrieve validation results
   - `GET /api/v1/schemas` - List available schemas
   - `GET /api/v1/schemas/{dataset_type}/{version}` - Get specific schema

### Testing Strategy (TDD)
1. **Unit tests**:
   - HTTP client: Mock httpx responses, test timeout/retry logic
   - Validation service: Test with valid/invalid CSV data
   - Schema repository: Test CRUD operations

2. **Integration tests**:
   - End-to-end: Create job with URL, worker fetches + validates, results retrievable
   - Test with valid data → job succeeds, results show 0 errors
   - Test with invalid data → job succeeds, results show validation errors
   - Test with unreachable URL → job fails with network error

3. **Contract tests**:
   - Validate schema definition JSON format
   - Validate validation result response format

### Success Criteria
- [ ] Schema registry seeded with example schema
- [ ] Worker fetches data from URL (test with local HTTP server or mock)
- [ ] Validation logic identifies column/type mismatches
- [ ] Validation results persisted and retrievable via API
- [ ] Failed downloads transition job to FAILED with error details
- [ ] All tested via TDD (unit + integration)

### Files Created/Modified
- `app/domains/schema.py`, `app/domains/validation_result.py` - New domain models
- `app/db/models/schema.py`, `app/db/models/validation_result.py` - New ORM models
- `app/repositories/schema_repository.py` - New repository
- `app/clients/http_client.py` - New HTTP client
- `app/services/validation_service.py` - New validation service
- `app/workers/tasks.py` - Update to use real validation
- `app/api/v1/endpoints/jobs.py` - Add /results endpoint
- `app/api/v1/endpoints/schemas.py` - New schema endpoints
- `alembic/versions/` - Migrations for schemas + validation_results tables
- `tests/` - New test files for each component

---

## Phase 6: Retry Logic and Error Handling

**Duration**: 1-2 days
**Learning Goal**: Exponential backoff, retry strategies, transient vs permanent failures

### Why This Phase
Workers fail but retry is manual. Automate retries with exponential backoff for resilience.

### Deliverables
1. **Retry configuration**:
   - Add to `app/core/config.py`:
     - `MAX_RETRY_ATTEMPTS = 3`
     - `RETRY_BACKOFF_BASE = 2` (seconds)
     - `RETRY_BACKOFF_MAX = 60`

2. **Queue retry integration**:
   - **If using RQ**: Configure task with retry parameters:
     ```python
     @job('default', retry=Retry(max=3, interval=[2, 4, 8]))
     def execute_validation_job(job_id):
         ...
     ```
   - **If using Celery**: Configure task with:
     ```python
     @app.task(autoretry_for=(RetryableError,), retry_kwargs={'max_retries': 3}, retry_backoff=True)
     def execute_validation_job(job_id):
         ...
     ```

3. **Failure classification**:
   - Create `app/exceptions.py`:
     - `RetryableError` - Transient failures (network timeout, 503)
     - `PermanentError` - Non-retryable (404, invalid schema, malformed data)
   - Update worker to raise appropriate exceptions
   - Permanent errors → mark FAILED, don't retry
   - Retryable errors → let queue retry

4. **Service enhancements**:
   - `JobService.fail_job()` - Accept `is_retryable` flag
   - If retryable and retry_count < MAX_RETRY_ATTEMPTS:
     - Transition to RETRY_SCHEDULED
     - Queue schedules next attempt
   - If not retryable or max retries exceeded:
     - Transition to FAILED (terminal)

5. **Dead letter queue**:
   - Configure failed queue in RQ/Celery
   - Add monitoring script: `scripts/inspect_failed_jobs.py`
   - Document how to requeue failed jobs manually

### Testing Strategy (TDD)
1. **Unit tests**:
   - Test failure classification logic
   - Test retry count increment
   - Test max retry enforcement

2. **Integration tests**:
   - Simulate transient failure → verify retry scheduled
   - Simulate permanent failure → verify job marked FAILED immediately
   - Simulate 3 transient failures → verify job marked FAILED after max retries
   - Verify exponential backoff delays (check queue inspection)

### Success Criteria
- [ ] Transient failures automatically retry with backoff
- [ ] Permanent failures immediately marked FAILED
- [ ] Max retry limit enforced
- [ ] Failed jobs inspectable via queue tools
- [ ] Retry logic fully tested

### Files Created/Modified
- `app/core/config.py` - Add retry configuration
- `app/exceptions.py` - New exception classes
- `app/workers/tasks.py` - Add retry decorator + failure classification
- `app/services/job_service.py` - Enhance fail_job logic
- `scripts/inspect_failed_jobs.py` - Dead letter queue inspector
- `tests/integration/workers/test_retry_logic.py` - Retry integration tests

---

## Phase 7: Authentication (API Keys)

**Duration**: 1-2 days
**Learning Goal**: API authentication, security patterns, user context

### Why This Phase
API is currently open. Add API key auth to control access and attribute jobs to users.

### Deliverables
1. **User model with admin role**:
   - Create `app/domains/user.py` - User domain model
   - Create `app/db/models/user.py` - User ORM model
   - Add users table migration (id, email, api_key_hash, is_active, is_admin, created_at)
   - Add `submitted_by` foreign key to jobs table

2. **API key generation**:
   - Create `scripts/create_api_key.py`:
     - Generates random API key (secrets.token_urlsafe)
     - Hashes key with bcrypt
     - Stores user + hash in DB
     - Accepts `--admin` flag to create admin users
     - Prints key (only time it's visible)

3. **Authentication dependencies**:
   - Create `app/api/auth.py`:
     - `get_current_user(api_key: str = Header(..., alias="X-API-Key"))` → User
       - Looks up user by hashed key
       - Raises 401 if invalid/missing
       - Raises 403 if user inactive
     - `admin_required(current_user: User = Depends(get_current_user))` → User
       - Raises 403 if user.is_admin is False

4. **Endpoint protection**:
   - **Regular user endpoints** (require `Depends(get_current_user)`):
     - `POST /api/v1/jobs` - Store `submitted_by = current_user.id`
     - `GET /api/v1/jobs` - Filter to only return current user's jobs
     - `GET /api/v1/jobs/{id}` - Ensure user can only view their own jobs

   - **Admin-only endpoints** (require `Depends(admin_required)`):
     - `PATCH /api/v1/jobs/{job_id}/start`
     - `PATCH /api/v1/jobs/{job_id}/complete`
     - `PATCH /api/v1/jobs/{job_id}/fail`
     - `POST /api/v1/jobs/{job_id}/retry`
     - `DELETE /api/v1/jobs/{job_id}`

5. **Testing with auth**:
   - Update test fixtures to generate test API keys (regular + admin)
   - Update integration tests to pass X-API-Key header

### Testing Strategy (TDD)
1. **Unit tests**:
   - Test API key hashing/verification
   - Test user lookup logic
   - Test admin_required dependency logic

2. **Integration tests**:
   - Test endpoints without API key → 401
   - Test endpoints with invalid key → 401
   - Test regular user endpoints with valid key → 200
   - Test admin endpoints with regular user key → 403
   - Test admin endpoints with admin key → 200
   - Test user can only see their own jobs
   - Test job creation attributes to correct user

### Success Criteria
- [ ] API key generation script works (with --admin flag)
- [ ] All endpoints require valid API key
- [ ] Admin endpoints reject regular users (403)
- [ ] Admin endpoints allow admin users (200)
- [ ] Jobs attributed to creating user
- [ ] Users isolated (can't see others' jobs)
- [ ] Auth + authorization tested via integration tests

### Files Created/Modified
- `app/domains/user.py`, `app/db/models/user.py` - User model
- `app/repositories/user_repository.py` - User persistence
- `app/api/auth.py` - Auth dependencies
- `app/api/v1/endpoints/jobs.py` - Add auth to endpoints
- `scripts/create_api_key.py` - Key generation script
- `alembic/versions/` - Migrations for users table + jobs.submitted_by FK
- `tests/conftest.py` - Add API key fixtures
- `tests/integration/api/test_auth.py` - Auth tests

---

## Phase 8: Pagination and Filtering

**Duration**: 1-2 days
**Learning Goal**: RESTful pagination patterns, query optimization

### Why This Phase
`GET /jobs` returns all jobs. Learn to handle large result sets efficiently.

### Deliverables
1. **Pagination schemas**:
   - Create `app/schemas/common.py`:
     - `PaginationParams(page: int = 1, page_size: int = 20, max=100)`
     - `PaginatedResponse[T]` - Generic wrapper with data, page, total_pages, total_items, has_next, has_prev

2. **Repository enhancement**:
   - Add `AbstractJobRepository.list_with_pagination(filters, page, page_size)` → tuple[list[Job], int]
   - Implement in `SqlAlchemyJobRepository`:
     - Use SQLAlchemy `.limit()` and `.offset()`
     - Return jobs + total count (for page metadata)

3. **Filtering**:
   - Add query parameters to `GET /api/v1/jobs`:
     - `status` - Filter by JobStatus (comma-separated for multiple)
     - `dataset_type` - Filter by dataset type
     - `created_after`, `created_before` - Date range filters
   - Implement in repository as dynamic WHERE clauses

4. **Sorting**:
   - Add `sort_by` query param: `created_at`, `status`, `dataset_type`
   - Add `sort_order`: `asc` or `desc`
   - Implement in repository with ORDER BY

5. **Response format**:
   - Update `GET /api/v1/jobs` response:
     ```json
     {
       "data": [...],
       "pagination": {
         "page": 1,
         "page_size": 20,
         "total_pages": 5,
         "total_items": 94,
         "has_next": true,
         "has_prev": false
       }
     }
     ```

### Testing Strategy (TDD)
1. **Unit tests**:
   - Test pagination logic (page bounds, total calculation)
   - Test filter parsing

2. **Integration tests**:
   - Create 50 jobs, paginate through them
   - Test page boundaries (first, middle, last page)
   - Test filtering combinations
   - Test sorting
   - Test invalid page/page_size → 400

### Success Criteria
- [ ] Pagination works correctly for large datasets
- [ ] Filtering by status, type, date range works
- [ ] Sorting works
- [ ] Response includes pagination metadata
- [ ] Query performance acceptable (tested with 100+ jobs)

### Files Created/Modified
- `app/schemas/common.py` - Pagination schemas
- `app/repositories/job_repository.py` - Add pagination/filtering methods
- `app/services/job_service.py` - Add service method with filters
- `app/api/v1/endpoints/jobs.py` - Update GET /jobs with query params
- `tests/integration/api/test_pagination.py` - Pagination tests

---

## Phase 9: Metrics (Prometheus + Grafana)

**Duration**: 1-2 days
**Learning Goal**: Application metrics, Prometheus instrumentation, Grafana dashboards

### Why This Phase
No visibility into system performance. Add metrics to measure health and behavior.

### Deliverables
1. **Prometheus client**:
   - Install: `pip install prometheus-client`
   - Create `app/observability/metrics.py`:
     - `http_requests_total` (Counter) - Track API requests by endpoint, method, status
     - `http_request_duration_seconds` (Histogram) - Track request latency
     - `job_transitions_total` (Counter) - Track state transitions by from_state, to_state
     - `jobs_by_status` (Gauge) - Track count of jobs in each status
     - `validation_duration_seconds` (Histogram) - Track validation time
     - `data_download_duration_seconds` (Histogram) - Track download time
     - `data_download_bytes` (Histogram) - Track file sizes

2. **Instrumentation**:
   - API middleware: Wrap requests to record http_* metrics
   - Job service: Record job_transitions_total on state change
   - Validation service: Record validation_duration_seconds
   - HTTP client: Record download metrics

3. **Metrics endpoint**:
   - Add `GET /metrics` endpoint (unauthenticated, Prometheus scrapes it)
   - Returns Prometheus text format

4. **Prometheus + Grafana**:
   - Add to `docker-compose.yml`:
     - Prometheus service (scrapes /metrics every 15s)
     - Grafana service (visualizes metrics)
   - Create `prometheus.yml` config
   - Create Grafana dashboard JSON:
     - Request rate and latency
     - Job status distribution
     - Validation duration over time
     - Error rate

### Testing Strategy (TDD)
1. **Unit tests**:
   - Test metrics are incremented correctly
   - Test histogram buckets

2. **Integration tests**:
   - Make API calls, assert metrics incremented
   - Create/transition jobs, assert job metrics updated

3. **Manual testing**:
   - Run service, scrape /metrics, verify format
   - Open Grafana, view dashboard
   - Generate load, watch metrics update

### Success Criteria
- [ ] Prometheus scrapes /metrics endpoint successfully
- [ ] Grafana dashboard shows key metrics
- [ ] Metrics accurately reflect system behavior
- [ ] All instrumentation tested

### Files Created/Modified
- `app/observability/metrics.py` - Metric definitions
- `app/middleware/metrics.py` - Metrics middleware
- `app/services/job_service.py` - Add metric recording
- `app/services/validation_service.py` - Add metric recording
- `app/clients/http_client.py` - Add metric recording
- `app/api/v1/endpoints/metrics.py` - Metrics endpoint
- `docker-compose.yml` - Add prometheus + grafana services
- `prometheus.yml` - Prometheus config
- `grafana/dashboards/` - Dashboard definitions
- `tests/integration/observability/test_metrics.py` - Metrics tests

---

## Phase 10: Caching (Redis)

**Duration**: 1-2 days
**Learning Goal**: Caching strategies, cache invalidation, performance optimization

### Why This Phase
Schema lookups and job queries hit DB every time. Add caching to improve performance.

### Deliverables
1. **Cache abstraction**:
   - Create `app/caching/cache.py`:
     - `Cache` interface: `get(key)`, `set(key, value, ttl)`, `delete(key)`, `clear()`
     - `RedisCache` implementation (using redis-py)
     - `InMemoryCache` implementation (for testing)

2. **Schema caching**:
   - Wrap `SchemaRepository.get_by_type_and_version()`:
     - Check cache first
     - If miss, fetch from DB, cache for 1 hour
     - Cache key: `schema:{dataset_type}:{version}`
   - Invalidate on schema update/deactivation

3. **Job caching**:
   - Cache individual jobs after retrieval:
     - Cache key: `job:{job_id}`
     - TTL: 5 minutes
   - Invalidate on job state transition

4. **Cache metrics**:
   - Add metrics to `app/observability/metrics.py`:
     - `cache_hits_total`, `cache_misses_total` by cache_name
     - `cache_operation_duration_seconds` by operation (get, set, delete)

### Testing Strategy (TDD)
1. **Unit tests**:
   - Test cache interface implementations
   - Test cache hit/miss logic
   - Test TTL expiration

2. **Integration tests**:
   - Fetch schema twice, assert DB queried once (cache hit)
   - Update schema, assert cache invalidated
   - Measure latency improvement with cache enabled vs disabled

### Success Criteria
- [ ] Schema lookups served from cache (reduces DB load)
- [ ] Job queries faster with caching
- [ ] Cache invalidation works correctly
- [ ] Cache metrics show hit rate
- [ ] Performance improvement measurable

### Files Created/Modified
- `app/caching/cache.py` - Cache interface + implementations
- `app/repositories/schema_repository.py` - Add caching layer
- `app/repositories/job_repository.py` - Add caching layer
- `app/observability/metrics.py` - Add cache metrics
- `tests/unit/caching/test_cache.py` - Cache unit tests
- `tests/integration/caching/test_cache_integration.py` - Cache integration tests

---

## Phase 11: Rate Limiting

**Duration**: 1-2 days
**Learning Goal**: Rate limiting strategies, abuse prevention, fairness

### Why This Phase
API has no rate limits. Users can overload system. Learn to protect resources.

### Deliverables
1. **Rate limiting library**:
   - Install: `pip install slowapi`
   - Create `app/middleware/rate_limit.py`:
     - Configure rate limiter with Redis backend
     - Default limits: 100 requests/minute per user (by API key)

2. **Endpoint-specific limits**:
   - `POST /api/v1/jobs` - 20 requests/minute (expensive)
   - `GET /api/v1/jobs` - 100 requests/minute
   - `GET /api/v1/jobs/{id}` - 200 requests/minute (cheap)
   - `GET /api/v1/schemas` - No limit (public, cached)

3. **Rate limit headers**:
   - Add headers to all responses:
     - `X-RateLimit-Limit: 100`
     - `X-RateLimit-Remaining: 87`
     - `X-RateLimit-Reset: 1640000000` (Unix timestamp)

4. **429 response**:
   - Return 429 Too Many Requests when limit exceeded
   - Include `Retry-After` header (seconds until reset)
   - Response body:
     ```json
     {
       "error": "rate_limit_exceeded",
       "message": "Rate limit of 20 requests/minute exceeded",
       "retry_after": 42
     }
     ```

5. **Monitoring**:
   - Add metrics:
     - `rate_limit_hits_total` by endpoint, user
     - `rate_limit_exceeded_total` by endpoint

### Testing Strategy (TDD)
1. **Unit tests**:
   - Test rate limit calculation
   - Test limit exceeded logic

2. **Integration tests**:
   - Make 101 requests in 1 minute → assert 100 succeed, 1 gets 429
   - Assert rate limit headers correct

### Success Criteria
- [ ] Rate limits enforced per user per endpoint
- [ ] 429 responses include correct headers
- [ ] Rate limit metrics tracked
- [ ] Rate limiting tested thoroughly

### Files Created/Modified
- `app/middleware/rate_limit.py` - Rate limiter setup
- `app/main.py` - Add rate limit middleware
- `app/api/v1/endpoints/jobs.py` - Apply rate limits to endpoints
- `app/observability/metrics.py` - Add rate limit metrics
- `tests/integration/api/test_rate_limiting.py` - Rate limit tests

---

## Phase 12: Production Readiness

**Duration**: 1-2 days
**Learning Goal**: Production deployment patterns, health checks, graceful shutdown

### Why This Phase
System runs locally but not production-ready. Prepare for real deployment.

### Deliverables
1. **Production Dockerfile**:
   - Multi-stage build:
     - Stage 1: Build dependencies
     - Stage 2: Runtime (slim image)
   - Non-root user
   - Health check command
   - Security: No secrets in image

2. **Health check endpoints**:
   - `GET /health` - Liveness probe (returns 200 if app running)
   - `GET /ready` - Readiness probe (checks DB + Redis connectivity)
   - Used by orchestrators (Docker Compose, Kubernetes)

3. **Environment separation**:
   - Create `.env.local`, `.env.staging`, `.env.production`
   - Document differences (log level, DB, timeouts)
   - Production: INFO logging, PostgreSQL, longer timeouts

4. **Migrations in production**:
   - Document migration strategy:
     - Run migrations before deploying new code
     - Use Alembic's `alembic upgrade head`
   - Add migration health check (assert DB schema version matches code)

5. **Graceful shutdown**:
   - Handle SIGTERM in API + worker:
     - API: Stop accepting new requests, finish in-flight requests
     - Worker: Finish current task, don't pick up new tasks
   - Set shutdown timeout (30 seconds)

6. **Production checklist**:
   - Create `docs/production_checklist.md`:
     - [ ] Environment variables configured
     - [ ] Database migrations run
     - [ ] Redis accessible
     - [ ] Workers running
     - [ ] Health checks passing
     - [ ] Monitoring configured
     - [ ] Secrets rotated
     - [ ] TLS enabled (if applicable)

### Testing Strategy
1. **Integration tests**:
   - Test health/ready endpoints
   - Test graceful shutdown (send SIGTERM, assert tasks complete)

2. **Manual testing**:
   - Build production Docker image
   - Run with production config
   - Test deployment simulation (stop old, start new)

### Success Criteria
- [ ] Production Docker image builds successfully
- [ ] Health checks work correctly
- [ ] Graceful shutdown tested
- [ ] Production checklist complete
- [ ] Deployment documented

### Files Created/Modified
- `Dockerfile` - Update for production (multi-stage)
- `app/api/v1/endpoints/health.py` - Health/ready endpoints
- `app/main.py` - Add graceful shutdown handlers
- `docker-compose.prod.yml` - Production compose file
- `.env.production` - Production config template
- `docs/production_checklist.md` - Deployment checklist
- `docs/deployment.md` - Deployment guide

---

## Phase Progression Summary

```
Phase 1: Foundation (project setup, basic CRUD API, clean architecture)
  ↓
Phase 2: Structured Logging (JSON logging, request context)
  ↓
Phase 3: Job Lifecycle API (state transitions, idempotency)
  ↓
Phase 4: Background Workers (RQ or Celery - pick one)
  ↓
Phase 5: Data Validation (schema registry, HTTP client, validation engine)
  ↓
Phase 6: Retry Logic (exponential backoff, failure classification)
  ↓
Phase 7: Authentication (API keys, user attribution)
  ↓
Phase 8: Pagination & Filtering (query optimization, REST patterns)
  ↓
Phase 9: Metrics (Prometheus, Grafana dashboards)
  ↓
Phase 10: Caching (Redis, cache invalidation, performance)
  ↓
Phase 11: Rate Limiting (abuse prevention, fairness)
  ↓
Phase 12: Production Readiness (deployment, health checks, graceful shutdown)
```

---

## What Was Excluded (Save for Future Projects)

These are valuable but not essential for a first project:

### Authorization (RBAC)
**Why excluded**: Basic auth (Phase 7) is enough. RBAC adds complexity without much learning value in a single-user context. Better learned in a team-oriented or multi-tenant project.

**When to learn**: Project 2 or 3, when you build something with real role hierarchies.

### Distributed Tracing (OpenTelemetry)
**Why excluded**: Tracing shines in multi-service architectures. This is a single service. Logs + metrics are sufficient.

**When to learn**: When you build microservices or a service mesh.

### Alerting & SLOs
**Why excluded**: SLOs make sense with real users and uptime requirements. Metrics (Phase 9) give you the foundation - alerts are just queries on metrics.

**When to learn**: When you operate a service in production with real users.

### Load Testing & Optimization
**Why excluded**: Can add load testing in 2-3 hours when needed. Not a core learning goal for "first FastAPI project." Caching (Phase 10) teaches optimization without needing a dedicated phase.

**When to learn**: Dedicated "performance week" across all your projects, or when you have real performance requirements.

### Celery Migration (if you start with Celery)
**Why excluded**: Framework comparison is educational but time-consuming. Pick RQ or Celery in Phase 4, use the other in your next project, compare naturally.

**When to learn**: Across multiple projects, not within one.

### Advanced Features
**Excluded**: Webhooks, file uploads, S3 storage, GraphQL, multi-tenancy, event sourcing, Kubernetes, admin UI.

**Why**: These are all great learning topics, but they're either too specific (webhooks, S3) or too ambitious (K8s, event sourcing) for a first project. Better as dedicated projects or enhancements after you've shipped this one.

---

## Testing Strategy Summary

Across all phases, maintain these testing practices:

### TDD Discipline
1. **Write test first** (RED)
2. **Watch it fail** (verify it tests the right thing)
3. **Write minimal code** (GREEN)
4. **Refactor** (keep tests green)

### Test Pyramid
- **Unit tests** (70%): Fast, isolated, test business logic
- **Integration tests** (25%): Test layer interactions, DB, external APIs
- **E2E tests** (5%): Test full user workflows

### Continuous Testing
- Pre-commit hooks: Run fast tests before commit
- CI: Run full suite on every PR
- Manual: Test each feature end-to-end before moving to next phase

---

## Success Metrics

By the end of this 10-phase plan, you will have:

### Technical Skills Mastered
- ✅ RESTful API design (CRUD, pagination, filtering, idempotency)
- ✅ TDD discipline (100+ hours of practice)
- ✅ Background job processing (RQ or Celery)
- ✅ Async workflows & state machines
- ✅ DDD patterns (pragmatic application)
- ✅ Authentication (API keys)
- ✅ Observability (logs + metrics)
- ✅ Performance optimization (caching)
- ✅ API protection (rate limiting)
- ✅ Production deployment

### Artifacts Produced
- Production-ready API service with authentication
- Background worker system with retry logic
- Comprehensive test suite (>80% coverage)
- Observability stack (Prometheus + Grafana)
- Complete documentation
- Production deployment setup

### Real-World Experience
- Built from scratch to production-ready
- Made architecture decisions (framework choices, caching strategies)
- Debugged distributed systems issues
- Designed for observability
- Prepared for production deployment

---

## Estimated Timeline

- **12 core phases**: 20-25 days at 1-2 days per phase
- **Total**: 4-5 weeks (working 1-2 hours/day)

This timeline assumes:
- 1-2 hours/day coding
- Strict TDD (may slow initial progress but compounds speed later)
- Learning as you go (reading docs, debugging)

---

## After Completion

Once you've completed these 12 phases, you'll have a **production-ready service** and can:

1. **Deploy it**: Put it on a VPS, AWS, or cloud platform
2. **Open source it**: Polish README, add CONTRIBUTING.md, publish
3. **Portfolio piece**: Showcase in interviews
4. **Build on it**: Add stretch features (webhooks, S3, etc.)
5. **Next project**: Apply lessons to a new system (microservices, GraphQL API, etc.)

---

## Resources

- **FastAPI**: fastapi.tiangolo.com
- **SQLAlchemy**: docs.sqlalchemy.org/en/20/
- **RQ**: python-rq.org
- **Celery**: docs.celeryq.dev
- **Prometheus**: prometheus.io/docs/
- **DDD**: Domain-Driven Design by Eric Evans (book)

---

**Ready to start with Phase 1?**
