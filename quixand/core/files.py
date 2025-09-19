from __future__ import annotations

from quixand.core.sandbox import Sandbox


class Files:
	def __init__(self, sbx: Sandbox):
		self._sbx = sbx

	def write(self, path: str, data: bytes | str, mode: str = "text") -> None:
		self._sbx.files.write(path, data, mode)


