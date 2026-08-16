from pathlib import Path

import pytest

from zmem.builtin import CancelExpander, DecisionExpander
from zmem.ext.expander import ExpanderRegistry, ExpansionContext, RegistryError
from zmem.utils.annotations import parse_annotations
from zmem.utils.discovery import discover


class Dummy:
    extension_id = "CUSTOM"

    def expand(self, annotation, context):
        return annotation


def test_extend_rejects_collision():
    registry = ExpanderRegistry()
    registry.extend("CUSTOM", Dummy())
    with pytest.raises(RegistryError):
        registry.extend("CUSTOM", Dummy())


def test_overwrite_requires_target():
    with pytest.raises(RegistryError):
        ExpanderRegistry().overwrite("CUSTOM", Dummy())


def test_untrusted_repo_is_not_discovered(tmp_path: Path):
    module = tmp_path / ".zmem" / "extend" / "expanders" / "custom.py"
    module.parent.mkdir(parents=True)
    module.write_text("API_VERSION = 1")
    manifest = discover(tmp_path / "home", tmp_path, ".zmem", trusted=False)
    assert not manifest.repo_modules
    assert manifest.diagnostics


def test_source_hash_changes(tmp_path: Path):
    root = tmp_path / "home" / "expanders"
    root.mkdir(parents=True)
    module = root / "custom.py"
    module.write_text("API_VERSION = 1")
    first = discover(tmp_path / "home", tmp_path, ".zmem", trusted=False).identity
    module.write_text("API_VERSION = 1\nVALUE = 2")
    second = discover(tmp_path / "home", tmp_path, ".zmem", trusted=False).identity
    assert first != second


def test_decision_expander_acts_on_context_without_returning():
    annotation = parse_annotations("zmem(DECISION): choose actions").annotations[0]
    context = ExpansionContext(annotation, {"sha": "a" * 40}, Path("."))
    assert DecisionExpander().expand(context) is None
    action = context.actions[0]
    assert action.kind == "add_entry"
    assert action.payload["content"] == "choose actions"


def test_cancel_expander_acts_on_context_without_returning():
    annotation = parse_annotations("zmem(CANCEL)[deadbeef, 1]").annotations[0]
    context = ExpansionContext(annotation, {"sha": "b" * 40}, Path("."))
    assert CancelExpander().expand(context) is None
    action = context.actions[0]
    assert action.kind == "cancel"
    assert action.payload["target_sha"] == "deadbeef"


def test_expansion_actions_are_immutable_snapshots():
    annotation = parse_annotations("zmem(DECISION): immutable").annotations[0]
    context = ExpansionContext(annotation, {"sha": "a" * 40}, Path("."))
    DecisionExpander().expand(context)
    with pytest.raises(AttributeError):
        context.actions.append("bad")
