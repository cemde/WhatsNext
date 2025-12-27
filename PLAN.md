# Implementation Plan: WhatsNext

This document compares the current state to the vision and outlines the path forward.

---

## Critical Issues (Must Fix First)

Issues found during code review that cause runtime errors, security vulnerabilities, or violate best practices.

### Security Vulnerabilities

| Severity | File | Line | Issue |
|----------|------|------|-------|
| **CRITICAL** | `client/job.py` | 48-49 | Command injection via `os.system(command)` - user parameters passed directly to shell |
| **HIGH** | `server/database.py` | 8 | Database password in plaintext URL string |
| **MEDIUM** | `server/routers/jobs.py` | 65 | Debug `print()` exposes data to logs |
| **MEDIUM** | `client/server.py` | 141 | No timeout on HTTP requests (can hang forever) |

### Runtime Errors (Code Will Crash)

| File | Line | Issue |
|------|------|-------|
| `server/routers/projects.py` | 79 | Parameter named `str` (Python builtin) instead of `id` |
| `server/routers/tasks.py` | 43 | References undefined variable `id` in error message |
| `client/task.py` | 8 | Missing import for `random_string()` |
| `client/project.py` | 56-57 | Property `queue` doesn't return value |
| `server/routers/projects.py` | 96-100 | Response dict keys don't match schema |

### Type Errors

| File | Line | Issue |
|------|------|-------|
| `client/client.py` | 28 | Type mismatch: `accelerator: List[int]` but `Resource` expects `List[str]` |
| `server/schemas.py` | 19 | Mutable default `depends: Dict = {}` shared across instances |
| `client/job.py` | 17 | Type hint says `List[Any]` but comment says "replaced by Job" |

### API Design Violations

| File | Line | Issue |
|------|------|-------|
| `server/routers/jobs.py` | 13-16 | Non-RESTful `/jobs/all` endpoint (redundant) |
| `server/routers/projects.py` | 26, 71, 82, 91 | Wrong resource names in error messages ("Job" instead of "Project") |
| `server/routers/tasks.py` | 35, 43 | Error messages say "Project" when getting tasks |

### Dead Code & Cruft

| File | Line | Issue |
|------|------|-------|
| `client/server.py` | 14-15 | Global mutable state `dummy_projects`, `dummy_jobs` |
| `client/server.py` | 32-95 | Large commented-out code blocks |
| `client/learn_requests.py` | 1-12 | Test/example code in production |
| `client/client.py` | 36-40 | Empty `append_artifact()`, `extend_artifacts()` methods |
| `server/routers/jobs.py` | 30-34 | Commented-out code block |
| `server/routers/tasks.py` | 59-61 | Empty `update_task()` endpoint |

### Architecture Issues

| File | Issue |
|------|-------|
| `client/job.py` | `Job.run()` mixes data object with execution logic - violates SRP |
| `client/project.py` | Thin wrapper delegating everything to `_server` - no domain logic |
| `client/server.py` | `ProjectConnector` mixes dummy data with HTTP calls inconsistently |
| `client/client.py` | Mixes resource management, artifacts, and formatting - unclear purpose |

---

## Status Quo vs Vision

| Feature | Vision | Current State | Gap |
|---------|--------|---------------|-----|
| Stateless client | All state on server | ✅ Design correct, but `dummy_projects`/`dummy_jobs` cruft remains | Cleanup needed |
| Formatter system | Convert params → commands | ❌ Empty stub classes | Full implementation needed |
| Worker loop | `client.work()` pulls continuously | ❌ Not implemented | New feature |
| Priority queuing | Higher priority first | ✅ Working | Done |
| Job dependencies | Jobs wait for dependencies | ⚠️ `depends` field exists, not enforced | Server-side logic needed |
| Resource tracking | CPU/GPU allocation | ⚠️ Classes exist, not functional | Implementation needed |
| Artifact management | Track job I/O | ❌ Stub only | Future phase |
| Queue operations | pop, extend, clear | ❌ Return "Not implemented" | Implementation needed |
| Security | Auth, CORS | ❌ None | Future phase |
| Tests | Comprehensive coverage | ❌ Mostly stubs | Ongoing |

---

## Phase 0: Critical Fixes (Blockers)

Fix issues that cause crashes or security vulnerabilities.

### 0.1 Security fixes
- [ ] Replace `os.system()` with `subprocess.run(shell=False)` in `client/job.py`
- [ ] Move database credentials to environment variables in `server/database.py`
- [ ] Add timeout to all `requests.*()` calls in `client/server.py`
- [ ] Remove debug `print()` statements from routers

### 0.2 Runtime error fixes
- [ ] Fix parameter `str` → `id` in `server/routers/projects.py:79`
- [ ] Fix undefined `id` variable in `server/routers/tasks.py:43`
- [ ] Add missing import in `client/task.py`
- [ ] Add return statement to `queue` property in `client/project.py`
- [ ] Fix response dict keys in `server/routers/projects.py:100`

### 0.3 Type fixes
- [ ] Fix `accelerator` type in `client/client.py`
- [ ] Fix mutable default `depends={}` in `server/schemas.py`

---

## Phase 1: Cleanup

Remove legacy code and establish clean foundation.

### 1.1 Remove dead code
- [ ] Delete `dummy_projects = {}` and `dummy_jobs = {}` from `client/server.py`
- [ ] Delete `client/learn_requests.py` (test code in production)
- [ ] Remove all commented-out code blocks
- [ ] Remove empty stub methods (`append_artifact`, `extend_artifacts`)
- [ ] Remove or implement empty `update_task()` endpoint

