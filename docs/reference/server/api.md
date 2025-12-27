# Server API Reference

The WhatsNext server provides a REST API built with FastAPI.

**Base URL**: `http://localhost:8000` (or your deployed server)

**API Documentation**: Access interactive docs at `/docs` (Swagger UI) or `/redoc` (ReDoc)

## Authentication

If API keys are configured, include the `X-API-Key` header in all requests:

```bash
curl -H "X-API-Key: your-api-key" http://localhost:8000/projects/
```

## Projects

Projects are containers for organizing related tasks and jobs.

### List Projects

```http
GET /projects/
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `limit` | int | Max results (default: 100) |
| `skip` | int | Offset for pagination |
| `status` | string | Filter by status (ACTIVE, ARCHIVED) |

**Response:**

```json
[
  {
    "id": 1,
    "name": "ml-training",
    "description": "Machine learning experiments",
    "status": "ACTIVE",
    "created_at": "2024-01-15T10:30:00",
    "updated_at": "2024-01-15T10:30:00"
  }
]
```

### Create Project

```http
POST /projects/
```

**Request Body:**

```json
{
  "name": "ml-training",
  "description": "Machine learning experiments"
}
```

**Response:** `201 Created`

```json
{
  "id": 1,
  "name": "ml-training",
  "description": "Machine learning experiments",
  "status": "ACTIVE",
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00"
}
```

### Get Project

```http
GET /projects/{id}
GET /projects/name/{name}
```

### Update Project

```http
PUT /projects/{id}
```

**Request Body:**

```json
{
  "name": "ml-training-v2",
  "description": "Updated description",
  "status": "ACTIVE"
}
```

### Delete Project

```http
DELETE /projects/{id}
DELETE /projects/name/{name}
```

**Response:** `204 No Content`

### Fetch Next Job

Get the next job ready for execution from a project's queue.

```http
GET /projects/{id}/fetch_job
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `available_cpu` | int | Filter by CPU requirement (0 = no filter) |
| `available_accelerators` | int | Filter by accelerator requirement (0 = no filter) |

**Response:**

```json
{
  "job": {
    "id": 42,
    "name": "experiment-1",
    "project_id": 1,
    "task_id": 1,
    "task_name": "train-model",
    "parameters": {"lr": 0.01},
    "status": "QUEUED",
    "priority": 5,
    "depends": {},
    "created_at": "2024-01-15T10:30:00",
    "updated_at": "2024-01-15T10:35:00"
  },
  "num_pending": 10
}
```

**Notes:**

- Jobs are returned in priority order (highest first)
- Jobs with unmet dependencies are skipped
- Jobs are marked as `QUEUED` when fetched

### Clear Queue

Delete all pending jobs from a project's queue.

```http
DELETE /projects/{id}/queue
```

**Response:**

```json
{
  "deleted": 15
}
```

### Batch Create Jobs

Create multiple jobs in a single request.

```http
POST /projects/{id}/jobs/batch
```

**Request Body:**

```json
{
  "jobs": [
    {"name": "job-1", "task_id": 1, "parameters": {"x": 1}},
    {"name": "job-2", "task_id": 1, "parameters": {"x": 2}},
    {"name": "job-3", "task_id": 1, "parameters": {"x": 3}}
  ]
}
```

**Response:** `201 Created`

```json
{
  "created": 3,
  "job_ids": [1, 2, 3]
}
```

## Tasks

Tasks define types of jobs that can be run, including resource requirements.

### List Tasks

```http
GET /tasks/
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | int | Yes | Filter by project |

### Create Task

```http
POST /tasks/
```

**Request Body:**

```json
{
  "name": "train-model",
  "project_id": 1,
  "command_template": "python train.py --lr {lr} --epochs {epochs}",
  "required_cpu": 8,
  "required_accelerators": 4
}
```

**Response:** `201 Created`

```json
{
  "id": 1,
  "name": "train-model",
  "project_id": 1,
  "command_template": "python train.py --lr {lr} --epochs {epochs}",
  "required_cpu": 8,
  "required_accelerators": 4,
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00"
}
```

### Get Task

```http
GET /tasks/{id}
GET /tasks/name/{name}?project_id=1
```

### Update Task

```http
PUT /tasks/{id}
```

**Request Body:** (partial updates supported)

```json
{
  "required_cpu": 16,
  "required_accelerators": 8
}
```

### Delete Task

```http
DELETE /tasks/{id}
```

## Jobs

Jobs are instances of tasks waiting to be executed.

### List Jobs

```http
GET /jobs/
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `project_id` | int | Filter by project |
| `limit` | int | Max results |
| `skip` | int | Offset for pagination |

