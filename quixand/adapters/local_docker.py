from __future__ import annotations

import json
import os
import shlex
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable, Optional
import shutil

from ..config import Config
from ..errors import QSAdapterError, QSSandboxNotFound, QSTimeout
from ..types import CommandResult, Execution, FileInfo, PTYHandle, SandboxHandle, SandboxStatus
from ..utils.docker_utils import (
	docker_cp,
	docker_exec,
	docker_exec_capture,
	docker_rm,
	docker_run_detached,
	docker_stop,
	detect_runtime,
	run_cli,
)
from ..utils.fs import atomic_write_text
from .base import SandboxConfig
from ..core import watchdog as watchdog_module
import subprocess, sys


@dataclass
class LocalHandle(SandboxHandle):
	container_id: str
	id: str
	runtime: str
	workdir: str
	created_at: datetime
	last_active_at: datetime
	timeout_seconds: int
	metadata: dict


class LocalPTY(PTYHandle):
	def __init__(self):
		self._closed = True


class LocalDockerAdapter:
	name = "local-docker"

	def __init__(self, cfg: Optional[Config] = None):
		self.cfg = cfg or Config()
		self.runtime = detect_runtime(self.cfg.runtime)

	# lifecycle
	def create(self, cfg: "SandboxConfig") -> LocalHandle:
		sbx_id = str(uuid.uuid4())
		container_name = f"qs_{sbx_id[:8]}"

		args = [
			"--name",
			container_name,
			"--workdir",
			cfg.workdir,
			"-e",
			"PYTHONUNBUFFERED=1",
			"-e",
			"PYTHONDONTWRITEBYTECODE=1",
			"-v",
			f"{self._ensure_volume_dir(sbx_id)}:{cfg.workdir}",
		]

		for k, v in (cfg.env or {}).items():
			args += ["-e", f"{k}={v}"]

		if cfg.resources and cfg.resources.network == "none":
			args += ["--network", "none"]

		if cfg.resources and cfg.resources.mem_limit:
			args += ["--memory", cfg.resources.mem_limit]
		if cfg.resources and cfg.resources.pids_limit:
			args += ["--pids-limit", str(cfg.resources.pids_limit)]
		if cfg.resources and cfg.resources.cpu_limit:
			# docker expects --cpus for fractional
			args += ["--cpus", str(cfg.resources.cpu_limit)]

		image = cfg.image
		# Force a neutral entrypoint to ensure long-lived container even if image sets ENTRYPOINT
		# Use /bin/sh -c "sleep infinity" to avoid images where bash is not present or ENTRYPOINT interferes
		args += ["--entrypoint", "/bin/sh"]
		args += [image, "-c", "sleep infinity"]

		container_id = docker_run_detached(self.runtime, args)
		h = LocalHandle(
			container_id=container_id,
			id=sbx_id,
			runtime=self.runtime,
			workdir=cfg.workdir,
			created_at=datetime.utcnow(),
			last_active_at=datetime.utcnow(),
			timeout_seconds=cfg.timeout,
			metadata=cfg.metadata or {},
		)
		self._persist_handle(h)
		# Spawn watchdog in background, fully detached from this process/TTY
		if os.getenv("QS_DISABLE_WATCHDOG") not in {"1", "true", "TRUE", "True"}:
			try:
				interpreter = sys.executable or "python"
				subprocess.Popen(
					[interpreter, "-m", "quixand.core.watchdog", h.id],
					stdin=subprocess.DEVNULL,
					stdout=subprocess.DEVNULL,
					stderr=subprocess.DEVNULL,
					start_new_session=True,
				)
			except Exception:
				pass
		return h

	def connect(self, sandbox_id: str) -> LocalHandle:
		state = self._load_state()
		entry = state.get(sandbox_id)
		if not entry:
			raise QSSandboxNotFound(f"Sandbox {sandbox_id} not found")
		return LocalHandle(
			container_id=entry["container_id"],
			id=sandbox_id,
			runtime=entry["runtime"],
			workdir=entry["workdir"],
			created_at=datetime.fromisoformat(entry["created_at"]),
			last_active_at=datetime.fromisoformat(entry["last_active_at"]),
			timeout_seconds=entry["timeout_seconds"],
			metadata=entry.get("metadata", {}),
		)

	def shutdown(self, h: LocalHandle) -> None:
		docker_stop(self.runtime, h.container_id)
		docker_rm(self.runtime, h.container_id)
		self._remove_state(h.id)
		# Best-effort cleanup of host-mounted dirs for this sandbox
		self._cleanup_host_dirs(h.id)

	def status(self, h: LocalHandle) -> SandboxStatus:
		# Inspect the container to determine actual state
		container_state = "error"
		try:
			proc = run_cli([self.runtime, "inspect", h.container_id], check=False)
			if proc.returncode == 0:
				try:
					info = json.loads(proc.stdout.decode("utf-8", "ignore"))
					if isinstance(info, list) and info:
						status_str = (
							info[0].get("State", {}).get("Status") or ""
						).lower()
						# Map Docker status to SandboxState
						if status_str in {"running", "paused"}:
							container_state = "running"
						elif status_str in {"created"}:
							container_state = "creating"
						elif status_str in {"restarting", "removing"}:
							container_state = "stopping"
						elif status_str in {"exited", "dead"}:
							container_state = "stopped"
						else:
							container_state = "error"
					else:
						container_state = "error"
				except Exception:
					container_state = "error"
			else:
				container_state = "error"
		except Exception:
			container_state = "error"

		deadline = h.last_active_at + timedelta(seconds=h.timeout_seconds)
		return SandboxStatus(
			state=container_state, created_at=h.created_at, last_active_at=h.last_active_at, timeout_at=deadline, metadata=h.metadata
		)

	def refresh_timeout(self, h: LocalHandle, seconds: int) -> None:
		h.timeout_seconds = seconds
		h.last_active_at = datetime.utcnow()
		self._persist_handle(h)

	# filesystem
	def fs_write(self, h: LocalHandle, path: str, data: bytes, text: bool) -> None:
		local = self._scratch(h, "put.tmp")
		local.write_bytes(data if not text else data.decode("utf-8").encode("utf-8"))
		docker_cp(self.runtime, str(local), f"{h.container_id}:{self._abs(h, path)}")
		h.last_active_at = datetime.utcnow()
		self._persist_handle(h)

	def fs_read(self, h: LocalHandle, path: str, text: bool) -> bytes | str:
		local = self._scratch(h, "get.tmp")
		docker_cp(self.runtime, f"{h.container_id}:{self._abs(h, path)}", str(local))
		data = local.read_bytes()
		h.last_active_at = datetime.utcnow()
		self._persist_handle(h)
		return data.decode("utf-8", "ignore") if text else data

	def fs_ls(self, h: LocalHandle, path: str) -> list[FileInfo]:
		res = docker_exec_capture(self.runtime, h.container_id, ["sh", "-lc", f"ls -la --time-style=+%s {shlex.quote(self._abs(h, path))}"])
		out = res.stdout.decode("utf-8", "ignore")
		files: list[FileInfo] = []
		for line in out.splitlines()[1:]:
			parts = line.split()
			if len(parts) < 7:
				continue
			size = int(parts[4]) if parts[4].isdigit() else 0
			mtime = None
			try:
				mtime = datetime.utcfromtimestamp(int(parts[5]))
			except Exception:
				mtime = None
			name = parts[-1]
			is_dir = line.startswith("d")
			files.append(FileInfo(path=name, size=size, is_dir=is_dir, modified_at=mtime))
		return files

	def fs_mkdir(self, h: LocalHandle, path: str, parents: bool) -> None:
		flag = "-p" if parents else ""
		docker_exec(self.runtime, h.container_id, ["sh", "-lc", f"mkdir {flag} {shlex.quote(self._abs(h, path))}"])
		h.last_active_at = datetime.utcnow()
		self._persist_handle(h)

	def fs_rm(self, h: LocalHandle, path: str, recursive: bool) -> None:
		flag = "-r" if recursive else ""
		docker_exec(self.runtime, h.container_id, ["sh", "-lc", f"rm {flag} -f {shlex.quote(self._abs(h, path))}"])
		h.last_active_at = datetime.utcnow()
		self._persist_handle(h)

	def fs_mv(self, h: LocalHandle, src: str, dst: str) -> None:
		docker_exec(self.runtime, h.container_id, ["sh", "-lc", f"mv {shlex.quote(self._abs(h, src))} {shlex.quote(self._abs(h, dst))}"])
		h.last_active_at = datetime.utcnow()
		self._persist_handle(h)

	def fs_put(self, h: LocalHandle, local: str, remote: str) -> None:
		docker_cp(self.runtime, local, f"{h.container_id}:{self._abs(h, remote)}")
		h.last_active_at = datetime.utcnow()
		self._persist_handle(h)

	def fs_get(self, h: LocalHandle, remote: str, local: str) -> None:
		docker_cp(self.runtime, f"{h.container_id}:{self._abs(h, remote)}", local)
		h.last_active_at = datetime.utcnow()
		self._persist_handle(h)

	# processes
	def run(self, h: LocalHandle, cmd: list[str] | str, env: Optional[dict], timeout: Optional[int]) -> CommandResult:
		cmd_str = shlex.join(cmd) if isinstance(cmd, list) else cmd
		if env:
			prefix = " ".join(f"{k}={shlex.quote(str(v))}" for k, v in env.items())
			cmd_str = f"{prefix} {cmd_str}"
		args = ["sh", "-lc", cmd_str]
		start = time.monotonic()
		try:
			res = docker_exec_capture(self.runtime, h.container_id, args, timeout=timeout)
		except Exception as e:
			import subprocess
			if isinstance(e, subprocess.TimeoutExpired):
				raise QSTimeout(f"Command timed out after {timeout}s")
			raise
		duration = time.monotonic() - start
		stdout = res.stdout
		stderr = res.stderr
		exit_code = res.returncode
		text = stdout.decode("utf-8", "ignore")
		h.last_active_at = datetime.utcnow()
		self._persist_handle(h)
		return CommandResult(text=text, stdout=stdout, stderr=stderr, exit_code=exit_code, duration_s=duration)

	def pty_start(self, h: LocalHandle, cmd: str, env: Optional[dict]) -> PTYHandle:  # TODO: implement true PTY
		return LocalPTY()

	def pty_send(self, pty: PTYHandle, data: bytes) -> None:  # TODO
		pass

	def pty_stream(self, pty: PTYHandle) -> Iterable[bytes]:  # TODO
		if False:
			yield b""
		return

	def pty_close(self, pty: PTYHandle) -> None:  # TODO
		pass

	# code conveniences
	def run_code(self, h: LocalHandle, code: str) -> Execution:
		code_path = self._abs(h, ".qs_exec.py")
		self.fs_write(h, code_path, code.encode("utf-8"), text=False)
		res = self.run(h, ["python", code_path], env=None, timeout=None)
		ok = res.exit_code == 0
		return Execution(text=res.text, images=None, files=None, stderr=res.stderr.decode("utf-8", "ignore"), ok=ok)

	def install_pkg(self, h: LocalHandle, spec: str) -> CommandResult:
		return self.run(h, ["python", "-m", "pip", "install", "--no-input", spec], env=None, timeout=None)

	def expose(self, h: LocalHandle, port: int, host_port: Optional[int], proto: str):  # TODO
		return {"container_port": port, "host_port": host_port or port, "proto": proto}

	# helpers
	def _abs(self, h: LocalHandle, path: str) -> str:
		p = Path(path)
		return str(p if p.is_absolute() else Path(h.workdir) / p)

	def _scratch(self, h: LocalHandle, name: str) -> Path:
		p = Config.state_file().parent / "scratch" / h.id
		p.mkdir(parents=True, exist_ok=True)
		return p / name

	def _ensure_volume_dir(self, sbx_id: str) -> str:
		p = Config.state_file().parent / "volumes" / sbx_id
		p.mkdir(parents=True, exist_ok=True)
		return str(p)

	def _cleanup_host_dirs(self, sbx_id: str) -> None:
		base = Config.state_file().parent
		for rel in ("scratch", "volumes"):
			try:
				shutil.rmtree(str(base / rel / sbx_id), ignore_errors=True)
			except Exception:
				pass

	def _load_state(self) -> dict:
		if not Config.state_file().exists():
			return {}
		try:
			return json.loads(Config.state_file().read_text())
		except Exception:
			return {}

	def _persist_handle(self, h: LocalHandle) -> None:
		state = self._load_state()
		state[h.id] = {
			"container_id": h.container_id,
			"runtime": h.runtime,
			"workdir": h.workdir,
			"created_at": h.created_at.isoformat(),
			"last_active_at": h.last_active_at.isoformat(),
			"timeout_seconds": h.timeout_seconds,
			"metadata": h.metadata,
			"adapter": self.name,
		}
		atomic_write_text(Config.state_file(), json.dumps(state, indent=2))

	def _remove_state(self, sandbox_id: str) -> None:
		state = self._load_state()
		state.pop(sandbox_id, None)
		atomic_write_text(Config.state_file(), json.dumps(state, indent=2))


