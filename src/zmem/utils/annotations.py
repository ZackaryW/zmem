"""Deterministic parsing for zmem commit-message annotations."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from enum import StrEnum

_ENTRY = re.compile(r"^(?:[-*]\s+)?zmem\((?P<type>[A-Z][A-Z0-9_]*)\):\s*(?P<content>.+)$")
_DECAY = re.compile(
    r"^(?:[-*]\s+)?zmem\(DECAY\)\[\s*(?P<sha>[0-9a-fA-F]+)\s*,\s*(?P<index>\d+)\s*,\s*(?P<factor>[^]]+)\s*]$"
)
_CANCEL = re.compile(r"^(?:[-*]\s+)?zmem\(CANCEL\)\[\s*(?P<sha>[0-9a-fA-F]+)\s*,\s*(?P<index>\d+)\s*]$")
_CONVENTIONAL = re.compile(r"^[a-z]+(?:\((?P<scope>[^)]*)\))?!?:")


class AnnotationKind(StrEnum):
    ENTRY = "entry"
    DECAY = "decay"
    CANCEL = "cancel"


@dataclass(frozen=True)
class TargetRef:
    sha_prefix: str
    index: int


@dataclass(frozen=True)
class Annotation:
    kind: AnnotationKind
    index: int
    type: str
    content: str | None = None
    target: TargetRef | None = None
    factor: float | None = None


@dataclass(frozen=True)
class ParseResult:
    annotations: tuple[Annotation, ...]
    diagnostics: tuple[str, ...]


def parse_annotations(message: str) -> ParseResult:
    annotations: list[Annotation] = []
    diagnostics: list[str] = []
    ordinal = 0
    for raw in message.splitlines():
        line = raw.strip()
        if "zmem(" not in line:
            continue
        ordinal += 1
        if match := _DECAY.match(line):
            factor_text = match.group("factor").strip()
            try:
                factor = float(factor_text)
            except ValueError:
                factor = math.nan
            index = int(match.group("index"))
            if index < 1 or not math.isfinite(factor) or not 0.0 <= factor <= 1.0:
                diagnostics.append(f"invalid DECAY annotation at index {ordinal}")
                continue
            annotations.append(
                Annotation(
                    AnnotationKind.DECAY,
                    ordinal,
                    "DECAY",
                    target=TargetRef(match.group("sha").lower(), index),
                    factor=factor,
                )
            )
            continue
        if match := _CANCEL.match(line):
            index = int(match.group("index"))
            if index < 1:
                diagnostics.append(f"invalid CANCEL annotation at index {ordinal}")
                continue
            annotations.append(
                Annotation(
                    AnnotationKind.CANCEL, ordinal, "CANCEL", target=TargetRef(match.group("sha").lower(), index)
                )
            )
            continue
        if match := _ENTRY.match(line):
            annotation_type = match.group("type")
            if annotation_type in {"DECAY", "CANCEL"}:
                diagnostics.append(f"invalid {annotation_type} annotation at index {ordinal}")
                continue
            annotations.append(
                Annotation(AnnotationKind.ENTRY, ordinal, annotation_type, match.group("content").strip())
            )
            continue
        diagnostics.append(f"invalid zmem annotation at index {ordinal}")
    return ParseResult(tuple(annotations), tuple(diagnostics))


def parse_scope(message: str) -> str | None:
    first = message.splitlines()[0].strip() if message.splitlines() else ""
    match = _CONVENTIONAL.match(first)
    return match.group("scope") or None if match else None
