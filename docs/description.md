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

## What the MVP should look like

Keep the first shippable version narrower than your final vision.

### MVP capabilities

* submit a validation job using a JSON payload containing:

  * dataset type
  * schema version
  * file URL or small uploaded file
  * idempotency key
* persist job metadata in Postgres
* enqueue job for background processing
* worker downloads or reads the input
* worker validates:

  * file shape
  * required columns
  * data types
  * a few business rules
* persist validation results
* expose:

  * `POST /jobs`
  * `GET /jobs/{job_id}`
  * `GET /jobs/{job_id}/results`
  * `POST /jobs/{job_id}/retry`
  * `GET /schemas`
* structured logs with request ID and job ID
* metrics endpoint
* tests
* Dockerized local run

That is already enough to teach you a large amount.

---

## Tech choices

Use boring choices.

* **FastAPI**
* **Pydantic**
* **SQLAlchemy 2.x**
* **Postgres**
* **Alembic**
* **Redis**
* **RQ or Dramatiq** for background jobs

For a first project, I would lean **Dramatiq** or **RQ** over Celery. They are easier to reason about. You do not need Celery’s complexity yet.

* **pytest**
* **httpx**
* **uvicorn**
* **Docker / docker compose**
* **structlog or stdlib logging with JSON formatter**
* **prometheus-client**
* **ruff + mypy**

For file handling, start with local disk or a local object-store emulator. Do not introduce real cloud dependencies immediately.

---

## Data model

Keep the persistence model simple.

### jobs

* id
* dataset_type
* schema_version
* source_type
* source_uri
* submitted_by
* status
* idempotency_key
* created_at
* started_at
* finished_at
* retry_count
* error_code
* error_message

### validation_results

* id
* job_id
* total_rows
* valid_rows
* invalid_rows
* summary_json
* artifact_uri

### schemas

* id
* dataset_type
* version
* definition_json
* is_active
* created_at

Optional later:

### job_events

For an append-only audit trail of state transitions.

---

## API design

A clean first-pass API could be:

### `POST /jobs`

Submit a job.

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

Response:

```json
{
  "job_id": "job_001",
  "status": "queued"
}
```

### `GET /jobs/{job_id}`

Returns job metadata and current state.

### `GET /jobs/{job_id}/results`

Returns validation summary and links to artifacts.

### `POST /jobs/{job_id}/retry`

Retries only if the prior state allows it.

### `GET /jobs`

Supports filtering by status, dataset type, date range, submitter, pagination.

### `GET /schemas`

Returns available schemas.

### `POST /schemas`

Admin-only in later phases.

---

## Job lifecycle

This is one of the most important parts.

Use an explicit state machine:

* `queued`
* `running`
* `succeeded`
* `failed`
* `cancelled`

Optional:

* `retry_scheduled`
* `partially_succeeded`

Make state transitions explicit and validated. Do not allow arbitrary updates from anywhere.

This directly teaches workflow state management, which your document correctly highlights as essential. 

---

## Idempotency design

This should be a first-class feature, not a later cleanup task.

When a client submits `POST /jobs` with an `idempotency_key`, the API should:

* check whether a matching request already exists
* if yes, return the existing job instead of creating a new one
* if not, create a new job

Store the idempotency key with enough context to prevent accidental duplication.

This is a core senior-DE concept because it shows up everywhere: pipeline reruns, delivery retries, webhook handling, duplicate loads. Your attached document is right to elevate it. 

---

## Validation logic

Start with CSV.

Validation phases:

1. source accessibility check
2. file format check
3. required columns check
4. type coercion / type errors
5. row-level business rule validation
6. aggregate checks

Examples of business rules:

* `student_id` must be non-null
* `enrollment_date <= withdrawal_date`
* `grade_level` must be in accepted values
* no duplicate `(student_id, school_id, effective_date)` keys

Later, support JSONL or parquet.

---

## Project Phases

### Phase 1: Core API and clean structure

Goal: get a thin but real service running.

Build:

* FastAPI app structure
* settings/config
* Pydantic models
* SQLAlchemy setup
* Postgres persistence
* `POST /jobs`
* `GET /jobs/{id}`
* basic error handling
* structured logging
* pytest baseline
* Dockerized local dev

Focus concepts:

* architecture
* typing
* dependency injection
* REST basics
* packaging/project structure
* config management

### Phase 2: Background processing and state transitions

Build:

* Redis + worker
* enqueue job on submit
* worker processes simple validation
* job lifecycle state machine
* retry endpoint
* idempotency key support

Focus concepts:

* background jobs
* async workflow state
* resilience
* idempotency
* service-to-service communication patterns

### Phase 3: Validation engine and data contracts

Build:

* schema registry table
* versioned schema definitions
* richer validation reports
* reusable validator interfaces
* downloadable artifacts for failures

Focus concepts:

* data contracts
* boundary validation
* domain modeling
* extensibility

### Phase 4: Auth, authz, and safer operations

Build:

* API keys first
* roles
* admin-only schema management
* job ownership checks

Focus concepts:

* auth
* authorization
* protected internal services

### Phase 5: Observability and operational maturity

Build:

* Prometheus metrics
* request timing middleware
* correlation IDs
* health/readiness endpoints
* better failure taxonomy
* backoff on transient failures

Focus concepts:

* monitoring
* practical observability
* production debugging
* error handling discipline

### Phase 6: Performance and robustness

Build:

* streamed file reads
* chunked validation
* load testing
* pagination/filtering refinement
* caching for schema lookups
* rate limiting conceptually or minimally

Focus concepts:

* performance basics
* load testing
* caching
* scaling tradeoffs

### Phase 7: Deployment polish

Build:

* production Docker image
* compose for local multi-service stack
* environment separation
* migration flow
* basic reverse proxy understanding
* CI checks

Focus concepts:

* deployment model
* environment management
* real-world run lifecycle

---

## Stretch goals

After the core project is solid, add one or two of these:

* webhook callback on job completion
* S3-compatible storage backend
* CLI client
* signed artifact URLs
* dead-letter queue behavior
* multi-tenant dataset isolation
* OpenTelemetry tracing
* admin dashboard
* scheduled recurring jobs

These are useful, but not necessary for the first full pass.