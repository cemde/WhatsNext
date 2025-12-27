# Implementation Plan: WhatsNext

This document compares the current state to the vision and outlines the path forward.

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

## Phase 1: Cleanup

Remove legacy code and establish clean foundation.

### 1.1 Remove dummy data stores
- [ ] Delete `dummy_projects = {}` and `dummy_jobs = {}` from `client/server.py`
- [ ] Remove all references to dummy stores in `ProjectConnector`
- [ ] Update `get_queue()` to use HTTP call instead of dummy data

### 1.2 Fix incomplete HTTP implementations
- [ ] `ProjectConnector.get_last_updated()` → HTTP call
- [ ] `ProjectConnector.get_description()` → HTTP call
- [ ] `ProjectConnector.get_status()` → HTTP call
- [ ] `ProjectConnector.get_created_at()` → HTTP call
- [ ] `ProjectConnector.set_name()` → HTTP call
- [ ] `ProjectConnector.set_status()` → HTTP call

### 1.3 Code quality fixes
- [ ] Fix typo in `server/routers/projects.py:79` (`delete_project(str, ...)`)
- [ ] Consistent error handling across all HTTP calls
- [ ] Remove commented-out code blocks

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

## Future Phases (Not Planned Yet)

- **Authentication & Authorization**: Protected routes, API keys, user roles
- **CORS Configuration**: For web-based clients
- **Artifact Management**: Track job inputs/outputs, file storage
- **Web Dashboard**: Monitor jobs, projects, queue status
- **Metrics & Monitoring**: Prometheus integration, job duration tracking

---

## Immediate Next Steps

1. **Phase 1.1**: Remove dummy data stores (30 min)
2. **Phase 1.2**: Fix HTTP implementations (1-2 hours)
3. **Phase 2.1-2.2**: Implement CLIFormatter as MVP (2-3 hours)
4. **Phase 3.1**: Basic worker loop (1-2 hours)

This gets a minimal working system where a client can continuously pull and execute jobs.
