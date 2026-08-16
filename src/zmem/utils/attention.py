"""Resolution and output composition for repository attention limits."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

DEFAULT_COMMIT_LIMIT = 500
DEFAULT_NODE_LIMIT = 400


def parse_attention_limit(value: object, option: str) -> int:
    if isinstance(value, bool):
        raise TypeError(f"{option} must be a positive integer or -1")
    try:
        parsed = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{option} must be a positive integer or -1") from exc
    if isinstance(value, float) and not value.is_integer():
        raise ValueError(f"{option} must be a positive integer or -1")
    if parsed != -1 and parsed < 1:
        raise ValueError(f"{option} must be a positive integer or -1")
    return parsed


@dataclass(frozen=True)
class AttentionPolicy:
    commit_limit: int
    node_limit: int

    def __post_init__(self) -> None:
        parse_attention_limit(self.commit_limit, "--commit-limit")
        parse_attention_limit(self.node_limit, "--node-limit")


def resolve_attention(
    *,
    commit_limit: object | None,
    node_limit: object | None,
    environ: Mapping[str, str],
) -> AttentionPolicy:
    resolved_commit = (
        commit_limit if commit_limit is not None else environ.get("ZMEM_COMMIT_LIMIT", DEFAULT_COMMIT_LIMIT)
    )
    resolved_node = node_limit if node_limit is not None else environ.get("ZMEM_NODE_LIMIT", DEFAULT_NODE_LIMIT)
    return AttentionPolicy(
        commit_limit=parse_attention_limit(resolved_commit, "--commit-limit"),
        node_limit=parse_attention_limit(resolved_node, "--node-limit"),
    )


def attention_metadata(native: Mapping[str, object]) -> dict[str, object]:
    value = native.get("attention")
    if not isinstance(value, Mapping):
        raise TypeError("service response is missing attention metadata")
    required = {
        "commit_limit": int,
        "node_limit": int,
        "selected_commits": int,
        "selected_nodes": int,
        "truncated": bool,
        "reached": list,
    }
    for key, expected in required.items():
        if not isinstance(value.get(key), expected):
            raise TypeError(f"service attention metadata has invalid {key}")
    return dict(value)


def combine_truncation(attention: Mapping[str, object], result_truncated: bool) -> bool:
    return bool(attention.get("truncated")) or result_truncated
