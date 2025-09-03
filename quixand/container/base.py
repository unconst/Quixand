"""Base classes and data structures for container runtime abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum


class ContainerState(Enum):
    """Container state enumeration."""
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    EXITED = "exited"
    DEAD = "dead"
    REMOVING = "removing"
    ERROR = "error"


@dataclass
class ResourceLimits:
    """Resource limits for container."""
    cpu_limit: Optional[float] = None  # CPU cores (e.g., 1.5)
    memory_limit: Optional[str] = None  # Memory limit (e.g., "512m", "2g")
    pids_limit: Optional[int] = None  # Maximum number of PIDs
    network_mode: str = "bridge"  # Network mode: bridge, host, none


@dataclass
class VolumeMount:
    """Volume mount configuration."""
    source: str  # Host path or volume name
    target: str  # Container path
    read_only: bool = False
    type: str = "bind"  # bind or volume


@dataclass
class ContainerConfig:
    """Configuration for creating a container."""
    name: str
    image: str
    workdir: str = "/workspace"
    env: Dict[str, str] = field(default_factory=dict)
    volumes: List[VolumeMount] = field(default_factory=list)
    resources: Optional[ResourceLimits] = None
    entrypoint: Optional[List[str]] = None
    command: Optional[List[str]] = None
    labels: Dict[str, str] = field(default_factory=dict)
    ports: Dict[str, int] = field(default_factory=dict)  # container_port: host_port


@dataclass
class ContainerInfo:
    """Information about a container."""
    id: str
    name: str
    state: ContainerState
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    exit_code: Optional[int] = None
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class ExecConfig:
    """Configuration for executing command in container."""
    command: List[str]
    env: Optional[Dict[str, str]] = None
    workdir: Optional[str] = None
    user: Optional[str] = None
    privileged: bool = False
    tty: bool = False
    stdin: bool = False
    detach: bool = False


@dataclass  
class ExecResult:
    """Result of command execution in container."""
    exit_code: int
    stdout: bytes
    stderr: bytes
    duration_seconds: float


@dataclass
class CopyConfig:
    """Configuration for copying files to/from container."""
    container_path: str
    host_path: str
    to_container: bool = True  # True: host->container, False: container->host


class ContainerRuntime(ABC):
    """Abstract base class for container runtime operations."""

    @abstractmethod
    def create_container(self, config: ContainerConfig) -> str:
        """Create a new container and return its ID."""
        pass

    @abstractmethod
    def start_container(self, container_id: str) -> None:
        """Start a created container."""
        pass

    @abstractmethod
    def stop_container(self, container_id: str, timeout: int = 10) -> None:
        """Stop a running container."""
        pass

    @abstractmethod
    def remove_container(self, container_id: str, force: bool = False) -> None:
        """Remove a container."""
        pass

    @abstractmethod
    def get_container_info(self, container_id: str) -> ContainerInfo:
        """Get information about a container."""
        pass

    @abstractmethod
    def container_exists(self, container_id: str) -> bool:
        """Check if container exists."""
        pass

    @abstractmethod
    def exec_in_container(
        self,
        container_id: str,
        config: ExecConfig,
        timeout: Optional[int] = None
    ) -> ExecResult:
        """Execute a command in a running container."""
        pass

    @abstractmethod
    def copy_to_container(
        self,
        container_id: str,
        source: str,
        dest: str
    ) -> None:
        """Copy file or directory from host to container."""
        pass

    @abstractmethod
    def copy_from_container(
        self,
        container_id: str,
        source: str,
        dest: str
    ) -> None:
        """Copy file or directory from container to host."""
        pass

    @abstractmethod
    def list_containers(self, all: bool = False) -> List[ContainerInfo]:
        """List containers."""
        pass

    @abstractmethod
    def get_container_logs(
        self,
        container_id: str,
        stdout: bool = True,
        stderr: bool = True,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        tail: Optional[int] = None
    ) -> str:
        """Get container logs."""
        pass

    @abstractmethod
    def wait_container(self, container_id: str, timeout: Optional[int] = None) -> int:
        """Wait for container to stop and return exit code."""
        pass