### Create Job

```http
POST /jobs/
```

**Request Body:**

```json
{
  "name": "experiment-001",
  "project_id": 1,
  "task_id": 1,
  "parameters": {
    "learning_rate": 0.01,
    "epochs": 100,
    "batch_size": 32
  },
  "priority": 5,
  "depends": {}
}
```

**Priority:** Higher numbers = higher priority (processed first)

**Depends:** Map of job ID to job name for dependencies:

```json
{
  "depends": {
    "42": "preprocessing-job",
    "43": "data-validation"
  }
}
```

### Get Job

```http
GET /jobs/{id}
```

### Update Job

```http
PUT /jobs/{id}
```

**Request Body:**

```json
{
  "name": "experiment-001",
  "project_id": 1,
  "task_id": 1,
  "parameters": {"learning_rate": 0.01},
  "status": "COMPLETED",
  "priority": 5,
  "depends": {}
}
```

**Valid Status Values:**

| Status | Description |
|--------|-------------|
| `PENDING` | Waiting to be scheduled |
| `QUEUED` | Scheduled, waiting for worker |
| `RUNNING` | Currently executing |
| `COMPLETED` | Finished successfully |
| `FAILED` | Execution failed |
| `BLOCKED` | Dependency failed |

### Delete Job

```http
DELETE /jobs/{id}
```

### Get Job Dependencies

Check the status of a job's dependencies.

```http
GET /jobs/{id}/dependencies
```

**Response:**

```json
{
  "job_id": 45,
  "dependencies": [
    {
      "id": 42,
      "name": "preprocessing",
      "status": "COMPLETED"
    },
    {
      "id": 43,
      "name": "validation",
      "status": "RUNNING"
    }
  ],
  "all_completed": false
}
```

## Clients

Clients are worker processes that execute jobs.

### Register Client

Register a new client or update an existing one.

```http
POST /clients/register
```

**Request Body:**

```json
{
  "id": "worker-gpu-001",
  "name": "GPU Worker 1",
  "entity": "ml-team",
  "description": "4x A100 training server",
  "available_cpu": 64,
  "available_accelerators": 4
}
```

**Response:** `201 Created`

```json
{
  "id": "worker-gpu-001",
  "name": "GPU Worker 1",
  "entity": "ml-team",
  "description": "4x A100 training server",
  "available_cpu": 64,
  "available_accelerators": 4,
  "last_heartbeat": "2024-01-15T10:30:00",
  "created_at": "2024-01-15T10:30:00",
  "is_active": 1
}
```

### List Clients

```http
GET /clients/
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `active_only` | bool | Only show active clients (default: true) |
| `limit` | int | Max results |
| `skip` | int | Offset |

### Get Client

```http
GET /clients/{id}
```

### Update Client

```http
PUT /clients/{id}
```

**Request Body:** (partial updates supported)

```json
{
  "available_cpu": 32,
  "available_accelerators": 2
}
```

### Client Heartbeat

Update the client's last heartbeat timestamp.

```http
POST /clients/{id}/heartbeat
```

**Response:**

```json
{
  "status": "ok"
}
```

### Deactivate Client

Mark a client as inactive (graceful disconnect).

```http
POST /clients/{id}/deactivate
```

**Response:**

```json
{
  "status": "deactivated"
}
```

### Delete Client

```http
DELETE /clients/{id}
```

## Health Checks

### Connection Check

```http
GET /
```

**Response:**

```json
{
  "message": "OK"
}
```

### Database Check

```http
GET /checkdb
```

**Response:**

```json
{
  "message": "DB is working"
}
```

## Error Responses

All endpoints return standard HTTP error codes:

| Code | Description |
|------|-------------|
| `400` | Bad request (invalid parameters) |
| `401` | Unauthorized (missing API key) |
| `403` | Forbidden (invalid API key) |
| `404` | Resource not found |
| `422` | Validation error |
| `429` | Rate limit exceeded |
| `500` | Internal server error |

**Error Response Format:**

```json
{
  "detail": "Project with id 999 not found."
}
```

**Validation Error Format:**

```json
{
  "detail": [
    {
      "loc": ["body", "name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```
