from __future__ import annotations

import os
import shutil
import subprocess
from typing import Optional

import pytest


def _runtime_is_usable(candidate: str) -> bool:
    try:
        subprocess.run([candidate, "ps"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, timeout=5)
        return True
    except Exception:
        return False


def get_available_runtime() -> Optional[str]:
    for name in ("docker", "podman"):
        if shutil.which(name) and _runtime_is_usable(name):
            return name
    return None


def require_container_runtime() -> str:
    runtime = get_available_runtime()
    if not runtime:
        pytest.skip("Container runtime (docker/podman) not available or not running")
    return runtime


@pytest.fixture()
def sbx():
    import quixand as qs

    require_container_runtime()
    sandbox = qs.Sandbox(template="python:3.11-slim", timeout=300, metadata={"test": "true"})
    try:
        yield sandbox
    finally:
        try:
            sandbox.shutdown()
        except Exception:
            pass


