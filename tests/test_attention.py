from __future__ import annotations

import pytest

from zmem.host import inspect_batch_request, inspect_request
from zmem.utils.attention import (
    AttentionPolicy,
    attention_metadata,
    combine_truncation,
    parse_attention_limit,
    resolve_attention,
)


@pytest.mark.parametrize("value", [0, -2, True, "", "many", "1.5"])
def test_attention_limit_rejects_invalid_values(value: object) -> None:
    with pytest.raises((TypeError, ValueError), match="--commit-limit"):
        parse_attention_limit(value, "--commit-limit")


@pytest.mark.parametrize(("value", "expected"), [(1, 1), ("25", 25), (-1, -1), ("-1", -1)])
def test_attention_limit_accepts_positive_or_unlimited(value: object, expected: int) -> None:
    assert parse_attention_limit(value, "--node-limit") == expected


def test_attention_resolution_is_independent_and_cli_precedes_environment() -> None:
    policy = resolve_attention(
        commit_limit=None,
        node_limit=25,
        environ={"ZMEM_COMMIT_LIMIT": "30", "ZMEM_NODE_LIMIT": "10"},
    )
    assert policy == AttentionPolicy(commit_limit=30, node_limit=25)


def test_attention_resolution_uses_built_in_defaults() -> None:
    assert resolve_attention(commit_limit=None, node_limit=None, environ={}) == AttentionPolicy(
        commit_limit=500,
        node_limit=400,
    )


def test_parser_only_inspection_counts_supported_unsupported_and_effect_annotations() -> None:
    response = inspect_request(
        {
            "message": """feat: bounded

zmem(DECISION): keep this
zmem(CUSTOM): extension-owned
zmem(CANCEL)[deadbeef, 1]
zmem(DECAY)[deadbeef, 1, 0.5]
zmem(CANCEL): malformed"""
        }
    )
    assert response["annotation_count"] == 4
    assert response["parser_diagnostics"] == ["invalid CANCEL annotation at index 5"]


def test_batch_inspection_is_strict_complete_and_ordered() -> None:
    response = inspect_batch_request(
        {"items": [{"id": "a", "message": "zmem(DECISION): keep"}, {"id": "b", "message": "plain"}]}
    )
    assert [item["id"] for item in response["inspections"]] == ["a", "b"]
    assert [item["annotation_count"] for item in response["inspections"]] == [1, 0]

    for invalid in (
        {"items": []},
        {"items": [{"id": "", "message": "plain"}]},
        {"items": [{"id": "a", "message": "plain", "extra": True}]},
        {"items": [{"id": "a", "message": 1}]},
    ):
        with pytest.raises((TypeError, ValueError)):
            inspect_batch_request(invalid)


def test_native_attention_metadata_and_result_truncation_compose() -> None:
    native = {
        "attention": {
            "commit_limit": 3,
            "node_limit": 2,
            "selected_commits": 2,
            "selected_nodes": 2,
            "truncated": True,
            "reached": ["node"],
        }
    }
    metadata = attention_metadata(native)
    assert metadata == native["attention"]
    assert combine_truncation(metadata, False) is True
    assert combine_truncation({**metadata, "truncated": False}, True) is True
