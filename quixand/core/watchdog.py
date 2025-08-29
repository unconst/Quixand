from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timedelta, timezone

from ..config import Config
from ..utils.docker_utils import docker_stop, docker_rm


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
			last_active_at = datetime.utcnow()
		timeout_seconds = int(entry.get("timeout_seconds", 300))
		now = datetime.utcnow()
		deadline = last_active_at + timedelta(seconds=timeout_seconds)
		# If idle or lifetime exceeded
		if now >= deadline:
			runtime = entry.get("runtime", "docker")
			container_id = entry.get("container_id")
			if container_id:
				try:
					docker_stop(runtime, container_id)
					docker_rm(runtime, container_id)
				except Exception:
					pass
			# Remove from state
			try:
				state.pop(sbx_id, None)
				Config.state_file().write_text(json.dumps(state, indent=2))
			except Exception:
				pass
			return 0
		time.sleep(1.0)


if __name__ == "__main__":
	sys.exit(main())


