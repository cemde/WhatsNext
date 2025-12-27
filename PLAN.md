# Implementation Plan: WhatsNext

This document compares the current state to the vision and outlines the path forward.

---

## Critical Issues (Must Fix First)

Issues found during code review that cause runtime errors, security vulnerabilities, or violate best practices.

### Security Vulnerabilities

| Severity | File | Line | Issue | Status |
|----------|------|------|-------|--------|
| **CRITICAL** | `client/job.py` | 48-49 | Command injection via `os.system(command)` - user parameters passed directly to shell | ✅ Fixed - uses `subprocess.run(shell=False)` |
| **HIGH** | `server/database.py` | 8 | Database password in plaintext URL string | ✅ Fixed - uses environment variables via pydantic-settings |
| **MEDIUM** | `server/routers/jobs.py` | 65 | Debug `print()` exposes data to logs | ✅ Fixed - removed |
| **MEDIUM** | `client/server.py` | 141 | No timeout on HTTP requests (can hang forever) | ✅ Fixed - all requests have `DEFAULT_TIMEOUT` |

### Runtime Errors (Code Will Crash)

| File | Line | Issue | Status |
|------|------|-------|--------|
| `server/routers/projects.py` | 79 | Parameter named `str` (Python builtin) instead of `id` | ✅ Fixed |
| `server/routers/tasks.py` | 43 | References undefined variable `id` in error message | ✅ Fixed |
| `client/task.py` | 8 | Missing import for `random_string()` | ✅ Fixed |
| `client/project.py` | 56-57 | Property `queue` doesn't return value | ✅ Fixed |
| `server/routers/projects.py` | 96-100 | Response dict keys don't match schema | ✅ Fixed |

### Type Errors

| File | Line | Issue | Status |
|------|------|-------|--------|
| `client/client.py` | 28 | Type mismatch: `accelerator: List[int]` but `Resource` expects `List[str]` | ✅ Fixed |
| `server/schemas.py` | 19 | Mutable default `depends: Dict = {}` shared across instances | ✅ Fixed - uses `Field(default_factory=dict)` |
| `client/job.py` | 17 | Type hint says `List[Any]` but comment says "replaced by Job" | ✅ Fixed |
| `server/validate_in_db.py` | 16 | `task_id` parameter type `str` should be `int` | ✅ Fixed |

### API Design Violations

| File | Line | Issue | Status |
|------|------|-------|--------|
| `server/routers/jobs.py` | 13-16 | Non-RESTful `/jobs/all` endpoint (redundant) | ✅ Removed |
| `server/routers/projects.py` | 26, 71, 82, 91 | Wrong resource names in error messages ("Job" instead of "Project") | ✅ Fixed |
| `server/routers/tasks.py` | 35, 43 | Error messages say "Project" when getting tasks | ✅ Fixed |

### Dead Code & Cruft

| File | Line | Issue | Status |
|------|------|-------|--------|
| `client/server.py` | 14-15 | Global mutable state `dummy_projects`, `dummy_jobs` | ✅ Removed |
| `client/server.py` | 32-95 | Large commented-out code blocks | ✅ Removed |
| `client/learn_requests.py` | 1-12 | Test/example code in production | ✅ Deleted |
| `client/client.py` | 36-40 | Empty `append_artifact()`, `extend_artifacts()` methods | ✅ Removed |
| `server/routers/jobs.py` | 30-34 | Commented-out code block | ✅ Removed |
| `server/routers/tasks.py` | 59-61 | Empty `update_task()` endpoint | ✅ Implemented |

### Architecture Issues

| File | Issue | Status |
|------|-------|--------|
| `client/job.py` | `Job.run()` mixes data object with execution logic - violates SRP | ✅ Fixed - uses Formatter for execution |
| `client/project.py` | Thin wrapper delegating everything to `_server` - no domain logic | ✅ Acceptable pattern for stateless client |
| `client/server.py` | `ProjectConnector` mixes dummy data with HTTP calls inconsistently | ✅ Fixed - clean HTTP-only implementation |
| `client/client.py` | Mixes resource management, artifacts, and formatting - unclear purpose | ✅ Clarified - focused on worker functionality |

---

## Status Quo vs Vision

