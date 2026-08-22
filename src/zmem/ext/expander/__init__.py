"""Deterministic annotation expander registry."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Protocol

from zmem.utils.annotations import Annotation, TargetRef
from zmem.utils.metadata import MetadataPatch


@dataclass(frozen=True)
class Action:
    kind: str
    payload: Mapping[str, Any]


class ExpansionContext:
    """Behavioral expansion surface; actions are journaled, never executed here."""

    def __init__(self, annotation: Annotation, commit: Mapping[str, Any], repository: Path) -> None:
        self.annotation = annotation
        self.commit = MappingProxyType(dict(commit))
        self.repository = repository.resolve()
        self._actions: list[Action] = []

    @property
    def actions(self) -> tuple[Action, ...]:
        return tuple(self._actions)

    def _record(self, kind: str, **payload: Any) -> None:
        self._actions.append(Action(kind, MappingProxyType(payload)))

    def add_entry(self, *, type: str, content: str, score: float = 1.0) -> None:
        if not 0.0 <= score <= 1.0:
            raise ValueError("score must be between 0.0 and 1.0")
        self._record(
            "add_entry",
            commit_sha=self.commit["sha"],
            annotation_index=self.annotation.index,
            type=type,
            content=content,
            score=score,
            valid=True,
            commit_time=self.commit.get("commit_time", 0),
            scope=self.commit.get("scope"),
        )

    def add_relationship(self, *, source: str, target: str, score: float = 1.0) -> None:
        self._record("add_relationship", commit_sha=self.commit["sha"], source=source, target=target, score=score)

    def decay(self, target: TargetRef, *, factor: float) -> None:
        self._record("decay", target_sha=target.sha_prefix, target_index=target.index, factor=factor)

    def cancel(self, target: TargetRef) -> None:
        self._record("cancel", target_sha=target.sha_prefix, target_index=target.index)

    def metadata_patch(self, patch: MetadataPatch) -> None:
        self._record(
            "metadata_patch",
            from_sha=patch.from_sha,
            to_sha=patch.to_sha,
            operations=tuple(operation.to_mapping() for operation in patch.operations),
        )

    def diagnose(self, message: str) -> None:
        self._record("diagnose", message=message)


class Expander(Protocol):
    extension_id: str

    def expand(self, context: ExpansionContext) -> None: ...


class RegistryError(ValueError):
    pass


class ExpanderRegistry:
    def __init__(self) -> None:
        self._items: dict[str, Expander] = {}
        self._overwritten: set[str] = set()

    def extend(self, extension_id: str, expander: Expander) -> None:
        if extension_id in self._items:
            raise RegistryError(f"extension already registered: {extension_id}")
        self._items[extension_id] = expander

    def overwrite(self, extension_id: str, expander: Expander) -> None:
        if extension_id not in self._items:
            raise RegistryError(f"overwrite target missing: {extension_id}")
        if extension_id in self._overwritten:
            raise RegistryError(f"duplicate overwrite: {extension_id}")
        self._items[extension_id] = expander
        self._overwritten.add(extension_id)

    def get(self, extension_id: str) -> Expander | None:
        return self._items.get(extension_id)
