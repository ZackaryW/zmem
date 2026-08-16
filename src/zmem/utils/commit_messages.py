"""Commit-message policies that callers may opt into during checks."""

from __future__ import annotations

import re

_CONVENTIONAL_SUBJECT = re.compile(r"^[a-z]+(?:\([^)]*\))?!?: .+$")


def validate_policy(
    message: str,
    annotation_count: int,
    *,
    conventional: bool = False,
    max_subject_length: int | None = None,
    require_annotation: bool = False,
) -> tuple[str, ...]:
    """Return every independently requested commit-message policy failure."""

    if max_subject_length is not None and max_subject_length < 1:
        raise ValueError("maximum subject length must be positive")
    subject = message.splitlines()[0].strip() if message.splitlines() else ""
    diagnostics: list[str] = []
    if not subject:
        diagnostics.append("commit subject is empty")
    if conventional and subject and not _CONVENTIONAL_SUBJECT.fullmatch(subject):
        diagnostics.append("subject is not a conventional commit")
    if max_subject_length is not None and len(subject) > max_subject_length:
        diagnostics.append(f"subject exceeds {max_subject_length} characters")
    if require_annotation and annotation_count == 0:
        diagnostics.append("message requires at least one zmem annotation")
    return tuple(diagnostics)