### 1.2 Fix API error messages
- [ ] Fix all "Job with" → "Project with" in `server/routers/projects.py`
- [ ] Fix all "Project with" → "Task with" in `server/routers/tasks.py`
- [ ] Remove redundant `/jobs/all` endpoint

### 1.3 Simplify ProjectConnector
- [ ] Remove all dummy data references
- [ ] Make all methods use HTTP calls consistently
- [ ] Or: Remove `ProjectConnector` entirely and inline into `Server` class

---

## Phase 2: Formatter System

Implement the runtime-agnostic job execution.

### 2.1 Define Formatter interface
```python
class Formatter(ABC):
    @abstractmethod
    def format(self, task: str, parameters: Dict[str, Any]) -> str:
        """Convert job parameters to executable command string."""
        pass

    @abstractmethod
    def execute(self, command: str) -> int:
        """Execute the formatted command. Returns exit code."""
        pass
```

### 2.2 Implement formatters
- [ ] `CLIFormatter`: Direct shell command execution
- [ ] `SlurmFormatter`: Generate and submit sbatch scripts
- [ ] `RUNAIFormatter`: Generate RUNAI job submissions
- [ ] `PythonFormatter`: Call Python functions directly (optional)

### 2.3 Template system
- [ ] Define command templates per task (e.g., `"python train.py --lr {lr} --epochs {epochs}"`)
- [ ] Store templates in Task model or client-side config
- [ ] Parameter substitution with validation

---

## Phase 3: Worker Loop

Enable continuous job pulling.

### 3.1 Implement `Client.work()` method
```python
def work(self, project: str, poll_interval: float = 5.0) -> None:
    """Continuously fetch and execute jobs until queue is empty."""
    while True:
        try:
            job = self.fetch_job(project)
            job.run(self.resource)
        except EmptyQueueError:
            break  # or sleep and retry
```

### 3.2 Features
- [ ] Configurable poll interval for waiting on new jobs
- [ ] Graceful shutdown on SIGINT/SIGTERM
- [ ] Option to run forever vs exit on empty queue
- [ ] Logging of job execution

### 3.3 Update `Job.run()`
- [ ] Use formatter from client/resource
- [ ] Proper subprocess handling (not `os.system`)
- [ ] Capture stdout/stderr
- [ ] Report execution time to server

---

## Phase 4: Queue Operations

Complete the queue management API.

### 4.1 Server endpoints
- [ ] `DELETE /projects/{id}/jobs/{job_id}` - Remove specific job
- [ ] `DELETE /projects/{id}/queue` - Clear all pending jobs
- [ ] `POST /projects/{id}/jobs/batch` - Add multiple jobs

### 4.2 Client methods
- [ ] `pop_queue(idx)` → Remove job by index
- [ ] `extend_queue(jobs)` → Add multiple jobs
- [ ] `remove_queue(job)` → Remove specific job
- [ ] `clear_queue()` → Clear all pending jobs

---

## Phase 5: Job Dependencies

Enforce job execution order.

### 5.1 Server-side dependency resolution
- [ ] `fetch_job` only returns jobs whose dependencies are COMPLETED
- [ ] Track dependency graph
- [ ] Detect circular dependencies on job creation

### 5.2 Dependency status propagation
- [ ] If dependency FAILED, mark dependent jobs as BLOCKED or FAILED
- [ ] API to query job dependency status

---

## Phase 6: Resource Management

Track and enforce resource allocation.

### 6.1 Resource model improvements
- [ ] Define resource requirements per task
- [ ] Track available vs allocated resources per client
- [ ] `fetch_job` can filter by resource availability

### 6.2 Client resource registration
- [ ] Client reports available resources on connect
- [ ] Server tracks which client has which resources

---

## Phase 7: Testing & Documentation

### 7.1 Tests
- [ ] Unit tests for formatters
- [ ] Unit tests for client methods
- [ ] Integration tests for full job lifecycle
- [ ] Server endpoint tests

### 7.2 Documentation
- [ ] Quickstart guide with real examples
- [ ] Formatter configuration guide
- [ ] API reference (auto-generated from docstrings)
- [ ] Deployment guide

---

## Phase 8: Deployment & Security

For external/public-facing servers.

### 8.1 Basic deployment (systemd)
- [x] Document systemd service setup
- [x] Add example `whatsnext.service` file to repo (`deploy/`)
- [x] Add deployment README (`deploy/README.md`)

### 8.2 HTTPS with reverse proxy
- [x] Document nginx/caddy setup for HTTPS termination
- [x] Add example nginx config to repo (`deploy/nginx.conf`)

### 8.3 Authentication
- [ ] API key authentication for clients
- [ ] Environment variable for API key(s)
- [ ] Middleware to validate requests

### 8.4 Rate limiting & CORS
- [ ] Add CORS middleware for allowed origins
- [ ] Basic rate limiting to prevent abuse

---

## Future Phases (Not Planned Yet)

- **User Roles**: Multi-user with permissions
- **Artifact Management**: Track job inputs/outputs, file storage
- **Web Dashboard**: Monitor jobs, projects, queue status
- **Metrics & Monitoring**: Prometheus integration, job duration tracking

---

## Immediate Next Steps

1. **Phase 0**: Fix all critical/blocking issues first
2. **Phase 1**: Clean up dead code and cruft
3. **Phase 2**: Implement CLIFormatter as MVP
4. **Phase 3**: Basic worker loop

This gets a minimal working system where a client can continuously pull and execute jobs.
