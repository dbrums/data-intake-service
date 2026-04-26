# Project: Data Intake and Validation Service

A FastAPI service that accepts dataset uploads or pull requests, validates them against declared schemas and business rules, stores results, and exposes job status and validation reports through an API.

This is a strong first FastAPI project because it is not just CRUD. It naturally forces you to build the things that matter for a senior data engineer: API boundaries, schema validation, async job processing, idempotency, retries, observability, stateful workflows, API client behavior, packaging, and deployment. It also aligns closely with the concepts in your attached document.

## What the product does

A user or internal system can:

* submit a validation job
* either upload a file or provide a URL to pull from
* specify a dataset type and schema version
* poll job status
* retrieve validation results
* view historical jobs
* retry failed jobs safely
* list datasets, schemas, and validation rules
* optionally approve a validated dataset for downstream consumption

The core idea is simple:

1. request enters the API
2. request is validated and normalized
3. a background worker processes the job
4. job transitions through states
5. results, logs, and metrics are recorded
6. the API exposes status and artifacts

That gives you both synchronous and asynchronous system design in one project.

---

## What Gets Built (Full Feature Set)

By the end of the 12-phase plan, you'll have a production-ready service with:

### Core Capabilities

* Submit validation jobs with idempotency support
* Background job processing with automatic state transitions
* Data fetching from URLs
* Schema-driven validation (CSV initially)
* Validation result reporting with detailed error messages
* Automatic retry logic with exponential backoff
* API key authentication with admin roles
* User-isolated job listings

### API Endpoints

**Job Management:**
* `POST /api/v1/jobs` - Create validation job (with idempotency)
* `GET /api/v1/jobs` - List jobs (paginated, filtered, sorted)
* `GET /api/v1/jobs/{job_id}` - Get job details
* `GET /api/v1/jobs/{job_id}/results` - Get validation results

**Admin Operations:**
* `PATCH /api/v1/jobs/{job_id}/start` - Manually start job
* `PATCH /api/v1/jobs/{job_id}/complete` - Mark complete
* `PATCH /api/v1/jobs/{job_id}/fail` - Mark failed
* `POST /api/v1/jobs/{job_id}/retry` - Retry failed job
* `DELETE /api/v1/jobs/{job_id}` - Cancel job

**Schema Registry:**
* `GET /api/v1/schemas` - List available schemas
* `GET /api/v1/schemas/{dataset_type}/{version}` - Get schema definition

**System:**
* `GET /health` - Liveness probe
* `GET /ready` - Readiness probe (checks DB + Redis)
* `GET /metrics` - Prometheus metrics

### Production Features

* Structured JSON logging with request/job context
* Prometheus metrics + Grafana dashboards
* Redis caching for schemas and jobs
* Per-user, per-endpoint rate limiting
* Graceful shutdown for API and workers
* Multi-stage Docker builds
* Health checks for orchestration
* Environment separation (local/staging/prod)

This represents a complete, production-grade service suitable for real deployment.

---

## Tech Stack

Deliberately boring choices for reliability and learning.

### Core Framework
* **FastAPI** - Modern async web framework
* **Pydantic** - Data validation and settings management
* **SQLAlchemy 2.x** - ORM and database toolkit
* **Alembic** - Database migrations

### Infrastructure
* **PostgreSQL** - Primary data store
* **Redis** - Queue backend + caching
* **RQ or Celery** - Background job processing
  * *Recommendation*: Start with **RQ** (simpler, easier to debug, faster to learn)
  * Celery is more feature-rich but adds complexity better suited for later projects

### Development & Testing
* **pytest** - Testing framework
* **httpx** - HTTP client (async-capable)
* **uvicorn** - ASGI server
* **Docker / Docker Compose** - Containerization and local dev
* **ruff + mypy** - Linting and type checking

### Observability
* **structlog** - Structured JSON logging
* **prometheus-client** - Metrics instrumentation
* **Grafana** - Metrics visualization

### Other Tools
* **slowapi** - Rate limiting
* **bcrypt** - API key hashing

**Note on cloud services**: Start with local storage and Redis caching. Don’t introduce S3, cloud databases, or other external dependencies initially. Focus on concepts first, cloud integration later.

