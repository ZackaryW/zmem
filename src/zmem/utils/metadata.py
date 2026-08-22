"""Typed metadata values and conservative monorepo area matching."""

from __future__ import annotations

import re
from collections.abc import Collection, Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import PurePosixPath

_SHA = re.compile(r"^[0-9a-fA-F]+$")
_OPERATION = re.compile(r"^(?P<key>[a-z_][a-z0-9_]*)(?P<operator>\+=|=)(?P<value>.*)$")
_SET_KEYS = frozenset({"affected_areas", "tags"})
_SCALAR_KEYS = frozenset({"owner"})


class MetadataOperator(StrEnum):
    SET = "set"
    ADD = "add"
    NULL = "null"


@dataclass(frozen=True)
class MetadataOperation:
    key: str
    operator: MetadataOperator
    value: str | None

    def to_mapping(self) -> dict[str, str | None]:
        return {"key": self.key, "operator": self.operator.value, "value": self.value}

    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> MetadataOperation:
        if set(value) != {"key", "operator", "value"}:
            raise ValueError("metadata operation has unknown or missing fields")
        key = value["key"]
        raw_operator = value["operator"]
        raw_value = value["value"]
        if not isinstance(key, str) or not isinstance(raw_operator, str):
            raise TypeError("metadata operation key and operator must be strings")
        operator = MetadataOperator(raw_operator)
        if raw_value is not None and not isinstance(raw_value, str):
            raise TypeError("metadata operation value must be a string or null")
        operation = cls(key, operator, raw_value)
        _validate_operation(operation)
        return operation


@dataclass(frozen=True)
class MetadataPatch:
    from_sha: str
    to_sha: str
    operations: tuple[MetadataOperation, ...]

    def to_mapping(self) -> dict[str, object]:
        return {
            "from_sha": self.from_sha,
            "to_sha": self.to_sha,
            "operations": [operation.to_mapping() for operation in self.operations],
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> MetadataPatch:
        if set(value) != {"from_sha", "to_sha", "operations"}:
            raise ValueError("metadata patch has unknown or missing fields")
        from_sha = value["from_sha"]
        to_sha = value["to_sha"]
        operations = value["operations"]
        if not isinstance(from_sha, str) or not isinstance(to_sha, str):
            raise TypeError("metadata patch endpoints must be strings")
        if not _SHA.fullmatch(from_sha) or not _SHA.fullmatch(to_sha):
            raise ValueError("metadata patch endpoints must be hexadecimal prefixes")
        if not isinstance(operations, list) or not operations:
            raise TypeError("metadata patch operations must be a non-empty array")
        if any(not isinstance(item, Mapping) for item in operations):
            raise TypeError("metadata patch operation must be an object")
        return cls(from_sha, to_sha, tuple(MetadataOperation.from_mapping(item) for item in operations))


@dataclass(frozen=True)
class MetadataAssignment:
    commit_oid: str
    value: str
    ancestors: frozenset[str]


@dataclass(frozen=True)
class MetadataResolution:
    value: str | None
    conflicts: tuple[str, ...]


def resolve_assignments(assignments: Collection[MetadataAssignment]) -> MetadataResolution:
    maximal = [
        candidate
        for candidate in assignments
        if not any(candidate.commit_oid in other.ancestors for other in assignments if other is not candidate)
    ]
    values = tuple(sorted({candidate.value for candidate in maximal}))
    if len(values) == 1:
        return MetadataResolution(values[0], ())
    return MetadataResolution(None, values)


def normalize_area(value: str) -> str:
    if value == "<root>":
        return value
    if not value or value.startswith("/") or "\\" in value or "//" in value:
        raise ValueError("affected area must be a normalized repository-relative path")
    path = PurePosixPath(value)
    if str(path) != value or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError("affected area must be a normalized repository-relative path")
    return value


def areas_overlap(stored: tuple[str, ...] | None, requested: Collection[str]) -> bool:
    if stored is None:
        return True
    normalized_stored = tuple(normalize_area(area) for area in stored)
    normalized_requested = tuple(normalize_area(area) for area in requested)
    for left in normalized_stored:
        for right in normalized_requested:
            if left == "<root>" or right == "<root>":
                if left == right:
                    return True
                continue
            if left == right or left.startswith(f"{right}/") or right.startswith(f"{left}/"):
                return True
    return False


def _validate_operation(operation: MetadataOperation) -> None:
    if operation.key not in _SET_KEYS | _SCALAR_KEYS:
        raise ValueError("unsupported metadata key")
    if operation.operator is MetadataOperator.NULL:
        if operation.value is not None:
            raise ValueError("null metadata operation cannot carry a value")
        return
    if not operation.value:
        raise ValueError("metadata operation requires a value")
    if operation.operator is MetadataOperator.ADD and operation.key not in _SET_KEYS:
        raise ValueError("metadata add requires a set-valued key")
    if operation.key == "affected_areas":
        normalize_area(operation.value)


def parse_metadata_patch(parts: list[str]) -> MetadataPatch:
    if len(parts) < 3:
        raise ValueError("META requires two endpoints and at least one operation")
    from_sha, to_sha = (part.strip().lower() for part in parts[:2])
    if not _SHA.fullmatch(from_sha) or not _SHA.fullmatch(to_sha):
        raise ValueError("META endpoints must be hexadecimal commit prefixes")
    operations: list[MetadataOperation] = []
    for raw in parts[2:]:
        match = _OPERATION.fullmatch(raw.strip())
        if match is None:
            raise ValueError("invalid META operation")
        key = match.group("key")
        raw_operator = match.group("operator")
        raw_value = match.group("value").strip()
        if raw_operator == "=" and raw_value == "null":
            operation = MetadataOperation(key, MetadataOperator.NULL, None)
        else:
            operation = MetadataOperation(
                key,
                MetadataOperator.ADD if raw_operator == "+=" else MetadataOperator.SET,
                raw_value,
            )
        _validate_operation(operation)
        operations.append(operation)
    return MetadataPatch(from_sha, to_sha, tuple(operations))
