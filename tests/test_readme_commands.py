from __future__ import annotations

import asyncio
import os
from pathlib import Path
import shutil
import subprocess
import pytest


def test_top_level_imports_and_config():
    import quicksand as qs

    # Top-level imports
    assert hasattr(qs, "Sandbox")
    assert hasattr(qs, "AsyncSandbox")
    assert hasattr(qs, "connect")
    assert hasattr(qs, "Templates")

    # Programmatic config
    cfg = qs.Config(timeout=600, image="python:3.11-slim")
    assert cfg.timeout == 600
    assert cfg.image == "python:3.11-slim"


def test_sync_sandbox_basic(sbx):
    # Files
    sbx.files.write("hello.txt", "hi!")
    paths = [f.path for f in sbx.files.ls(".")]
    assert "hello.txt" in paths

    # Process execution
    res = sbx.run(["python", "-c", "print(2+2)"])
    assert res.exit_code == 0
    assert res.text.strip() == "4"

    # Python code convenience
    execn = sbx.run_code("x=1\nx+=1\nprint(x)")
    assert execn.ok is True
    assert execn.text.strip() == "2"


def _runtime_available() -> bool:
    for name in ("docker", "podman"):
        if shutil.which(name):
            try:
                subprocess.run([name, "ps"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, timeout=5)
                return True
            except Exception:
                continue
    return False


def test_async_sandbox_run_and_shutdown():
    if not _runtime_available():
        pytest.skip("Container runtime (docker/podman) not available or not running")
    import quicksand as qs

    async def _inner():
        sbx = await qs.AsyncSandbox.create(template="python:3.11-slim")
        try:
            tmp_local = Path(qs.Config.state_file().parent) / "tmp_async_put.txt"
            tmp_local.write_text("data")
            # Avoid blocking event loop
            await asyncio.to_thread(sbx.files.put, str(tmp_local), "/workspace/data.txt")

            res = await sbx.run(["python", "-c", "print(42)"])
            assert res.exit_code == 0
            assert res.text.strip() == "42"
        finally:
            await sbx.shutdown()

    asyncio.run(_inner())


def test_connect_to_running_sandbox(sbx):
    import quicksand as qs

    sid = sbx.id
    sbx2 = qs.connect(sid)
    st = sbx2.status()
    assert st.state in {"running", "creating", "stopped", "stopping", "error"}


def test_filesystem_api_text_and_binary_and_glob(sbx, tmp_path):
    # text
    sbx.files.write("/workspace/notes.txt", "hello")
    # binary
    sbx.files.write("/workspace/blob.bin", b"\x00\x01", mode="binary")
    assert sbx.files.read("/workspace/notes.txt") == "hello"
    assert sbx.files.read("/workspace/blob.bin", mode="binary") == b"\x00\x01"

    sbx.files.mkdir("/workspace/data", parents=True)

    # put/get
    local_src = tmp_path / "local.txt"
    local_src.write_text("hey")
    sbx.files.put(str(local_src), "/workspace/local.txt")
    local_dst = tmp_path / "local_copy.txt"
    sbx.files.get("/workspace/local.txt", str(local_dst))
    assert local_dst.read_text() == "hey"

    # glob (best-effort; pattern expansion through shell)
    paths = sbx.files.glob("/workspace/*.txt")
    assert any(p.endswith("notes.txt") for p in paths)
    assert any(p.endswith("local.txt") for p in paths)


def test_process_exec_and_env(sbx):
    # Use Python to read env to avoid shell scoping subtleties
    res = sbx.run(["python", "-c", "import os;print(os.getenv('FOO'))"], env={"FOO": "BAR"})
    assert res.exit_code == 0
    assert res.text.strip() == "BAR"
    # Basic command still works
    res2 = sbx.run(["uname", "-s"])  # separate call
    assert res2.exit_code == 0
    assert len(res2.text.strip()) > 0


def test_templates_ls_and_rm_smoke():
    # We don't build images in tests to keep CI light; just smoke test ls/rm paths
    import quicksand as qs

    # ls returns a dict
    idx = qs.Templates.ls()
    assert isinstance(idx, dict)

    # rm of non-existent key should be no-op
    qs.Templates.rm("__nonexistent__template__")


def test_expose_and_lifecycle_status_and_timeout(sbx):
    bind = sbx.expose(port=8000, host_port=18000, protocol="tcp")
    assert bind["container_port"] == 8000
    assert bind["host_port"] == 18000
    assert bind["proto"] == "tcp"

    st = sbx.status()
    assert st.created_at is not None
    assert st.last_active_at is not None
    assert st.timeout_at is not None

    # refresh timeout
    sbx.refresh_timeout(900)
    st2 = sbx.status()
    assert st2.timeout_at is not None


