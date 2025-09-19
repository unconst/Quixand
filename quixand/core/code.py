from __future__ import annotations

from quixand.core.sandbox import Sandbox
from quixand.types import Execution


def run_code(sbx: Sandbox, code: str) -> Execution:
	return sbx.run_code(code)


