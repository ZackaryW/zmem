import pytest

from zmem.utils.annotations import AnnotationKind, parse_annotations


def test_text_annotations_have_one_based_indexes():
    parsed = parse_annotations("subject\n\nzmem(DECISION): choose sqlite\nzmem(LESSON_LEARNT): use full ids")
    assert [(item.kind, item.index, item.content) for item in parsed.annotations] == [
        (AnnotationKind.ENTRY, 1, "choose sqlite"),
        (AnnotationKind.ENTRY, 2, "use full ids"),
    ]


@pytest.mark.parametrize("factor", ["-0.1", "1.1", "nan"])
def test_invalid_decay_factor_is_diagnostic(factor):
    parsed = parse_annotations(f"zmem(DECAY)[deadbeef, 1, {factor}]")
    assert not parsed.annotations
    assert parsed.diagnostics


def test_cancel_is_an_effect():
    parsed = parse_annotations("zmem(CANCEL)[deadbeef, 2]")
    assert parsed.annotations[0].kind is AnnotationKind.CANCEL
    assert parsed.annotations[0].target.index == 2
