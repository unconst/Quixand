"""
This module has been deprecated.
Container operations have been moved to the quixand.container package.
"""

# Kept for backward compatibility - will be removed in future version
import warnings

warnings.warn(
    "quixand.utils.docker_utils is deprecated. "
    "Use quixand.container package instead.",
    DeprecationWarning,
    stacklevel=2
)


def detect_runtime(preferred=None):
    """Deprecated - use container runtime detection in LocalDockerAdapter."""
    warnings.warn(
        "detect_runtime is deprecated. Use LocalDockerAdapter._detect_runtime instead.",
        DeprecationWarning,
        stacklevel=2
    )
    import shutil
    if preferred in {"docker", "podman"}:
        return preferred
    for candidate in ("docker", "podman"):
        if shutil.which(candidate):
            return candidate
    return "docker"
