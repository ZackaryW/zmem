"""Extension path discovery and stable source identity."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ExtensionManifest:
    global_modules: tuple[Path, ...]
    repo_modules: tuple[Path, ...]
    identity: str
    diagnostics: tuple[str, ...]


def module_mode(path: Path) -> str:
    parts = {part.casefold() for part in path.parts}
    return "overwrite" if "overwrite" in parts else "extend"


def module_kind(path: Path) -> str:
    parts = {part.casefold() for part in path.parts}
    return "hook" if "hooks" in parts else "expander"


def _modules(root: Path) -> tuple[Path, ...]:
    if not root.exists():
        return ()
    return tuple(sorted((p.resolve() for p in root.rglob("*.py") if p.is_file()), key=lambda p: str(p).casefold()))


def discover(global_root: Path, repo: Path, custom_root: str, trusted: bool) -> ExtensionManifest:
    global_modules = _modules(global_root / "expanders") + _modules(global_root / "hooks")
    candidate = Path(custom_root)
    repo_root = candidate if candidate.is_absolute() else repo / candidate
    repo_modules: tuple[Path, ...] = ()
    diagnostics: list[str] = []
    if trusted:
        repo_modules = (
            _modules(repo_root / "extend" / "expanders")
            + _modules(repo_root / "extend" / "hooks")
            + _modules(repo_root / "overwrite" / "expanders")
            + _modules(repo_root / "overwrite" / "hooks")
        )
    elif any((repo_root / branch).exists() for branch in ("extend", "overwrite")):
        diagnostics.append(f"repository extensions disabled: {repo_root}")
    digest = hashlib.sha256()
    for path in global_modules + repo_modules:
        digest.update(str(path).encode())
        digest.update(path.read_bytes())
    return ExtensionManifest(global_modules, repo_modules, digest.hexdigest(), tuple(diagnostics))
