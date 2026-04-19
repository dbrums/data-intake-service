# Domain Model - Data Intake Service

This document captures the domain knowledge, entities, boundaries, and patterns for the Data Intake and Validation Service.

## Core Domains Identified

### 1. Job Management Domain (Core Aggregate)

**Purpose:** Orchestrate validation workflows through explicit state transitions

**Key Entities:**
- **Job** (Aggregate Root)
  - Identity: `job_id`
  - Lifecycle: `queued → running → succeeded/failed → [retry_scheduled] → cancelled`
  - Properties: `dataset_type`, `schema_version`, `source`, `submitted_by`, `idempotency_key`
  - Temporal: `created_at`, `started_at`, `finished_at`
  - Resilience: `retry_count`, `error_code`, `error_message`

**Invariants:**
- State transitions must be validated (no arbitrary jumps)
- `finished_at` must be >= `started_at` >= `created_at`
- Idempotency keys prevent duplicate job creation
- Retry only allowed from `failed` state

**Domain Events:**
- `JobSubmitted`, `JobStarted`, `JobSucceeded`, `JobFailed`, `JobRetryScheduled`, `JobCancelled`

### 2. Validation Domain

**Purpose:** Enforce data quality through multi-phase validation pipeline

**Validation Phases (Order Matters):**
1. **Source Accessibility** - can we reach the data?
2. **Format Check** - is it parseable (CSV/JSONL/Parquet)?
3. **Schema Conformance** - required columns present?
4. **Type Coercion** - can values be cast to expected types?
5. **Business Rules** - row-level constraints (nullability, value ranges, cross-field)
6. **Aggregate Checks** - uniqueness constraints, cardinality rules

**Key Entities:**
- **ValidationResult** (Value Object)
  - Metrics: `total_rows`, `valid_rows`, `invalid_rows`
  - Summary: `summary_json` (detailed error breakdown)
  - Artifact: `artifact_uri` (points to detailed report)

**Business Rules Examples:**
- `student_id` non-null
- `enrollment_date <= withdrawal_date`
- `grade_level` in allowed values
- No duplicate `(student_id, school_id, effective_date)` composite keys

### 3. Schema Registry Domain

**Purpose:** Version-controlled data contracts as first-class entities

**Key Entities:**
- **DatasetSchema** (Aggregate Root)
  - Identity: `(dataset_type, version)` composite key
  - Definition: `definition_json` (column specs, types, rules)
  - Lifecycle: `is_active` flag
  - Temporal: `created_at`

**Concepts:**
- Schemas are **versioned** - `student_enrollment:v1`, `student_enrollment:v2`
- Only one version can be `is_active=true` per dataset type (or multiple active versions allowed?)
- Schema evolution: new versions don't break existing jobs

**Invariants:**
- Version strings must be immutable once created
- Definition changes require new version
- Cannot delete schemas referenced by existing jobs

### 4. Data Source Domain

**Purpose:** Abstract different ingestion mechanisms

**Source Types:**
- **URL Pull** - `{"type": "url", "uri": "https://..."}`
- **File Upload** - direct upload (binary data in request)
- Future: S3/GCS paths, streaming sources

**Responsibilities:**
- Retrieve data from source
- Handle transient failures (retry with backoff)
- Support large files (streaming)

### 5. Idempotency Domain (Cross-cutting)

**Purpose:** Prevent duplicate processing from retries

**Key Concepts:**
- `idempotency_key` in submission = client-controlled deduplication
- Check existing jobs before creating new one
- Return existing job if key matches
- Keys must be unique + contextual (likely scoped to user/tenant)

**Critical for:**
- Webhook retries
- Pipeline reruns
- Client-side retry logic
- Network failure recovery

---

## Domain Relationships

```
Job (1) ←→ (1) ValidationResult
Job (N) → (1) DatasetSchema [via dataset_type + schema_version]
Job (1) → (1) DataSource [composition]
Job (1) ← (N) JobEvent [optional audit trail]
```

---

## Bounded Contexts

**API Context:**
- Translates HTTP requests to domain commands
- Owns request/response schemas
- Exception → HTTP status mapping
- Never imports from workers

**Worker Context:**
- Executes async validation jobs
- Owns background job infrastructure
- Never imports from API

**Shared Kernel:**
- Services layer (business logic)
- Repositories (data access)
- DB models (persistence)
- Core utilities (config, logging, exceptions)

---

## Key Domain Patterns

**State Machine:** Jobs follow explicit FSM, transitions validated

**Event Sourcing (Optional):** `job_events` table for audit trail

**Repository Pattern:** Abstract persistence from business logic

**Value Objects:** `ValidationResult`, `DataSource` (no identity, compared by value)

**Aggregate Roots:** `Job`, `DatasetSchema` (consistency boundaries)

**Idempotent Operations:** Submission, retry (using idempotency keys)

---

## What This Teaches You

This domain model naturally forces:
- **Workflow state management** (FSM)
- **Data contracts** (versioned schemas)
- **Boundary validation** (multi-phase validation)
- **Resilience patterns** (idempotency, retries)
- **Async workflows** (job submission ≠ job execution)
- **Domain events** (state transition tracking)

The complexity is real but not overwhelming - perfect senior-level scope.