---

## Data Model

Simple, focused persistence model that grows with the phases.

> **Note**: For a deeper understanding of domain concepts, entities, invariants, and bounded contexts, see [docs/domains.md](domains.md) which provides a domain-driven design perspective.

### jobs

Core entity tracking validation job lifecycle.

* `id` - UUID primary key
* `dataset_type` - Type of dataset (e.g., "student_enrollment")
* `schema_version` - Version of schema to validate against
* `source_type` - "url" or "upload" (initially just "url")
* `source_uri` - Location of data to validate
* `submitted_by` - Foreign key to users (added in Phase 7)
* `status` - Current state (queued/running/succeeded/failed/cancelled/retry_scheduled)
* `idempotency_key` - Optional key for idempotent requests
* `created_at` - Timestamp when job created
* `updated_at` - Timestamp of last update
* `started_at` - When processing began (added in Phase 3)
* `finished_at` - When processing completed (added in Phase 3)
* `retry_count` - Number of retry attempts (added in Phase 3)
* `error_code` - Structured error identifier (added in Phase 3)
* `error_message` - Human-readable error details (added in Phase 3)

### users

User accounts and API key authentication (added in Phase 7).

* `id` - UUID primary key
* `email` - User email (unique)
* `api_key_hash` - Bcrypt hash of API key
* `is_active` - Account status
* `is_admin` - Admin role flag
* `created_at` - Account creation timestamp

### schemas

Schema registry for versioned dataset definitions (added in Phase 5).

* `id` - UUID primary key
* `dataset_type` - Type identifier (e.g., "student_enrollment")
* `version` - Semantic version (e.g., "v1", "v2")
* `definition_json` - JSON schema definition
* `is_active` - Whether this schema version is active
* `created_at` - When schema was registered

### validation_results

Detailed validation outcomes (added in Phase 5).

* `id` - UUID primary key
* `job_id` - Foreign key to jobs
* `total_rows` - Total row count in dataset
* `valid_rows` - Rows passing validation
* `invalid_rows` - Rows failing validation
* `summary_json` - Structured validation report (errors by row/column)
* `created_at` - When results were recorded

### Future Extensions (Not in Initial 12 Phases)

**job_events**: Append-only audit trail of state transitions (useful for debugging, compliance, or building event-sourced systems)

---

## API Design

RESTful API following standard HTTP semantics.

### Job Submission

**`POST /api/v1/jobs`**

Submit a new validation job. Supports idempotency.

Request:
```json
{
  "dataset_type": "student_enrollment",
  "schema_version": "v1",
  "source": {
    "type": "url",
    "uri": "https://example.com/data.csv"
  },
  "idempotency_key": "abc-123"
}
```

Response (201 Created):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "dataset_type": "student_enrollment",
  "schema_version": "v1",
  "status": "queued",
  "created_at": "2026-04-23T10:30:00Z",
  "updated_at": "2026-04-23T10:30:00Z"
}
```

Headers:
- `X-API-Key: <your-api-key>` (required after Phase 7)

### Job Queries

**`GET /api/v1/jobs`**

List jobs with pagination, filtering, and sorting.

Query parameters:
- `page` - Page number (default: 1)
- `page_size` - Items per page (default: 20, max: 100)
- `status` - Filter by status (comma-separated for multiple)
- `dataset_type` - Filter by dataset type
- `created_after` - ISO 8601 timestamp
- `created_before` - ISO 8601 timestamp
- `sort_by` - Field to sort by (created_at, status, dataset_type)
- `sort_order` - asc or desc

Response:
```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "dataset_type": "student_enrollment",
      "status": "succeeded",
      "created_at": "2026-04-23T10:30:00Z"
    }
  ],
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

**`GET /api/v1/jobs/{job_id}`**

Get detailed job information.

