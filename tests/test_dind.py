from __future__ import annotations

import os
import shutil
import subprocess
import pytest


def _inside_container() -> bool:
	# Heuristics: /.dockerenv or cgroup markers
	if os.path.exists("/.dockerenv"):
		return True
	try:
		with open("/proc/1/cgroup", "rt") as f:
			data = f.read()
		return any(k in data for k in ("docker", "containerd", "kubepods"))
	except Exception:
		return False


def _docker_cli_works() -> bool:
	if not shutil.which("docker"):
		return False
	try:
		subprocess.run(["docker", "ps"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, timeout=5)
		return True
	except Exception:
		return False


@pytest.mark.timeout(60)
def test_dind_prerequisites_or_skip():
	if not _inside_container():
		pytest.skip("Not running inside a container; DinD test skipped")
	if not shutil.which("docker"):
		pytest.skip("docker CLI is not installed in this container")
	if not os.path.exists("/var/run/docker.sock"):
		pytest.skip("/var/run/docker.sock is not mounted into this container")
	if not _docker_cli_works():
		pytest.skip("docker CLI cannot talk to daemon via docker.sock")


@pytest.mark.timeout(120)
def test_quixand_inside_container_can_spawn_child():
	if not _inside_container():
		pytest.skip("Not running inside a container; DinD test skipped")
	if not _docker_cli_works():
		pytest.skip("docker CLI unavailable or cannot reach daemon")

	import quixand as qs
	image = os.getenv("QS_IMAGE", "python:3.11-slim")
	sbx = qs.Sandbox(template=image, timeout=60)
	try:
		res = sbx.run(["python", "-c", "print(2+2)"])
		assert res.exit_code == 0
		assert res.text.strip() == "4"
	finally:
		try:
			sbx.shutdown()
		except Exception:
			pass
