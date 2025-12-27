from __future__ import annotations

import logging
import signal
import time
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from .exceptions import EmptyQueueError
from .formatter import Formatter
from .resource import Resource
from .utils import random_string

if TYPE_CHECKING:
    from .project import Project

logger = logging.getLogger(__name__)


class Client:
    """Represents a worker client that executes jobs.

    A Client manages resources (CPU/GPU) and uses a formatter to convert
    job parameters into executable commands.
    """

    def __init__(
        self,
        entity: str,
        name: str,
        description: str,
        project: "Project",
        formatter: Formatter,
        available_cpu: int = 1,
        available_accelerators: int = 0,
        register_with_server: bool = True,
    ) -> None:
        self.id = random_string()
        self.entity = entity
        self.name = name
        self.project = project
        self.description = description
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.formatter = formatter
        self.active_resources: List[Resource] = []
        self._shutdown_requested = False
        self.available_cpu = available_cpu
        self.available_accelerators = available_accelerators
        self._registered = False

        if register_with_server:
            self._register()

    def _register(self) -> None:
        """Register the client with the server."""
        server = self.project._server
        if server is None:
            logger.warning("Cannot register client: project is not bound to a server")
            return

        success = server.register_client(
            client_id=self.id,
            name=self.name,
            entity=self.entity,
            description=self.description,
            available_cpu=self.available_cpu,
            available_accelerators=self.available_accelerators,
        )
        if success:
            self._registered = True
            logger.info(f"Client {self.id} registered with server")
        else:
            logger.warning(f"Failed to register client {self.id} with server")

    def _deactivate(self) -> None:
        """Deactivate the client on the server."""
        server = self.project._server
        if self._registered and server is not None:
            server.deactivate_client(self.id)
            self._registered = False

    def allocate_resource(self, cpu: int, accelerator: List[str]) -> Resource:
        """Allocate a resource for job execution.

        Args:
            cpu: Number of CPUs to allocate.
            accelerator: List of accelerator device IDs (e.g., ["0", "1"] for GPUs).

        Returns:
            The allocated Resource.
        """
        resource = Resource(cpu, accelerator, self)
        self.active_resources.append(resource)
        return resource

    def free_resource(self, resource: Resource) -> None:
        """Release a previously allocated resource."""
        self.active_resources.remove(resource)

    def _signal_handler(self, signum: int, frame) -> None:
        """Handle shutdown signals gracefully."""
        signal_name = signal.Signals(signum).name
        logger.info(f"Received {signal_name}, initiating graceful shutdown...")
        self._shutdown_requested = True

    def work(
        self,
        resource: Optional[Resource] = None,
        poll_interval: float = 5.0,
        run_forever: bool = False,
        use_resource_filter: bool = True,
    ) -> int:
        """Continuously fetch and execute jobs until queue is empty.

        Args:
            resource: Resource to use for job execution. If None, allocates
                a default resource with 1 CPU and no accelerators.
            poll_interval: Seconds to wait between polling when run_forever=True.
            run_forever: If True, wait for new jobs instead of exiting on empty queue.
            use_resource_filter: If True, only fetch jobs that match client's resources.

        Returns:
            Number of jobs executed.
        """
        # Set up signal handlers for graceful shutdown
        original_sigint = signal.signal(signal.SIGINT, self._signal_handler)
        original_sigterm = signal.signal(signal.SIGTERM, self._signal_handler)

        # Allocate default resource if none provided
        if resource is None:
            resource = self.allocate_resource(cpu=1, accelerator=[])

        jobs_executed = 0
        self._shutdown_requested = False

        logger.info(f"Worker started for project {self.project.id}")

        try:
            while not self._shutdown_requested:
                try:
                    # Fetch job with resource filtering if enabled
                    if use_resource_filter:
                        job = self.project.fetch_job(
                            available_cpu=self.available_cpu,
                            available_accelerators=self.available_accelerators,
                        )
                    else:
                        job = self.project.fetch_job()
                    logger.info(f"Fetched job {job.id}: {job.name}")
                    exit_code = job.run(resource)
                    jobs_executed += 1
                    if exit_code == 0:
                        logger.info(f"Job {job.id} completed successfully")
                    else:
                        logger.warning(f"Job {job.id} failed with exit code {exit_code}")
                except EmptyQueueError:
                    if run_forever:
                        logger.debug(f"Queue empty, waiting {poll_interval}s...")
                        time.sleep(poll_interval)
                    else:
                        logger.info("Queue empty, worker exiting")
                        break
                except Exception as e:
                    logger.exception(f"Error processing job: {e}")
                    if not run_forever:
                        break
        finally:
            # Restore original signal handlers
            signal.signal(signal.SIGINT, original_sigint)
            signal.signal(signal.SIGTERM, original_sigterm)

            # Mark resource as inactive
            resource.set_status("inactive")

            # Deactivate client on server
            self._deactivate()

            logger.info(f"Worker finished. Executed {jobs_executed} jobs.")

        return jobs_executed

    def stop(self) -> None:
        """Request the worker to stop gracefully."""
        self._shutdown_requested = True
