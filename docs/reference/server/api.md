# Server API

The WhatsNext server provides a REST API built with FastAPI.

## Endpoints

### Projects

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/projects` | List all projects |
| POST | `/projects` | Create a new project |
| GET | `/projects/{id}` | Get project by ID |
| PUT | `/projects/{id}` | Update project |
| DELETE | `/projects/{id}` | Delete project |
| GET | `/projects/{id}/fetch_job` | Fetch next job from queue |

### Jobs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/jobs` | List all jobs |
| POST | `/jobs` | Create a new job |
| GET | `/jobs/{id}` | Get job by ID |
| PUT | `/jobs/{id}` | Update job |
| DELETE | `/jobs/{id}` | Delete job |

### Tasks

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/tasks` | List all tasks |
| POST | `/tasks` | Create a new task |
| GET | `/tasks/{id}` | Get task by ID |
| PUT | `/tasks/{id}` | Update task |
| DELETE | `/tasks/{id}` | Delete task |

## API Reference

::: whatsnext.api.server.main
