from __future__ import annotations

import json
from typing import Optional

from ..adapters.local_docker import LocalDockerAdapter
from ..config import Config
from ..errors import QSSandboxNotFound
from ..types import SandboxStatus
from .sandbox import Sandbox


def connect(sandbox_id: str, adapter: str | None = None) -> Sandbox:
	cfg = Config()
	name = adapter or cfg.adapter
	if name == "local-docker":
		ad = LocalDockerAdapter(cfg)
		# Build a dummy Sandbox bound to existing handle
		h = ad.connect(sandbox_id)
		obj = object.__new__(Sandbox)
		obj._cfg = cfg
		obj._adapter = ad
		obj._handle = h
		obj.files = type("FilesFacade", (), {})  # placeholder; Sandbox __init__ sets this normally
		# reconstruct FilesFacade bound to obj
		from .sandbox import FilesFacade as _FF

		obj.files = _FF(obj)
		obj.id = h.id
		return obj
	raise QSSandboxNotFound(f"Adapter {name} connect not implemented")


