"""Live Git observations and strict immutable-trail response types."""

from __future__ import annotations

import re
import subprocess
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

_OID = re.compile(r"^[0-9a-f]{40}$")


@dataclass(frozen=True)
class ObservedRef:
    selector: str | None
    oid: str


def observe_ref(repository: Path, selector: str | None) -> ObservedRef:
    target = selector or "HEAD"
    completed = subprocess.run(
        ["git", "-C", repository, "rev-parse", "--verify", f"{target}^{{commit}}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode:
        raise ValueError(completed.stderr.strip() or f"cannot resolve Git selector: {target}")
    oid = completed.stdout.strip().lower()
    if not _OID.fullmatch(oid):
        raise ValueError("Git selector did not resolve to a full commit OID")
    return ObservedRef(selector, oid)


@dataclass(frozen=True)
class TrailSummary:
    requested_selector: str | None
    resolved_oid: str
    trail_id: str
    attention_identity: str
    selected_commits: int
    selected_nodes: int
    extension_identity: str
    protocol_version: int
    schema_version: int

    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> TrailSummary:
        expected = {
            "requested_selector",
            "resolved_oid",
            "trail_id",
            "attention_identity",
            "selected_commits",
            "selected_nodes",
            "extension_identity",
            "protocol_version",
            "schema_version",
        }
        if set(value) != expected:
            raise ValueError("trail summary has unknown or missing fields")
        selector = value["requested_selector"]
        strings = ("resolved_oid", "trail_id", "attention_identity", "extension_identity")
        integers = ("selected_commits", "selected_nodes", "protocol_version", "schema_version")
        if selector is not None and not isinstance(selector, str):
            raise TypeError("requested selector must be a string or null")
        if any(not isinstance(value[field], str) or not value[field] for field in strings):
            raise TypeError("trail identity fields must be non-empty strings")
        if not _OID.fullmatch(str(value["resolved_oid"])):
            raise ValueError("resolved OID must be a full lowercase commit OID")
        if any(type(value[field]) is not int or value[field] < 0 for field in integers):
            raise TypeError("trail count and compatibility fields must be non-negative integers")
        return cls(
            requested_selector=selector,
            resolved_oid=value["resolved_oid"],
            trail_id=value["trail_id"],
            attention_identity=value["attention_identity"],
            selected_commits=value["selected_commits"],
            selected_nodes=value["selected_nodes"],
            extension_identity=value["extension_identity"],
            protocol_version=value["protocol_version"],
            schema_version=value["schema_version"],
        )

    def to_mapping(self) -> dict[str, object]:
        return {
            "requested_selector": self.requested_selector,
            "resolved_oid": self.resolved_oid,
            "trail_id": self.trail_id,
            "attention_identity": self.attention_identity,
            "selected_commits": self.selected_commits,
            "selected_nodes": self.selected_nodes,
            "extension_identity": self.extension_identity,
            "protocol_version": self.protocol_version,
            "schema_version": self.schema_version,
        }


@dataclass(frozen=True)
class NativeQueryRequest:
    repository: str
    selector: str | None = None
    observed_oid: str | None = None

    def with_ref(self, observed: ObservedRef) -> NativeQueryRequest:
        return NativeQueryRequest(self.repository, observed.selector, observed.oid)

    def to_mapping(self) -> dict[str, object]:
        return {
            "repository": self.repository,
            "selector": self.selector,
            "observed_oid": self.observed_oid,
        }