Response (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "dataset_type": "student_enrollment",
  "schema_version": "v1",
  "source_type": "url",
  "source_uri": "https://example.com/data.csv",
  "status": "succeeded",
  "created_at": "2026-04-23T10:30:00Z",
  "started_at": "2026-04-23T10:30:05Z",
  "finished_at": "2026-04-23T10:30:42Z",
  "retry_count": 0
}
```

**`GET /api/v1/jobs/{job_id}/results`**

Get validation results for completed job.

Response (200 OK):
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_rows": 1000,
  "valid_rows": 987,
  "invalid_rows": 13,
  "summary": {
    "errors": [
      {
        "row": 42,
        "column": "enrollment_date",
        "error": "Date format invalid: '2024-13-01'"
      }
    ]
  }
}
```

### Job State Transitions (Admin Only)

These endpoints require admin API key (Phase 7+).

**`PATCH /api/v1/jobs/{job_id}/start`**

Manually transition job from queued to running.

**`PATCH /api/v1/jobs/{job_id}/complete`**

Mark job as succeeded (with optional validation results).

Request:
```json
{
  "results": {
    "total_rows": 1000,
    "valid_rows": 1000,
    "invalid_rows": 0
  }
}
```

**`PATCH /api/v1/jobs/{job_id}/fail`**

Mark job as failed with error details.

Request:
```json
{
  "error_code": "network_timeout",
  "error_message": "Failed to download from source URL after 3 attempts"
}
```

**`POST /api/v1/jobs/{job_id}/retry`**

Retry a failed job (increments retry_count, transitions to queued).

**`DELETE /api/v1/jobs/{job_id}`**

Cancel a job (transition to cancelled state).

### Schema Registry

**`GET /api/v1/schemas`**

List available dataset schemas.

Response:
```json
{
  "schemas": [
    {
      "dataset_type": "student_enrollment",
      "version": "v1",
      "is_active": true,
      "created_at": "2026-01-15T08:00:00Z"
    }
  ]
}
```

**`GET /api/v1/schemas/{dataset_type}/{version}`**

Get specific schema definition.

Response:
```json
{
  "dataset_type": "student_enrollment",
  "version": "v1",
  "definition": {
    "required_columns": ["student_id", "school_id", "enrollment_date"],
    "columns": {
      "student_id": {"type": "string", "nullable": false},
      "enrollment_date": {"type": "date", "nullable": false},
      "grade_level": {"type": "integer", "min": 1, "max": 12}
    },
    "business_rules": [
      "enrollment_date <= withdrawal_date",
      "grade_level must be in [1-12]"
    ]
  }
}
```

### System Health

**`GET /health`**

Liveness probe (returns 200 if service is running).

**`GET /ready`**

Readiness probe (checks DB and Redis connectivity).

Response:
```json
{
  "status": "ready",
  "checks": {
    "database": "ok",
    "redis": "ok"
  }
}
```

**`GET /metrics`**

Prometheus metrics endpoint (text format, unauthenticated).

---

## Job Lifecycle State Machine

One of the most important architectural patterns in the project.

### States

Jobs transition through a well-defined state machine:

```
    ┌─────────┐
    │ QUEUED  │ ← Initial state, waiting for worker
    └────┬────┘
         │
         ▼
    ┌─────────┐
    │ RUNNING │ ← Worker processing
    └────┬────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌──────────┐ ┌────────┐
│SUCCEEDED │ │ FAILED │ ← Terminal states
└──────────┘ └───┬────┘
                 │
                 ▼
           ┌───────────────┐
           │RETRY_SCHEDULED│ ← Automatic retry queued
           └───────┬───────┘
                   │
                   ▼
              ┌─────────┐
              │ QUEUED  │ ← Re-enters queue
              └─────────┘

    Non-terminal states can transition to:
    ┌──────────┐
    │CANCELLED │ ← Manual cancellation (from QUEUED, RUNNING, FAILED, RETRY_SCHEDULED)
    └──────────┘
```

### Valid Transitions

State transitions are enforced in the domain model:

- **QUEUED** → RUNNING (worker picks up job)
- **QUEUED** → CANCELLED (manual cancellation)
- **RUNNING** → SUCCEEDED (validation passed)
- **RUNNING** → FAILED (validation failed or error occurred)
- **RUNNING** → CANCELLED (manual cancellation)
- **FAILED** → RETRY_SCHEDULED (if retries remain)
- **FAILED** → CANCELLED (manual cancellation)
- **RETRY_SCHEDULED** → QUEUED (scheduled retry executes)
- **RETRY_SCHEDULED** → CANCELLED (manual cancellation)