| Feature | Vision | Current State | Gap |
|---------|--------|---------------|-----|
| Stateless client | All state on server | ✅ Design correct, clean implementation | Done |
| Formatter system | Convert params → commands | ✅ CLIFormatter, SlurmFormatter, RUNAIFormatter implemented | Done |
| Worker loop | `client.work()` pulls continuously | ✅ Implemented with signal handling | Done |
| Priority queuing | Higher priority first | ✅ Working | Done |
| Job dependencies | Jobs wait for dependencies | ⚠️ `depends` field exists, not enforced | Server-side logic needed |
| Resource tracking | CPU/GPU allocation | ⚠️ Classes exist, basic tracking | Enhanced implementation needed |
| Artifact management | Track job I/O | ❌ Stub only | Future phase |
| Queue operations | pop, extend, clear | ✅ Implemented | Done |
| Security | Auth, CORS | ❌ None | Future phase |
| Tests | Comprehensive coverage | ❌ Mostly stubs | Ongoing |

---

## Phase 0: Critical Fixes (Blockers) ✅ COMPLETE

Fix issues that cause crashes or security vulnerabilities.

### 0.1 Security fixes
- [x] Replace `os.system()` with `subprocess.run(shell=False)` in `client/job.py`
- [x] Move database credentials to environment variables in `server/database.py`
- [x] Add timeout to all `requests.*()` calls in `client/server.py`
- [x] Remove debug `print()` statements from routers

### 0.2 Runtime error fixes
- [x] Fix parameter `str` → `id` in `server/routers/projects.py:79`
- [x] Fix undefined `id` variable in `server/routers/tasks.py:43`
- [x] Add missing import in `client/task.py`
- [x] Add return statement to `queue` property in `client/project.py`
- [x] Fix response dict keys in `server/routers/projects.py:100`

### 0.3 Type fixes
- [x] Fix `accelerator` type in `client/client.py`
- [x] Fix mutable default `depends={}` in `server/schemas.py`

---

## Phase 1: Cleanup ✅ COMPLETE

Remove legacy code and establish clean foundation.

### 1.1 Remove dead code
- [x] Delete `dummy_projects = {}` and `dummy_jobs = {}` from `client/server.py`
- [x] Delete `client/learn_requests.py` (test code in production)
- [x] Remove all commented-out code blocks
- [x] Remove empty stub methods (`append_artifact`, `extend_artifacts`)
- [x] Remove or implement empty `update_task()` endpoint

### 1.2 Fix API error messages
- [x] Fix all "Job with" → "Project with" in `server/routers/projects.py`
- [x] Fix all "Project with" → "Task with" in `server/routers/tasks.py`
- [x] Remove redundant `/jobs/all` endpoint

### 1.3 Simplify ProjectConnector
- [x] Remove all dummy data references
- [x] Make all methods use HTTP calls consistently

---

## Phase 2: Formatter System ✅ COMPLETE

Implement the runtime-agnostic job execution.

### 2.1 Define Formatter interface
```python
class Formatter(ABC):
    @abstractmethod
    def format(self, task: str, parameters: Dict[str, Any]) -> List[str]:
        """Convert job parameters to executable command."""
        pass

    @abstractmethod
    def execute(self, command: List[str]) -> subprocess.CompletedProcess:
        """Execute the formatted command. Returns CompletedProcess."""
        pass
```

### 2.2 Implement formatters
- [x] `CLIFormatter`: Direct shell command execution
- [x] `SlurmFormatter`: Generate and submit sbatch scripts
- [x] `RUNAIFormatter`: Generate RUNAI job submissions
- [ ] `PythonFormatter`: Call Python functions directly (optional - future)

### 2.3 Template system
- [x] Define command templates per task (e.g., `"python train.py --lr {lr} --epochs {epochs}"`)
- [x] Parameter substitution with validation

---

## Phase 3: Worker Loop ✅ COMPLETE

Enable continuous job pulling.

### 3.1 Implement `Client.work()` method
```python
def work(self, resource: Optional[Resource] = None, poll_interval: float = 5.0, run_forever: bool = False) -> int:
    """Continuously fetch and execute jobs until queue is empty."""
```

### 3.2 Features
- [x] Configurable poll interval for waiting on new jobs
- [x] Graceful shutdown on SIGINT/SIGTERM
- [x] Option to run forever vs exit on empty queue
- [x] Logging of job execution

### 3.3 Update `Job.run()`
- [x] Use formatter from client/resource
- [x] Proper subprocess handling (not `os.system`)
- [x] Capture stdout/stderr
- [ ] Report execution time to server (future enhancement)

