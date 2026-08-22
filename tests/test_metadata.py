from pathlib import Path

import pytest

from zmem.builtin import MetaExpander
from zmem.ext.expander import ExpansionContext
from zmem.utils.annotations import AnnotationKind, parse_annotations
from zmem.utils.metadata import (
    MetadataAssignment,
    MetadataOperator,
    MetadataPatch,
    areas_overlap,
    normalize_area,
    resolve_assignments,
)


def test_meta_parses_ordered_typed_operations_without_entry():
    parsed = parse_annotations("zmem(META)[abc123, def456, owner=platform, tags+=security, affected_areas=null]")
    assert parsed.diagnostics == ()
    annotation = parsed.annotations[0]
    assert annotation.kind is AnnotationKind.META
    assert annotation.patch.from_sha == "abc123"
    assert annotation.patch.to_sha == "def456"
    assert [(item.key, item.operator, item.value) for item in annotation.patch.operations] == [
        ("owner", MetadataOperator.SET, "platform"),
        ("tags", MetadataOperator.ADD, "security"),
        ("affected_areas", MetadataOperator.NULL, None),
    ]


@pytest.mark.parametrize(
    "text",
    [
        "zmem(META)[abc, def, owner+=platform]",
        "zmem(META)[abc, def, unknown=value]",
        "zmem(META)[abc, def, score=0]",
        "zmem(META)[abc, def, tags+=]",
        "zmem(META)[abc, def]",
    ],
)
def test_invalid_meta_is_diagnostic(text):
    parsed = parse_annotations(text)
    assert parsed.annotations == ()
    assert parsed.diagnostics == ("invalid META annotation at index 1",)


@pytest.mark.parametrize("value", ["", "/a", "a//b", "a/../b", "./a", "a\\b"])
def test_area_normalization_rejects_non_repository_relative_values(value):
    with pytest.raises(ValueError):
        normalize_area(value)


def test_area_overlap_is_hierarchical_with_root_and_global_rules():
    assert areas_overlap(None, ("anything",))
    assert areas_overlap(("b",), ("b/sub",))
    assert areas_overlap(("b/sub",), ("b",))
    assert not areas_overlap(("b",), ("c",))
    assert areas_overlap(("<root>",), ("<root>",))
    assert not areas_overlap(("<root>",), ("a",))


def test_meta_expander_journals_patch_without_entry():
    annotation = parse_annotations("zmem(META)[abc123, def456, owner=platform, tags+=security]").annotations[0]
    context = ExpansionContext(annotation, {"sha": "f" * 40}, Path("."))
    MetaExpander().expand(context)
    assert [action.kind for action in context.actions] == ["metadata_patch"]
    assert context.actions[0].payload == {
        "from_sha": "abc123",
        "to_sha": "def456",
        "operations": (
            {"key": "owner", "operator": "set", "value": "platform"},
            {"key": "tags", "operator": "add", "value": "security"},
        ),
    }


def test_metadata_patch_mapping_round_trips_without_type_coercion():
    patch = parse_annotations("zmem(META)[abc123, def456, tags=security]").annotations[0].patch
    assert MetadataPatch.from_mapping(patch.to_mapping()) == patch
    with pytest.raises((TypeError, ValueError)):
        MetadataPatch.from_mapping(patch.to_mapping() | {"from_sha": 12})


def test_incomparable_assignments_conflict_until_a_descendant_resolves():
    concurrent = resolve_assignments(
        (
            MetadataAssignment("a", "one", frozenset()),
            MetadataAssignment("b", "two", frozenset()),
        )
    )
    assert concurrent.value is None and concurrent.conflicts == ("one", "two")
    resolved = resolve_assignments(
        (
            MetadataAssignment("a", "one", frozenset()),
            MetadataAssignment("b", "two", frozenset()),
            MetadataAssignment("c", "resolved", frozenset({"a", "b"})),
        )
    )
    assert resolved.value == "resolved" and resolved.conflicts == ()