Invalid transitions (e.g., SUCCEEDED → RUNNING) raise domain exceptions.

### Why This Matters

Explicit state machines prevent:
- Race conditions from concurrent updates
- Invalid state combinations
- Unclear system behavior
- Debugging nightmares

This pattern is essential for: pipeline orchestration, workflow engines, order processing, approval flows, and any async system with state.

---

## Idempotency Design

First-class feature built in Phase 3, not bolted on later.

### How It Works

When a client submits `POST /api/v1/jobs` with an `idempotency_key`:

1. Service checks if a job with that key already exists
2. **If exists and in terminal state** (SUCCEEDED/FAILED/CANCELLED):
   - Return 409 Conflict (can't reuse key for completed jobs)
3. **If exists and in non-terminal state** (QUEUED/RUNNING/RETRY_SCHEDULED):
   - Return existing job (idempotent create, avoids duplicate)
4. **If doesn't exist**:
   - Create new job with that key

### Example

```bash
# First request
POST /api/v1/jobs
{
  "dataset_type": "student_enrollment",
  "schema_version": "v1",
  "source": {...},
  "idempotency_key": "import-2026-04-23-run-1"
}
# Response: 201 Created, job_id=abc-123

# Duplicate request (network retry)
POST /api/v1/jobs
{
  "dataset_type": "student_enrollment",
  "schema_version": "v1",
  "source": {...},
  "idempotency_key": "import-2026-04-23-run-1"
}
# Response: 200 OK, job_id=abc-123 (same job returned)
```

### Why This Matters

Idempotency is critical for:
- **Network retries** - Client doesn't know if first request succeeded
- **Pipeline reruns** - Airflow/Luigi retry logic
- **Webhook delivery** - Webhooks are often delivered multiple times
- **Duplicate messages** - Queue "at-least-once" delivery guarantees
- **Manual retries** - Operations team re-running commands

Without idempotency, you get duplicate jobs, wasted processing, and incorrect metrics. This is a senior engineer expectation in distributed systems.

---

## Validation Logic

Built in Phase 5, starts with CSV validation.

### Validation Pipeline

Jobs execute validation in stages:

1. **Source accessibility check**
   - Fetch data from URL
   - Check HTTP status, timeouts
   - Enforce max file size limits
   - Handle network failures (transient vs permanent)

2. **File format check**
   - Verify CSV format
   - Check encoding (UTF-8)
   - Detect delimiter
   - Validate headers present

3. **Schema lookup**
   - Fetch schema from registry by dataset_type + version
   - Ensure schema is active
   - Parse schema definition

4. **Required columns check**
   - Verify all required columns present
   - Match column names (case-sensitive)
   - Report missing columns

5. **Type validation**
   - Coerce types according to schema
   - Detect type mismatches (string in integer column)
   - Record per-row type errors

6. **Business rule validation**
   - Apply domain-specific rules
   - Examples:
     - `student_id` must be non-null
     - `enrollment_date <= withdrawal_date`
     - `grade_level` must be in [1, 2, 3, ..., 12]
     - No duplicate `(student_id, school_id, enrollment_date)` keys

7. **Aggregate checks**
   - Row count > 0
   - Percentage of invalid rows < threshold
   - Referential integrity (if applicable)

### Validation Results

Results stored in `validation_results` table:

```json
{
  "total_rows": 1000,
  "valid_rows": 987,
  "invalid_rows": 13,
  "errors": [
    {
      "row": 42,
      "column": "enrollment_date",
      "error_type": "type_mismatch",
      "message": "Expected date, got '2024-13-01'"
    },
    {
      "row": 105,
      "column": "grade_level",
      "error_type": "business_rule_violation",
      "message": "Value 15 exceeds maximum grade level 12"
    }
  ]
}
```

### Future Formats

After Phase 5 is solid, extend to:
- **JSONL** (newline-delimited JSON)
- **Parquet** (columnar format, common in data pipelines)
- **Excel** (.xlsx)

Keep the validation interface generic so new formats plug in easily.

---

## Project Phases

> **Note**: This section provides a high-level overview of the 12 phases. For detailed implementation guidance including specific deliverables, testing strategies, success criteria, and file-by-file breakdown, see [docs/implementation-plan.md](implementation-plan.md).

### Phase 1: Foundation (Project Setup & Basic API)

Goal: Establish project foundation with clean architecture and initial CRUD endpoints.

Build:

* FastAPI app structure
* settings/config
* Pydantic models
* SQLAlchemy setup with repository pattern
* Postgres persistence with Alembic migrations
* Domain model layer (Job entity with state machine)
* `POST /jobs`
* `GET /jobs`
* `GET /jobs/{id}`
* basic error handling
* pytest baseline with coverage enforcement
* Dockerized local dev
* CI/CD pipeline

Focus concepts:

* clean architecture (domain, service, repository layers)
* typing and Pydantic validation
* dependency injection
* REST basics
* packaging/project structure
* config management
* TDD fundamentals

### Phase 2: Structured Logging & Observability Foundation

Goal: Establish logging patterns before building complex async workflows.

Build:

* JSON structured logging (structlog)
* request context middleware (request_id)
* job context propagation (job_id in logs)
* log filtering and configuration

Focus concepts:

* structured logging for distributed systems
* request tracing
* observability foundations

### Phase 3: Complete Job Lifecycle (API State Transitions)

Goal: Enable manual state transitions to prepare for worker automation.

Build:

* State transition endpoints (start, complete, fail, retry, cancel)
* Domain enhancements (error fields, retry_count, timestamps)
* Service layer methods for state transitions
* Idempotency key support
* Database migrations for new fields

Focus concepts:

* RESTful design for state changes
* state machine enforcement
* idempotency patterns
* operational APIs

### Phase 4: Background Processing and Async Workflows

Goal: Automate job execution with background workers.

Build:

* Redis + worker (RQ or Celery)
* enqueue job on submit
* worker processes jobs asynchronously
* automatic state transitions
* worker failure handling
* logging in worker context

Focus concepts:

* async job processing
* message queues
* distributed workflow
* worker patterns

### Phase 5: Data Validation Engine

Goal: Implement core business logic - fetch and validate datasets.

Build:

* schema registry (versioned schema definitions)
* HTTP client for data fetching
* validation service (CSV parsing, type checking, business rules)
* validation result persistence
* result retrieval endpoints
* schema query endpoints

Focus concepts:

* data contracts and schema versioning
* HTTP client patterns (timeouts, retries)
* validation engine design
* domain modeling

### Phase 6: Retry Logic and Error Handling

Goal: Build resilience with automatic retries and failure classification.

Build:

* exponential backoff configuration
* retry decorators on tasks
* failure classification (transient vs permanent)
* dead letter queue
* max retry enforcement

Focus concepts:

* resilience patterns
* retry strategies
* transient vs permanent failures
* error handling discipline

### Phase 7: Authentication (API Keys)

Goal: Secure the API and attribute jobs to users.

Build:

* user model with API keys
* API key generation script
* authentication middleware
* authorization (admin vs regular users)
* job ownership and isolation

Focus concepts:

* API authentication
* authorization patterns
* security basics
* user context

### Phase 8: Pagination and Filtering

Goal: Handle large result sets efficiently.

Build:

* pagination for job listings
* filtering (status, dataset_type, date range)
* sorting
* query optimization

Focus concepts:

* RESTful pagination patterns
* query optimization
* API usability

### Phase 9: Metrics (Prometheus + Grafana)

Goal: Gain visibility into system performance and behavior.

Build:

* Prometheus client instrumentation
* metrics endpoint
* request/job/validation metrics
* Prometheus + Grafana services
* dashboards

Focus concepts:

* application metrics
* Prometheus instrumentation
* observability dashboards
* performance monitoring

### Phase 10: Caching (Redis)

Goal: Optimize performance with strategic caching.

Build:

* cache abstraction layer
* schema caching
* job caching
* cache invalidation
* cache metrics

Focus concepts:

* caching strategies
* cache invalidation
* performance optimization
* Redis usage patterns

### Phase 11: Rate Limiting

Goal: Protect API from abuse and ensure fairness.

Build:

* rate limiting middleware
* per-user, per-endpoint limits
* rate limit headers
* 429 responses
* rate limit metrics

Focus concepts:

* API protection
* rate limiting strategies
* resource fairness

### Phase 12: Production Readiness

Goal: Prepare for production deployment.

Build:

* production Docker image (multi-stage)
* health check endpoints (liveness/readiness)
* graceful shutdown handlers
* environment separation
* migration strategy documentation
* production checklist

Focus concepts:

* production deployment
* health checks
* graceful shutdown
* operational readiness

---

## Timeline and Effort

Based on the 12-phase plan:

- **Duration**: 20-25 days at 1-2 days per phase
- **Time commitment**: 1-2 hours per day
- **Total calendar time**: 4-5 weeks
- **Approach**: Strict TDD throughout, sequential phases

This assumes learning as you go: reading docs, debugging issues, understanding concepts. Phases deliver working software incrementally, so you can pause or adjust scope without losing progress.

---

## After Completion: Stretch Goals

Once the 12 phases are complete, you'll have a production-ready service. Consider adding these stretch features to deepen specific skills:

### Operational Enhancements
* **Webhook callbacks** - Notify external systems on job completion
* **Dead letter queue dashboard** - UI for inspecting and requeuing failed jobs
* **Scheduled recurring jobs** - Cron-like validation schedules
* **Job cancellation reasons** - Track why jobs were cancelled

### Storage & Performance
* **S3-compatible storage** - Store datasets and results in object storage
* **Signed artifact URLs** - Time-limited download links for validation results
* **Streaming validation** - Process large files without loading into memory
* **Batch job submission** - Submit multiple jobs in one request

### Multi-Tenancy & Isolation
* **Organization model** - Multiple teams using the service
* **Dataset access controls** - Role-based permissions per dataset
* **Quota enforcement** - Per-user or per-org job limits

### Developer Experience
* **CLI client** - Command-line tool for submitting jobs
* **Python SDK** - Client library for programmatic access
* **Admin dashboard** - Web UI for operations team
* **API documentation** - Auto-generated OpenAPI/Swagger docs

### Advanced Observability
* **OpenTelemetry tracing** - Distributed traces across API → worker → DB
* **Alerting rules** - Prometheus alerts for error rates, latency spikes
* **SLO tracking** - Service level objectives and error budgets
* **Audit log** - Immutable event stream of all state transitions

### Architectural Evolution
* **Event sourcing** - Rebuild job state from append-only event log
* **Multi-format support** - JSONL, Parquet, Excel validation
* **Schema migration tools** - Automated schema version upgrades
* **Approval workflows** - Human-in-the-loop validation approval

Choose 1-2 stretch goals that align with what you want to learn next. Don't try to build them all—each is a project unto itself.

---

## Learning Outcomes

By completing the 12-phase plan, you'll have hands-on experience with:

### Technical Skills
- RESTful API design (CRUD, state transitions, pagination, filtering, idempotency)
- TDD discipline (red-green-refactor for 20+ days)
- Clean architecture (domain models, repository pattern, service layer)
- Background job processing (async workflows, message queues)
- State machine implementation (explicit transitions, validation)
- Authentication & authorization (API keys, role-based access)
- Observability (structured logging, metrics, dashboards)
- Caching strategies (Redis, cache invalidation)
- Rate limiting (per-user, per-endpoint)
- Production deployment (Docker, health checks, graceful shutdown)

### System Design Patterns
- Idempotency for distributed systems
- Retry logic with exponential backoff
- Failure classification (transient vs permanent)
- Schema versioning and evolution
- Data validation pipelines
- Worker resilience patterns

### Artifacts
- Production-ready FastAPI service
- Comprehensive test suite (unit + integration, >70% coverage)
- CI/CD pipeline
- Grafana dashboards
- Deployment documentation
- API documentation

This is more than a tutorial project—it's a portfolio-grade system demonstrating senior-level concepts.