---

## Phase 4: Queue Operations ✅ COMPLETE

Complete the queue management API.

### 4.1 Server endpoints
- [x] `DELETE /projects/{id}/jobs/{job_id}` - Remove specific job
- [x] `DELETE /projects/{id}/queue` - Clear all pending jobs
- [x] `POST /projects/{id}/jobs/batch` - Add multiple jobs

### 4.2 Client methods
- [x] `pop_queue(idx)` → Remove job by index
- [x] `extend_queue(jobs)` → Add multiple jobs
- [x] `remove_job(job_id)` → Remove specific job
- [x] `clear_queue()` → Clear all pending jobs

---

## Phase 5: Job Dependencies ✅ COMPLETE

Enforce job execution order.

### 5.1 Server-side dependency resolution
- [x] `fetch_job` only returns jobs whose dependencies are COMPLETED
- [x] Track dependency graph
- [x] Detect circular dependencies on job creation

### 5.2 Dependency status propagation
- [x] If dependency FAILED, mark dependent jobs as BLOCKED
- [x] API to query job dependency status (`GET /jobs/{id}/dependencies`)

---

## Phase 6: Resource Management ✅ COMPLETE

Track and enforce resource allocation.

### 6.1 Resource model improvements
- [x] Define resource requirements per task (`required_cpu`, `required_accelerators` fields)
- [x] Track available vs allocated resources per client (Client model with resources)
- [x] `fetch_job` can filter by resource availability (query params)

### 6.2 Client resource registration
- [x] Client reports available resources on connect (`/clients/register` endpoint)
- [x] Server tracks which client has which resources (Client model in DB)

---

## Phase 7: Testing & Documentation ✅ COMPLETE

### 7.1 Tests
- [x] Unit tests for formatters (18 tests)
- [x] Unit tests for client methods (19 tests)
- [x] Server endpoint tests (7 tests)
- [ ] Integration tests for full job lifecycle (requires PostgreSQL)

### 7.2 Documentation
- [ ] Quickstart guide with real examples
- [ ] Formatter configuration guide
- [ ] API reference (auto-generated from docstrings)
- [ ] Deployment guide

---

## Phase 8: Deployment & Security ✅ COMPLETE

For external/public-facing servers.

### 8.1 Basic deployment (systemd)
- [x] Document systemd service setup
- [x] Add example `whatsnext.service` file to repo (`deploy/`)
- [x] Add deployment README (`deploy/README.md`)

### 8.2 HTTPS with reverse proxy
- [x] Document nginx/caddy setup for HTTPS termination
- [x] Add example nginx config to repo (`deploy/nginx.conf`)

### 8.3 Authentication
- [x] API key authentication for clients (`X-API-Key` header)
- [x] Environment variable for API key(s) (`api_keys` setting)
- [x] Middleware to validate requests (`AuthenticationMiddleware`)

### 8.4 Rate limiting & CORS
- [x] Add CORS middleware for allowed origins (configurable via settings)
- [x] Basic rate limiting to prevent abuse (`RateLimitMiddleware`)

---

## Future Phases (Not Planned Yet)

- **User Roles**: Multi-user with permissions
- **Artifact Management**: Track job inputs/outputs, file storage
- **Web Dashboard**: Monitor jobs, projects, queue status
- **Metrics & Monitoring**: Prometheus integration, job duration tracking

---

## Implementation Summary

**Completed Phases:**
- Phase 0: Critical Fixes ✅
- Phase 1: Cleanup ✅
- Phase 2: Formatter System ✅
- Phase 3: Worker Loop ✅
- Phase 4: Queue Operations ✅
- Phase 5: Job Dependencies ✅
- Phase 6: Resource Management ✅
- Phase 7: Testing (unit tests) ✅
- Phase 8: Security (auth, CORS, rate limiting) ✅

**Remaining Work:**
1. **Phase 7.2**: Documentation (quickstart, guides)
2. **Integration tests**: Full job lifecycle tests with PostgreSQL

The system now has a complete implementation with:
- Job dependency enforcement with circular detection and failure propagation
- Resource-aware job scheduling (CPU/accelerator requirements)
- Client registration and resource tracking
- API key authentication (optional)
- CORS support for web clients
- Rate limiting to prevent abuse
- Comprehensive unit tests (44 tests passing)
