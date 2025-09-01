from __future__ import annotations

import os
import shlex
import shutil
import subprocess
from dataclasses import dataclass
from typing import Dict, List, Optional


def detect_runtime(preferred: Optional[str] = None) -> str:
	if preferred in {"docker", "podman"}:
		return preferred
	for candidate in ("docker", "podman"):
		if shutil.which(candidate):
			return candidate
	return "docker"


def run_cli(cmd: List[str], env: Optional[Dict[str, str]] = None, check: bool = True, timeout: Optional[int] = None) -> subprocess.CompletedProcess:
	merged_env = os.environ.copy()
	if env:
		merged_env.update(env)
	proc = subprocess.run(cmd, env=merged_env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
	if check and proc.returncode != 0:
		raise subprocess.CalledProcessError(proc.returncode, cmd, output=proc.stdout, stderr=proc.stderr)
	return proc


def docker_cp(runtime: str, src: str, dst: str) -> None:
	run_cli([runtime, "cp", src, dst])


def docker_exec(runtime: str, container: str, args: List[str], timeout: Optional[int] = None) -> subprocess.CompletedProcess:
	return run_cli([runtime, "exec", container] + args, timeout=timeout)


def docker_exec_capture(runtime: str, container: str, args: List[str], timeout: Optional[int] = None) -> subprocess.CompletedProcess:
	return run_cli([runtime, "exec", container] + args, check=False, timeout=timeout)


def docker_run_detached(runtime: str, args: List[str]) -> str:
	proc = run_cli([runtime, "run", "-d"] + args)
	return proc.stdout.decode("utf-8").strip()


def docker_stop(runtime: str, container: str) -> None:
	# Bound the stop call so watchdogs can't hang forever if the runtime is stuck.
	timeout_s = int(os.getenv("QS_DOCKER_STOP_TIMEOUT", "15"))
	run_cli([runtime, "stop", container], check=False, timeout=timeout_s)


def docker_rm(runtime: str, container: str) -> None:
	# Bound the rm call to avoid stranded watchdogs.
	timeout_s = int(os.getenv("QS_DOCKER_RM_TIMEOUT", "15"))
	run_cli([runtime, "rm", "-f", container], check=False, timeout=timeout_s)


def docker_container_exists(runtime: str, container: str) -> bool:
	"""Return True if the container exists (running or stopped)."""
	timeout_s = int(os.getenv("QS_DOCKER_INSPECT_TIMEOUT", "5"))
	proc = run_cli([runtime, "inspect", container], check=False, timeout=timeout_s)
	return proc.returncode == 0

