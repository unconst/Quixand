from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any

from ..config import Config


INDEX = Config.templates_dir() / "index.json"


class Templates:
	@staticmethod
	def build(path: str, name: Optional[str] = None, build_args: Optional[Dict[str, Any]] = None) -> str:
		p = Path(path)
		if not p.exists():
			raise FileNotFoundError(path)
		dockerfile = p / "e2b.Dockerfile"
		if not dockerfile.exists():
			dockerfile = p / "Dockerfile"
		if not dockerfile.exists():
			raise FileNotFoundError("No e2b.Dockerfile or Dockerfile found")

		# Include build_args in digest calculation if provided
		digest_content = _hash_dir(p)
		if build_args:
			# Add build args to hash to ensure unique images for different build args
			args_str = json.dumps(build_args, sort_keys=True)
			digest_content = hashlib.sha256(
				(digest_content + args_str).encode()
			).hexdigest()

		img_name = f"qs/{name or p.name}:{digest_content[:12]}"
		
		# Use runtime from Config
		cfg = Config()
		runtime = cfg.runtime or "docker"
		
		# Check if image already exists
		if _image_exists(img_name, runtime):
			print(f"Using cached image: {img_name}")
			# Still update the index for consistency
			idx = _load_index()
			idx[name or p.name] = {"image": img_name, "digest": digest_content}
			INDEX.write_text(json.dumps(idx, indent=2))
			return img_name
		
		# Build the image if it doesn't exist
		print(f"Building new image: {img_name}")
		cmd = [runtime, "build", "-f", str(dockerfile), "-t", img_name]
		
		# Add build arguments if provided
		if build_args:
			for key, value in build_args.items():
				cmd.extend(["--build-arg", f"{key}={value}"])
		
		cmd.append(str(p))
		subprocess.check_call(cmd)

		idx = _load_index()
		idx[name or p.name] = {"image": img_name, "digest": digest_content}
		INDEX.write_text(json.dumps(idx, indent=2))
		return img_name

	@staticmethod
	def ls() -> dict:
		return _load_index()

	@staticmethod
	def rm(name: str) -> None:
		idx = _load_index()
		idx.pop(name, None)
		INDEX.write_text(json.dumps(idx, indent=2))
	
	@staticmethod
	def agentgym(env_name: str) -> str:
		template_path = "env_templates/agentgym"
		
		# Always pre-build with the specified environment
		return Templates.build(
			template_path,
			name=f"agentgym-{env_name}",
			build_args={"PREINSTALL_ENV": env_name}
		)


def _hash_dir(path: Path) -> str:
	h = hashlib.sha256()
	for root, _, files in os.walk(path):
		for f in sorted(files):
			pp = Path(root) / f
			if pp.name.startswith(".git"):
				continue
			h.update(pp.read_bytes())
	return h.hexdigest()


def _load_index() -> dict:
	if not INDEX.exists():
		return {}
	try:
		return json.loads(INDEX.read_text())
	except Exception:
		return {}


def _image_exists(image_name: str, runtime: str = "docker") -> bool:
	"""Check if a Docker/Podman image exists locally."""
	try:
		result = subprocess.run(
			[runtime, "images", "-q", image_name],
			capture_output=True,
			text=True,
			check=False
		)
		return bool(result.stdout.strip())
	except Exception:
		return False


