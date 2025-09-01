from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timedelta, timezone
import shutil
from pathlib import Path

from ..config import Config
from ..utils.docker_utils import docker_stop, docker_rm, docker_container_exists


def _load_state() -> dict:
	try:
		return json.loads(Config.state_file().read_text())
	except Exception:
		return {}


def main() -> int:
	if len(sys.argv) < 2:
		return 2
	sbx_id = sys.argv[1]
	# Poll state until sandbox is removed or timed out
	while True:
		state = _load_state()
		entry = state.get(sbx_id)
		if not entry:
			return 0
		try:
			created_at = datetime.fromisoformat(entry["created_at"])  # naive -> treat as UTC
		except Exception:
			created_at = datetime.utcnow()
		try:
			last_active_at = datetime.fromisoformat(entry["last_active_at"])  # naive -> treat as UTC
		except Exception:
			# If state is corrupted or missing last_active_at, fall back to created_at
			# rather than "now" to avoid extending lifetime indefinitely.
			last_active_at = created_at
		timeout_seconds = int(entry.get("timeout_seconds", 300))
		now = datetime.utcnow()
		deadline = last_active_at + timedelta(seconds=timeout_seconds)
		# Apply a hard lifetime cap to prevent a watchdog from running forever
		# in case last_active_at parsing keeps failing or state drifts.
		lifetime_deadline = created_at + timedelta(seconds=max(timeout_seconds * 2, timeout_seconds + 60))
		# If idle or lifetime exceeded
		if now >= deadline or now >= lifetime_deadline:
			runtime = entry.get("runtime", "docker")
			container_id = entry.get("container_id")
			if container_id:
				try:
					docker_stop(runtime, container_id)
					docker_rm(runtime, container_id)
				except Exception:
					pass
			# Best-effort cleanup of host-mounted dirs for this sandbox
			try:
				base = Config.state_file().parent
				for rel in ("scratch", "volumes"):
					shutil.rmtree(str(base / rel / sbx_id), ignore_errors=True)
			except Exception:
				pass
			# Remove from state
			try:
				state.pop(sbx_id, None)
				Config.state_file().write_text(json.dumps(state, indent=2))
			except Exception:
				pass
			return 0
		# If container does not exist anymore, exit and clean state quickly
		runtime = entry.get("runtime", "docker")
		container_id = entry.get("container_id")
		if container_id and not docker_container_exists(runtime, container_id):
			try:
				state.pop(sbx_id, None)
				Config.state_file().write_text(json.dumps(state, indent=2))
			except Exception:
				pass
			# Also cleanup host-mounted dirs
			try:
				base = Config.state_file().parent
				for rel in ("scratch", "volumes"):
					shutil.rmtree(str(base / rel / sbx_id), ignore_errors=True)
			except Exception:
				pass
			return 0
		time.sleep(1.0)


if __name__ == "__main__":
	sys.exit(main())


