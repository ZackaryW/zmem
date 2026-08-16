"""Read-only hook contracts and failure isolation."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


class HookRegistry:
    def __init__(self) -> None:
        self._hooks: dict[str, list[Callable[[dict[str, Any]], Any]]] = {"after_expand": [], "after_index": []}

    def register(self, event: str, hook: Callable[[dict[str, Any]], Any]) -> None:
        if event not in self._hooks:
            raise ValueError(f"unsupported hook event: {event}")
        self._hooks[event].append(hook)

    def run(self, event: str, context: dict[str, Any]) -> tuple[str, ...]:
        diagnostics: list[str] = []
        for hook in self._hooks[event]:
            try:
                result = hook(dict(context))
                if result is not None:
                    diagnostics.append(f"{event} hook canonical mutation rejected")
            except Exception as exc:  # noqa: BLE001 - arbitrary plugin failures are isolated by contract
                diagnostics.append(f"{event} hook failed: {exc}")
        return tuple(diagnostics)
