quixand — Local & Pluggable Sandboxes for AI Code Execution
=============================================================

Quixand is a local-first sandbox and code interpreter library. It mirrors the developer-facing API of E2B’s `Sandbox` and `AsyncSandbox` while running locally by default via Docker/Podman, with a clean adapter interface to plug in other backends (your infra, remote HTTP, etc.).

Why quixand?
--------------

- Familiar: mirrors E2B’s concepts and method names where practical
- Local-first: default execution in local containers (Docker/Podman)
- Pluggable: unified `Adapter` protocol for custom backends
- Async & streaming ready; simple, secure, fast
- CLI parity for everyday workflows

Requirements
------------

- Python 3.10+
- Docker or Podman installed and in PATH

Install
-------

Editable install with Docker extras:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -U pip
pip install -e '.[docker]'
```

Configuration
-------------

Quixand works out of the box, but you can configure via environment variables or code.

Environment variables:

- `QS_ADAPTER`: `local-docker` (default) | `chutes` | `remote-http`
- `QS_TIMEOUT_DEFAULT`: default timeout seconds (default 300)
- `QS_IMAGE`: default container image (default `python:3.11-slim`)
- `QS_RUNTIME`: `docker` | `podman` (auto-detects if unset)
- `QS_ROOT`: host directory for state/template cache (default `~/.quixand`)
- `QS_METADATA`: JSON string to tag sandboxes

Programmatic config:

```python
import quixand as qs
cfg = qs.Config(timeout=600, image="python:3.11-slim")
```

Python API
----------

Top-level imports:

```python
from quixand import Sandbox, AsyncSandbox, connect, Templates
```

Sync Sandbox:

```python
import quixand as qs

sbx = qs.Sandbox(template="python:3.11-slim", timeout=600, metadata={"user":"alice"})
sbx.files.write("hello.txt", "hi!")
print([f.path for f in sbx.files.ls(".")])
res = sbx.run(["python","-c","print(2+2)"])
print(res.text)  # "4\n"
execn = sbx.run_code("x=1\nx+=1\nprint(x)")
print(execn.text.strip())  # "2"
sbx.shutdown()
```

Async Sandbox:

```python
import asyncio, quixand as qs

async def main():
    sbx = await qs.AsyncSandbox.create(template="python:3.11-slim")
    await sbx.files.put("data.csv", "/workspace/data.csv")
    res = await sbx.run(["python","-c","print(42)"])
    print(res.text)
    await sbx.shutdown()

asyncio.run(main())
```

Connect to running sandbox:

```python
sbx1 = qs.Sandbox(template="python:3.11-slim")
sid = sbx1.id

sbx2 = qs.connect(sid)
print(sbx2.status())
```

Filesystem API:

```python
sbx.files.write("/workspace/notes.txt", "hello")         # text
sbx.files.write("/workspace/blob.bin", b"\x00\x01", mode="binary")
print(sbx.files.read("/workspace/notes.txt"))             # returns str
print(sbx.files.read("/workspace/blob.bin", mode="binary"))  # returns bytes
sbx.files.mkdir("/workspace/data", parents=True)
sbx.files.put("./local.txt", "/workspace/local.txt")
sbx.files.get("/workspace/local.txt", "./local_copy.txt")
sbx.files.rm("/workspace/local.txt")
paths = sbx.files.glob("/workspace/*.txt")
```

Process execution:

```python
res = sbx.run("echo $USER && uname -a")
print(res.exit_code, res.text)
```

Python code convenience:

```python
sbx.install_pkg("pandas==2.2.2")
execn = sbx.run_code("import pandas as pd; print(pd.__version__)")
print(execn.ok, execn.text)
```

Networking and ports (adapter-dependent):

```python
binding = sbx.expose(port=8000, host_port=18000, proto="tcp")
print(binding)
```

Timeouts and lifecycle:

```python
st = sbx.status()                     # created_at, last_active_at, timeout_at
sbx.refresh_timeout(900)              # extend timeout
sbx.shutdown()                        # stop container and clean state
```

CLI
---

The `qs` CLI mirrors E2B’s verbs.

```bash
qs --help

# Sandbox lifecycle
qs sandbox create --template python:3.11-slim --timeout 900 --env FOO=bar --env BAZ=qux
qs sandbox ls
qs sandbox connect <id>
qs sandbox exec <id> -- echo hello
qs sandbox run-code <id> --code "x=1; print(x+1)"
qs sandbox refresh-timeout <id> --seconds 600
qs sandbox kill <id>

# Files
qs files ls <id> /workspace
qs files put <id> ./local.txt /workspace/local.txt
qs files get <id> /workspace/local.txt ./local_copy.txt
qs files mkdir <id> /workspace/data --parents
qs files rm <id> /workspace/local.txt --recursive

# Templates
qs templates build ./path --name py311-tools
qs templates ls
qs templates rm py311-tools
```

Templates
---------

Quixand supports building images from `e2b.Dockerfile` or `Dockerfile` and caching references locally under `~/.quixand/templates`.

```bash
qs templates build ./examples --name py311-tools
qs templates ls
```

In code:

```python
from quixand import Templates, Sandbox
img = Templates.build("./examples", name="py311-tools")
sbx = Sandbox(template=img)
```

Adapters
--------

Adapters implement a common protocol in `quixand.adapters.base.Adapter`. Included:

- `LocalDockerAdapter` (default) — local Docker/Podman containers
- `ChutesAdapter` (skeleton) — wire to your infra
- `RemoteHTTPAdapter` (skeleton) — call a remote service

Select adapter via `QS_ADAPTER` or passing an instance to `Sandbox(adapter=...)`.

State and Timeout Enforcement
-----------------------------

Quixand keeps a local registry at `~/.quixand/state.json`. A lightweight watchdog process enforces idle timeouts and cleans up containers and state when deadlines are exceeded. Default timeout is 300s; refresh with `refresh_timeout()` or CLI.

Security Defaults
-----------------

- Non-root user inside container (image-dependent)
- No privileged flags
- Bridge network by default (configurable); `none` supported
- CPU/memory/pids limits supported by the adapter
- Ephemeral writable layer

Troubleshooting
---------------

- Docker/Podman not found: ensure one is installed and in PATH
- Permission errors: add your user to the `docker` group (Linux) or run Docker Desktop
- Hanging exec or timeouts: increase `timeout` in `run()` or `QS_TIMEOUT_DEFAULT`
- Unicode output: `CommandResult.text` decodes UTF-8 with replacement; use `stdout` bytes for raw data

Examples
--------

See `examples/`:

- `minimal.py`
- `async_minimal.py`
- `template_build.py`
- `streaming.py` (PTY placeholder; streaming to be implemented)

Roadmap
-------

- Full PTY streaming
- Richer RemoteHTTP/Chutes adapters
- Test suite and CI

License
-------

MIT


