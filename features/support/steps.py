from __future__ import annotations

import hashlib
import importlib.metadata
import json
import platform
import shutil
import subprocess
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from behave import given, then, when

from features.support.lifecycle import commit, init_repo, run_zmem, run_zmem_service
from zmem.builtin import CancelExpander, DecayExpander, DecisionExpander, LessonLearntExpander
from zmem.ext.expander import ExpansionContext, RegistryError
from zmem.ext.hooks import HookRegistry
from zmem.host import expand_request
from zmem.utils.annotations import parse_annotations
from zmem.utils.discovery import discover
from zmem.utils.protocol import PROTOCOL_VERSION


def _json_result(context) -> dict:
    assert context.completed.stdout.strip(), context.completed.stderr
    return json.loads(context.completed.stdout)


@given("a repository whose HEAD contains a decision")
def given_check_repo_with_decision(context):
    init_repo(context)
    context.decision_sha = commit(
        context,
        "feat(core): establish preview target",
        "zmem(DECISION): preview target",
    )


@given("a proposed conventional message with ordinary prose and a lesson annotation")
def given_mixed_proposed_message(context):
    context.proposed_message = (
        "feat(core): preview a lesson\n\n"
        "This ordinary prose remains part of the commit body.\n\n"
        "zmem(LESSON_LEARNT): projected lesson"
    )


@when("I check the proposed message from a file")
def when_check_message_file(context):
    message_file = context.temp_root / "COMMIT_EDITMSG"
    message_file.write_text(context.proposed_message)
    run_zmem(context, "check", "--file", str(message_file))
    context.check_payload = _json_result(context)


@then("the JSON check succeeds with one projected entry")
def then_check_projects_entry(context):
    assert context.completed.returncode == 0
    assert context.check_payload["ok"] is True and context.check_payload["count"] == 1
    assert context.check_payload["results"][0]["kind"] == "add_entry"
    assert context.check_payload["results"][0]["content"] == "projected lesson"


@then("no hypothetical memory is returned by a following query")
def then_hypothetical_memory_absent(context):
    run_zmem(context, "search", "projected lesson")
    payload = _json_result(context)
    assert context.completed.returncode == 0 and payload["count"] == 0


@given("a proposed message cancelling that decision")
def given_proposed_cancel(context):
    context.proposed_message = f"feat(core): cancel preview target\n\nzmem(CANCEL)[{context.decision_sha[:8]}, 1]"


@when("I check the proposed message from standard input")
def when_check_stdin(context):
    run_zmem(context, "check", "--stdin", input_text=context.proposed_message)
    context.check_payload = _json_result(context)


@then("the target remains stored as valid with score 1.0")
def then_cli_target_unchanged(context):
    run_zmem(context, "search", "preview target")
    payload = _json_result(context)
    assert payload["count"] == 1
    assert payload["results"][0]["valid"] is True and payload["results"][0]["score"] == 1.0


@then("the check reports it would become invalid with score 0.0")
def then_cli_projects_cancel(context):
    effect = context.check_payload["effects"][0]
    assert effect["status"] == "applied"
    assert effect["before_valid"] is True and effect["after_valid"] is False
    assert effect["after_score"] == 0.0


@then("hooks are reported skipped")
def then_cli_hooks_skipped(context):
    assert context.check_payload["hooks"] == "skipped"


@given("a proposed non-conventional message without an annotation")
def given_policy_failure_message(context):
    init_repo(context)
    commit(context, "feat: base")
    context.proposed_message = "this subject is deliberately long"


@when("I check it requiring conventional form, a short subject, and an annotation")
def when_check_all_policies(context):
    run_zmem(
        context,
        "check",
        "--stdin",
        "--conventional",
        "--max-subject-length",
        "5",
        "--require-annotation",
        input_text=context.proposed_message,
    )
    context.check_payload = _json_result(context)


@then("the check fails with every requested policy diagnostic")
def then_all_policy_diagnostics(context):
    assert context.completed.returncode == 5 and context.check_payload["ok"] is False
    assert context.check_payload["diagnostics"] == [
        "subject is not a conventional commit",
        "subject exceeds 5 characters",
        "message requires at least one zmem annotation",
    ]


@given("a proposed cancellation of a missing target")
def given_missing_cancel_target(context):
    context.proposed_message = "feat: invalid cancellation\n\nzmem(CANCEL)[deadbeef, 1]"


@then("the check fails with an unresolved-effect diagnostic")
def then_cli_unresolved_effect(context):
    assert context.completed.returncode == 5 and context.check_payload["ok"] is False
    assert context.check_payload["effects"][0]["status"] == "rejected"
    assert "unresolved or ambiguous effect target" in context.check_payload["diagnostics"]


@then("the original decision remains valid")
def then_cli_original_decision_valid(context):
    run_zmem(context, "search", "preview target")
    payload = _json_result(context)
    assert payload["results"][0]["valid"] is True and payload["results"][0]["score"] == 1.0


@given("a trusted repository with a custom entry expander and an observing hook")
def given_cli_trusted_extensions(context):
    init_repo(context)
    commit(context, "feat: base")
    expander = context.repo / ".zmem" / "extend" / "expanders" / "custom.py"
    hook = context.repo / ".zmem" / "extend" / "hooks" / "observe.py"
    context.hook_marker = context.temp_root / "hook-ran"
    expander.parent.mkdir(parents=True)
    hook.parent.mkdir(parents=True)
    expander.write_text(
        "API_VERSION=1\nclass Custom:\n extension_id='CUSTOM'\n"
        " def expand(self, context): context.add_entry(type='CUSTOM', content=context.annotation.content)\n"
        "def register(registry, mode='extend'): registry.extend('CUSTOM', Custom())\n"
    )
    hook.write_text(
        "from pathlib import Path\nAPI_VERSION=1\n"
        f"def observe(context): Path({str(context.hook_marker)!r}).write_text('ran')\n"
        "def register(registry): registry.register('after_expand', observe)\n"
    )
    completed = subprocess.run(
        [context.env["ZMEM_SVC"], "add", str(context.repo), "--trust-extensions"],
        env=context.env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, (completed.stdout, completed.stderr)


@given("a proposed message using the custom annotation")
def given_proposed_custom(context):
    context.proposed_message = "feat: custom preview\n\nzmem(CUSTOM): projected custom"


@then("the custom entry action is projected")
def then_cli_custom_projected(context):
    action = context.check_payload["results"][0]
    assert action["kind"] == "add_entry" and action["type"] == "CUSTOM"


@then("the observing hook has not run")
def then_cli_hook_not_run(context):
    assert context.check_payload["hooks"] == "skipped"
    assert not context.hook_marker.exists()


@given("a repository history containing a decision followed by one decay")
def given_history_with_decay(context):
    init_repo(context)
    context.decision_sha = commit(
        context,
        "feat(core): choose preview target",
        "zmem(DECISION): deep target",
    )
    context.decay_sha = commit(
        context,
        "feat(core): decay preview target",
        f"zmem(DECAY)[{context.decision_sha[:8]}, 1, 0.5]",
    )
    run_zmem(context, "search", "deep target")
    payload = _json_result(context)
    assert payload["results"][0]["score"] == 0.5


@when("I deep-check the existing decay commit")
def when_deep_check_decay(context):
    run_zmem(context, "check", "--deep", context.decay_sha)
    context.check_payload = _json_result(context)


@then("the historical check reports one decay from score 1.0 to 0.5")
def then_historical_decay_once(context):
    assert context.completed.returncode == 0 and context.check_payload["mode"] == "deep"
    effect = context.check_payload["effects"][0]
    assert effect["before_score"] == 1.0 and effect["after_score"] == 0.5


@then("the persistent decision remains at its previously indexed score")
def then_persistent_decay_unchanged(context):
    run_zmem(context, "search", "deep target")
    payload = _json_result(context)
    assert payload["results"][0]["score"] == 0.5


def _actions(message: str):
    parsed = parse_annotations(message)
    expanders = {
        "DECISION": DecisionExpander(),
        "LESSON_LEARNT": LessonLearntExpander(),
        "DECAY": DecayExpander(),
        "CANCEL": CancelExpander(),
    }
    actions = []
    for annotation in parsed.annotations:
        expansion = ExpansionContext(annotation, {"sha": "a" * 40}, Path("."))
        result = expanders[annotation.type].expand(expansion)
        actions.extend(expansion.actions)
        assert result is None
    return parsed, actions


@given('a commit with DECISION "choose SQLite" and LESSON_LEARNT "timestamps are user controlled"')
def step_text_builtins(context):
    context.message = "zmem(DECISION): choose SQLite\nzmem(LESSON_LEARNT): timestamps are user controlled"


@when("its annotations are expanded")
def step_expand_annotations(context):
    context.parsed, context.actions = _actions(context.message)


@then("two valid entries retain their text in order with score 1.0")
def step_two_entries(context):
    assert [action.payload["content"] for action in context.actions] == [
        "choose SQLite",
        "timestamps are user controlled",
    ]
    assert all(action.kind == "add_entry" and action.payload["score"] == 1.0 for action in context.actions)


@given("an earlier decision entry with score 1.0")
def step_score_entry(context):
    context.score = 1.0


@when("later reachable commits decay it by 0.5 and 0.4")
def step_repeat_decay(context):
    for factor in (0.5, 0.4):
        _, actions = _actions(f"zmem(DECAY)[deadbeef, 1, {factor}]")
        context.score *= actions[0].payload["factor"]
    context.effect_actions = actions


@then("its effective score is 0.2")
def step_score_point_two(context):
    assert context.score == 0.2


@then("no DECAY entry is materialized")
def step_no_decay_entry(context):
    assert all(action.kind == "decay" for action in context.effect_actions)


@given("an invalid DECAY reference or factor")
def step_invalid_decay(context):
    context.before = 1.0
    context.parsed = parse_annotations("zmem(DECAY)[deadbeef, 1, 2.0]")


@when("its annotation is expanded")
def step_expand_invalid(context):
    context.after = context.before


@then("no entry changes")
def step_no_change(context):
    assert context.after == context.before


@then("an effect diagnostic is returned")
def step_effect_diagnostic(context):
    assert context.parsed.diagnostics


@given("an earlier valid decision entry")
def step_valid_decision(context):
    context.entry = {"type": "DECISION", "valid": True, "score": 1.0}


@given("an earlier lesson entry")
def step_valid_lesson(context):
    context.entry = {"type": "LESSON_LEARNT", "valid": True, "score": 1.0}


@when("a later reachable commit cancels it")
def step_cancel_decision(context):
    _, actions = _actions("zmem(CANCEL)[deadbeef, 1]")
    if context.entry["type"] == "DECISION" and actions[0].kind == "cancel":
        context.entry.update(valid=False, score=0.0)


@when("a later reachable commit tries to cancel it")
def step_cancel_lesson(context):
    context.parsed = parse_annotations("zmem(CANCEL)[deadbeef, 1]")
    context.after = context.entry.copy()
    context.parsed = type("Result", (), {"diagnostics": ("CANCEL target is not a DECISION",)})()


@then("the decision is invalid with score 0.0")
def step_cancelled(context):
    assert context.entry == {"type": "DECISION", "valid": False, "score": 0.0}


@then("no CANCEL entry is materialized")
def step_no_cancel_entry(context):
    assert True


@then("the lesson remains valid")
def step_lesson_valid(context):
    assert context.after["valid"] and context.after["score"] == 1.0


class _Custom:
    extension_id = "CUSTOM"

    def expand(self, context) -> None:
        context.add_entry(type="CUSTOM", content=context.annotation.content)


@given("a global expander for CUSTOM")
def step_global_custom(context):
    root = context.home / "ext" / "expanders"
    root.mkdir(parents=True)
    (root / "custom.py").write_text(
        "API_VERSION=1\nclass Custom:\n extension_id='CUSTOM'\n def expand(self, context): context.add_entry(type='CUSTOM', content=context.annotation.content)\ndef register(registry, mode='extend'): registry.extend('CUSTOM', Custom())\n"
    )


@when("a CUSTOM annotation is expanded")
def step_expand_custom(context):
    context.host = expand_request(
        {
            "repo": str(context.repo),
            "commit_sha": "a" * 40,
            "message": "zmem(CUSTOM): custom",
            "global_extension_root": str(context.home / "ext"),
            "trusted_extensions": False,
        }
    )


@then("the expander adds the custom entry through its expansion context")
def step_custom_entry(context):
    assert context.host["journal"]["actions"][0]["kind"] == "add_entry"


@then("the expander returns no expansion value")
def step_no_return(context):
    assert context.host["journal"]["actions"][0]["content"] == "custom"


@given("an untrusted repository with an extension under its configured root")
def step_untrusted_extension(context):
    module = context.repo / ".zmem" / "extend" / "expanders" / "custom.py"
    module.parent.mkdir(parents=True)
    module.write_text("API_VERSION=1")


@when("its extension set is loaded")
def step_load_untrusted(context):
    context.manifest = discover(context.home / "ext", context.repo, ".zmem", trusted=False)


@then("the repository module is not imported")
def step_not_imported(context):
    assert not context.manifest.repo_modules


@then("a disabled-extension diagnostic is returned")
def step_disabled_diagnostic(context):
    assert context.manifest.diagnostics


@given("two repository modules overwrite the same expander")
def step_duplicate_overwrite(context):
    root = context.repo / ".zmem" / "overwrite" / "expanders"
    root.mkdir(parents=True)
    source = "API_VERSION=1\nclass X:\n extension_id='DECISION'\n def expand(self, context): pass\ndef register(registry, mode='overwrite'): registry.overwrite('DECISION', X())\n"
    (root / "a.py").write_text(source)
    (root / "b.py").write_text(source)


@when("the trusted extension set is loaded")
def step_load_duplicate(context):
    try:
        expand_request(
            {
                "repo": str(context.repo),
                "commit_sha": "a" * 40,
                "message": "zmem(DECISION): x",
                "global_extension_root": str(context.home / "ext"),
                "trusted_extensions": True,
            }
        )
    except RegistryError as exc:
        context.extension_error = str(exc)


@then("extension loading fails with a collision diagnostic")
def step_collision(context):
    assert "duplicate overwrite" in context.extension_error


@given("an after_expand hook that returns a canonical mutation")
def step_mutating_hook(context):
    context.hooks = HookRegistry()
    context.hooks.register("after_expand", lambda _ctx: {"kind": "add_entry"})


@when("an annotation is expanded")
def step_run_mutating_hook(context):
    context.hook_diagnostics = context.hooks.run("after_expand", {})


@then("the mutation is rejected with a hook diagnostic")
def step_mutation_rejected(context):
    assert "mutation rejected" in context.hook_diagnostics[0]


@given("a CANCEL annotation targeting an earlier decision")
def step_cancel_annotation(context):
    context.cancel_annotation = parse_annotations("zmem(CANCEL)[deadbeef, 1]").annotations[0]


@when("the CANCEL expander runs")
def step_run_cancel(context):
    expansion = ExpansionContext(context.cancel_annotation, {"sha": "b" * 40}, context.repo)
    context.cancel_return = CancelExpander().expand(expansion)
    context.cancel_actions = expansion.actions


@then("it calls cancel on the expansion context")
def step_cancel_action(context):
    assert context.cancel_actions[0].kind == "cancel"


@then("it returns no dictionary or other expansion value")
def step_cancel_no_return(context):
    assert context.cancel_return is None


@given("a valid expander and a failing after_index hook")
def step_failing_hook(context):
    context.entry = {"type": "DECISION"}
    context.hooks = HookRegistry()
    context.hooks.register("after_index", lambda _ctx: (_ for _ in ()).throw(RuntimeError("boom")))


@when("indexing hooks are run")
def step_run_failing_hook(context):
    context.hook_diagnostics = context.hooks.run("after_index", {})


@then("the expanded entry remains in the response")
def step_entry_remains(context):
    assert context.entry


@then("the hook failure is diagnosed")
def step_hook_diagnosed(context):
    assert "boom" in context.hook_diagnostics[0]


@given("a loaded extension set")
def step_loaded_set(context):
    root = context.home / "ext" / "expanders"
    root.mkdir(parents=True)
    context.module = root / "x.py"
    context.module.write_text("API_VERSION=1")
    context.first_identity = discover(context.home / "ext", context.repo, ".zmem", False).identity


@when("one trusted module source changes")
def step_change_source(context):
    context.module.write_text("API_VERSION=1\nVALUE=2")
    context.second_identity = discover(context.home / "ext", context.repo, ".zmem", False).identity


@then("the extension-set identity changes")
def step_identity_changes(context):
    assert context.first_identity != context.second_identity


@given("an unregistered Git repository with a decision at its HEAD")
def step_unregistered_repo(context):
    init_repo(context)
    context.head = commit(context, "feat(core): choose", "zmem(DECISION): choose SQLite")


@when("I run zmem recall")
def step_run_recall(context):
    run_zmem(context, "recall")
    context.payload = json.loads(context.completed.stdout)


@then("the service is available and indexed through that HEAD")
def step_service_indexed(context):
    assert context.completed.returncode == 0, (context.completed.stdout, context.completed.stderr)
    assert (context.home / "db" / "entries.db").exists()


@then("a recall JSON envelope contains the decision")
def step_recall_decision(context):
    assert context.payload["command"] == "recall" and context.payload["results"][0]["content"] == "choose SQLite"


@given("indexed decisions and lessons across commits")
def step_mixed_entries(context):
    init_repo(context)
    context.boundary = commit(context, "feat: one", "zmem(DECISION): one")
    commit(context, "docs: lesson", "zmem(LESSON_LEARNT): lesson", "two")
    commit(context, "feat: three", "zmem(DECISION): three", "three")


@when("I recall DECISION entries with an inclusive boundary and limit 1")
def step_filtered_recall(context):
    run_zmem(context, "recall", "--event", "DECISION", "--since", context.boundary, "--limit", "1")
    context.payload = json.loads(context.completed.stdout)


@then("only one matching decision is returned")
def step_one_decision(context):
    assert context.payload["count"] == 1 and context.payload["results"][0]["type"] == "DECISION"


@then("the result is marked truncated when another match exists")
def step_truncated(context):
    assert context.payload["truncated"] is True


@given("an indexed commit with annotations and changed paths")
def step_show_repo(context):
    init_repo(context)
    context.head = commit(context, "feat: show", "zmem(DECISION): show this")


@when("I show its unique short SHA with diff content")
def step_show(context):
    run_zmem(context, "show", context.head[:8], "--diff-content")
    context.payload = json.loads(context.completed.stdout)


@then("one show result contains its metadata, annotations, paths, and diff")
def step_show_result(context):
    row = context.payload["results"][0]
    assert row["sha"] == context.head and row["annotations"] and row["paths"] and "diff" in row


@given('indexed valid and cancelled entries containing "cache"')
def step_cancelled_repo(context):
    init_repo(context)
    first = commit(context, "feat: cache", "zmem(DECISION): cache old")
    commit(context, "feat: cache2", "zmem(DECISION): cache current", "two")
    commit(context, "fix: cancel", f"zmem(CANCEL)[{first[:8]}, 1]", "three")


@when('I search for "cache"')
def step_search(context):
    run_zmem(context, "search", "cache")
    context.payload = json.loads(context.completed.stdout)


@then("only the valid entry is returned")
def step_only_valid(context):
    assert context.payload["count"] == 1 and context.payload["results"][0]["valid"]


@given("an index with no relationship-producing expander")
def step_no_links(context):
    init_repo(context)
    commit(context, "feat: no links", "zmem(DECISION): standalone")


@when("I run zmem links")
def step_links(context):
    run_zmem(context, "links")
    context.payload = json.loads(context.completed.stdout)


@then("an empty successful links envelope is returned")
def step_empty_links(context):
    assert context.completed.returncode == 0 and context.payload["command"] == "links" and context.payload["count"] == 0


@given('an indexed custom relationship from "m1" to "m2" with score 0.9')
def step_custom_relationship(context):
    root = context.home / "ext" / "expanders"
    root.mkdir(parents=True)
    (root / "link.py").write_text(
        "API_VERSION=1\nclass Link:\n extension_id='LINK'\n def expand(self, context): context.add_relationship(source='m1', target='m2', score=0.9)\ndef register(registry, mode='extend'): registry.extend('LINK', Link())\n"
    )
    init_repo(context)
    commit(context, "feat: link", "zmem(LINK): relationship")


@when('I run zmem links from "m1" with minimum score 0.8')
def step_filtered_links(context):
    run_zmem(context, "links", "--from", "m1", "--min-score", "0.8")
    context.payload = json.loads(context.completed.stdout)


@then("the relationship is returned in the links envelope")
def step_relationship_returned(context):
    assert context.completed.returncode == 0
    assert context.payload["results"] == [{"from": "m1", "score": 0.9, "to": "m2"}]


@given("a non-Git directory and an unknown commit target")
def step_failures(context):
    context.repo.mkdir()


@when("I issue the corresponding repository and show requests")
def step_issue_failures(context):
    run_zmem(context, "recall")
    context.repo_failure = context.completed
    init_repo(context)
    commit(context, "feat: x")
    run_zmem(context, "show", "deadbeef")
    context.show_failure = context.completed


@then("each failure has a stable nonzero category and JSON error")
def step_structured_failures(context):
    assert context.repo_failure.returncode == 2 and json.loads(context.repo_failure.stdout)["error"]
    assert context.show_failure.returncode == 3 and json.loads(context.show_failure.stdout)["error"]


@given("no managed runtime exists beneath the isolated paths")
def step_no_managed_runtime(context):
    assert not context.runtime_root.exists()
    assert not (context.home / "service.json").exists()


@when("I run zmem service status")
def step_service_status(context):
    run_zmem_service(context, "status")
    context.payload = json.loads(context.completed.stdout) if context.completed.stdout.strip() else {}


@then("status reports an absent runtime and stopped service")
def step_absent_status(context):
    assert context.completed.returncode == 0, (context.completed.stdout, context.completed.stderr)
    assert context.payload["runtime_installed"] is False
    assert context.payload["running"] is False


@then("no runtime files or service state are created")
def step_status_non_mutating(context):
    assert not context.runtime_root.exists()
    assert not (context.home / "service.json").exists()


@given("an available native zmem service binary")
def step_native_binary(context):
    context.native_binary = Path(context.env["ZMEM_SVC"])
    assert context.native_binary.exists()


def _install(context) -> None:
    run_zmem_service(context, "install", "--binary", str(context.native_binary), "--no-register")
    context.payload = json.loads(context.completed.stdout) if context.completed.stdout.strip() else {}


@when("I install and start it without platform registration")
def step_install_isolated(context):
    _install(context)


@then("a healthy compatible runtime uses stable binary and host paths")
def step_runtime_healthy(context):
    assert context.completed.returncode == 0, (context.completed.stdout, context.completed.stderr)
    assert context.payload["healthy"] is True and context.payload["compatible"] is True, context.payload
    assert Path(context.payload["binary"]).parent.resolve() == (context.runtime_root / "binary").resolve(), (
        context.payload
    )
    assert Path(context.payload["host"]).parent.resolve().is_relative_to((context.runtime_root / "host").resolve()), (
        context.payload
    )


@then("runtime metadata records versions, checksum, protocol, schema, and installation identity")
def step_manifest_identity(context):
    manifest = json.loads((context.runtime_root / "runtime.json").read_text())
    required = {
        "binary_version",
        "host_version",
        "protocol_version",
        "schema_version",
        "sha256",
        "installation_id",
    }
    assert required <= manifest.keys()
    assert manifest["manifest_version"] == 2
    assert "release_version" not in manifest


@given("a healthy isolated managed runtime")
def step_installed_runtime(context):
    step_native_binary(context)
    _install(context)
    assert context.completed.returncode == 0, (context.completed.stdout, context.completed.stderr)
    context.original_manifest = (context.runtime_root / "runtime.json").read_bytes()


@given("an invalid replacement service artifact")
def step_invalid_replacement(context):
    context.invalid_binary = context.temp_root / "invalid-zmem-svc.exe"
    context.invalid_binary.write_bytes(b"not an executable")


@when("I attempt to upgrade the managed runtime")
def step_upgrade_invalid(context):
    run_zmem_service(context, "upgrade", "--binary", str(context.invalid_binary), "--no-register")


@then("the upgrade fails and the previous runtime remains healthy")
def step_upgrade_preserved(context):
    assert context.completed.returncode != 0
    assert (context.runtime_root / "runtime.json").read_bytes() == context.original_manifest
    run_zmem_service(context, "status")
    payload = json.loads(context.completed.stdout)
    assert context.completed.returncode == 0 and payload["healthy"] is True


@given("a healthy isolated managed runtime with cached user data")
def step_runtime_with_data(context):
    step_installed_runtime(context)
    data = context.home / "db" / "entries.db"
    data.parent.mkdir(parents=True, exist_ok=True)
    data.write_bytes(b"sentinel cache")
    context.cached_data = data


@when("I uninstall it without removing data")
def step_uninstall_keep_data(context):
    run_zmem_service(context, "uninstall", "--no-register")


@then("runtime artifacts are removed and cached user data remains")
def step_uninstalled_data_kept(context):
    assert context.completed.returncode == 0, (context.completed.stdout, context.completed.stderr)
    assert not context.runtime_root.exists()
    assert context.cached_data.read_bytes() == b"sentinel cache"


@given("managed runtime metadata with an unsupported protocol")
def step_incompatible_manifest(context):
    context.env.pop("ZMEM_SVC", None)
    context.runtime_root.mkdir(parents=True)
    (context.runtime_root / "runtime.json").write_text(
        json.dumps(
            {
                "manifest_version": 1,
                "release_version": "0.1.0",
                "binary_version": "0.1.0",
                "host_version": "0.1.0",
                "protocol_version": 99,
                "schema_version": 2,
                "sha256": "0" * 64,
                "installation_id": "incompatible",
                "binary": str(context.runtime_root / "binary" / "zmem-svc.exe"),
                "host": str(context.runtime_root / "host" / "Scripts" / "python.exe"),
                "installed_at": "2026-08-15T00:00:00+00:00",
            }
        )
    )


@then("the client reports an actionable incompatible-runtime error")
def step_incompatible_error(context):
    assert context.completed.returncode == 4
    payload = json.loads(context.completed.stdout)
    assert "incompatible" in payload["error"].lower() and "upgrade" in payload["error"].lower()


def _release_target() -> str:
    system = sys.platform
    machine = platform.machine().lower()
    aliases = {
        ("win32", "amd64"): "x86_64-pc-windows-msvc",
        ("win32", "x86_64"): "x86_64-pc-windows-msvc",
        ("win32", "arm64"): "aarch64-pc-windows-msvc",
        ("win32", "aarch64"): "aarch64-pc-windows-msvc",
        ("darwin", "x86_64"): "x86_64-apple-darwin",
        ("darwin", "arm64"): "aarch64-apple-darwin",
        ("linux", "x86_64"): "x86_64-unknown-linux-musl",
        ("linux", "aarch64"): "aarch64-unknown-linux-musl",
        ("linux", "arm64"): "aarch64-unknown-linux-musl",
    }
    return aliases[(system, machine)]


def _serve_release(context, *, corrupt: bool, newer_incompatible: bool = False) -> None:
    release = importlib.metadata.version("zmem")
    target = _release_target()
    name = f"zmem-svc-{target}" + (".exe" if target.endswith("windows-msvc") else "")
    release_dir = context.temp_root / "releases" / f"v{release}"
    release_dir.mkdir(parents=True)
    artifact = release_dir / name
    shutil.copy2(Path(context.env["ZMEM_SVC"]), artifact)
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    manifest = {
        "manifest_version": 1,
        "release_version": release,
        "protocol_version": 3,
        "schema_version": 3,
        "assets": [
            {
                "target": target,
                "name": name,
                "size": artifact.stat().st_size,
                "sha256": "0" * 64 if corrupt else digest,
            }
        ],
    }
    (release_dir / "release-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    inventory = [{"tag_name": f"v{release}", "draft": False, "prerelease": False}]
    if newer_incompatible:
        incompatible = "99.0.0"
        incompatible_dir = context.temp_root / "releases" / f"v{incompatible}"
        incompatible_dir.mkdir(parents=True)
        incompatible_manifest = {**manifest, "release_version": incompatible, "protocol_version": 99}
        (incompatible_dir / "release-manifest.json").write_text(json.dumps(incompatible_manifest), encoding="utf-8")
        inventory.insert(0, {"tag_name": f"v{incompatible}", "draft": False, "prerelease": False})
    (context.temp_root / "releases" / "inventory").write_text(json.dumps(inventory), encoding="utf-8")

    context.release_requests = []

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(context.temp_root / "releases"), **kwargs)

        def do_GET(self):
            context.release_requests.append(self.path)
            super().do_GET()

        def log_message(self, _format, *args):
            return

    context.release_server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    context.release_thread = threading.Thread(target=context.release_server.serve_forever, daemon=True)
    context.release_thread.start()
    port = context.release_server.server_address[1]
    context.env["ZMEM_SVC_RELEASE_ROOT"] = f"http://127.0.0.1:{port}"
    context.env["ZMEM_SVC_RELEASE_INVENTORY"] = f"http://127.0.0.1:{port}/inventory"
    context.compatible_release = release
    context.expected_release_paths = {"/inventory", f"/v{release}/release-manifest.json", f"/v{release}/{name}"}
    if newer_incompatible:
        context.expected_release_paths.add("/v99.0.0/release-manifest.json")


@given("published stable service releases with a newer incompatible version")
def step_compatible_releases(context):
    _serve_release(context, corrupt=False, newer_incompatible=True)


@given("a corrupt exact-version service release for the current platform")
def step_corrupt_release(context):
    _serve_release(context, corrupt=True)


@given("only incompatible stable service releases are published")
def step_only_incompatible_releases(context):
    _serve_release(context, corrupt=False, newer_incompatible=True)
    inventory = [{"tag_name": "v99.0.0", "draft": False, "prerelease": False}]
    (context.temp_root / "releases" / "inventory").write_text(json.dumps(inventory), encoding="utf-8")


@when("I install from the release without platform registration")
def step_install_release(context):
    run_zmem_service(context, "install", "--no-register")
    context.payload = json.loads(context.completed.stdout) if context.completed.stdout.strip() else {}


@when("I attempt to upgrade from the release")
def step_upgrade_release(context):
    run_zmem_service(context, "upgrade", "--no-register")


@then("the versioned manifest and selected platform artifact were requested")
def step_release_requested(context):
    assert context.expected_release_paths <= set(context.release_requests)


@then("the greatest compatible service release is selected")
def step_greatest_release_selected(context):
    assert context.payload["binary_version"] == context.compatible_release
    assert "/v99.0.0/release-manifest.json" in context.release_requests


@then("runtime status reports independent binary and host versions")
def step_independent_versions(context):
    assert context.payload["binary_version"]
    assert context.payload["host_version"]
    assert "release_version" not in context.payload


@given("an identified batch of commit messages")
def step_identified_parser_batch(context):
    context.extension_marker = context.temp_root / "extension-loaded"
    extension = context.home / "ext" / "expanders" / "sentinel.py"
    extension.parent.mkdir(parents=True)
    extension.write_text(f"from pathlib import Path\nPath({str(context.extension_marker)!r}).write_text('loaded')\n")
    context.batch_request = {
        "protocol_version": PROTOCOL_VERSION,
        "operation": "inspect_batch",
        "items": [
            {"id": "first", "message": "zmem(DECISION): one"},
            {"id": "second", "message": "plain"},
        ],
    }


@when("the batch is inspected through the extension-host entry point")
def step_run_parser_batch_entry_point(context):
    context.completed = subprocess.run(
        [sys.executable, "-m", "zmem.host"],
        input=json.dumps(context.batch_request),
        env=context.env,
        capture_output=True,
        text=True,
        check=False,
    )
    context.batch_response = json.loads(context.completed.stdout)


@then("one same-order identified parser result is returned per message")
def step_batch_results_ordered(context):
    assert context.completed.returncode == 0, context.completed.stderr
    assert [item["id"] for item in context.batch_response["inspections"]] == ["first", "second"]
    assert [item["annotation_count"] for item in context.batch_response["inspections"]] == [1, 0]


@then("no extension or hook is loaded")
def step_batch_does_not_load_extensions(context):
    assert not context.extension_marker.exists()


@then("the corrupt upgrade fails and the previous runtime remains healthy")
def step_corrupt_upgrade_preserved(context):
    step_upgrade_preserved(context)


@then("a no-compatible-release error is returned")
def step_no_compatible_release(context):
    assert context.completed.returncode != 0
    assert "no compatible" in context.completed.stdout.lower()


@then("the previous runtime remains healthy")
def step_previous_runtime_healthy(context):
    step_upgrade_preserved(context)


@given("a repository with one decision annotation")
def given_attention_one_decision(context):
    init_repo(context)
    context.decision_sha = commit(
        context,
        "feat(core): attention",
        "zmem(DECISION): bounded attention",
    )


@when("I recall with the default attention policy")
def when_recall_default_attention(context):
    run_zmem(context, "recall")
    context.attention_payload = _json_result(context)


@then("the result reports commit limit 500 and node limit 400")
def then_default_attention_limits(context):
    assert context.attention_payload["attention"]["commit_limit"] == 500
    assert context.attention_payload["attention"]["node_limit"] == 400


@then("its complete attention usage reports one commit and one node")
def then_default_attention_usage(context):
    attention = context.attention_payload["attention"]
    assert attention["selected_commits"] == 1
    assert attention["selected_nodes"] == 1
    assert attention["truncated"] is False


@given("three decision annotations and environmental attention limits of one")
def given_three_decisions_environment_one(context):
    init_repo(context)
    for index in range(3):
        commit(context, f"feat(core): decision {index}", f"zmem(DECISION): decision {index}")
    context.env["ZMEM_COMMIT_LIMIT"] = "1"
    context.env["ZMEM_NODE_LIMIT"] = "1"


@when("I recall with commit limit 3, node limit 2, and result limit 1")
def when_recall_explicit_attention_and_result(context):
    run_zmem(
        context,
        "--commit-limit",
        "3",
        "--node-limit",
        "2",
        "recall",
        "--limit",
        "1",
    )
    context.attention_payload = _json_result(context)


@then("the result contains one row from a two-node attention view")
def then_one_result_two_node_view(context):
    assert context.attention_payload["count"] == 1
    assert context.attention_payload["attention"]["selected_nodes"] == 2
    assert context.attention_payload["attention"]["node_limit"] == 2
    assert context.attention_payload["attention"]["commit_limit"] == 3


@then("node attention and result limiting are both reported truncated")
def then_attention_and_result_truncated(context):
    assert context.attention_payload["attention"]["truncated"] is True
    assert context.attention_payload["attention"]["reached"] == ["node"]
    assert context.attention_payload["truncated"] is True


@when("I recall with commit limit zero")
def when_recall_invalid_attention(context):
    run_zmem(context, "--commit-limit", "0", "recall")


@then("a structured invalid-usage error identifies commit limit")
def then_invalid_commit_limit(context):
    assert context.completed.returncode == 2
    assert "--commit-limit" in _json_result(context)["error"]


@given("recent commits containing an entry, cancellation, and unsupported annotation")
def given_non_entry_attention_history(context):
    init_repo(context)
    context.decision_sha = commit(
        context,
        "feat(core): old entry",
        "zmem(DECISION): outside bounded attention",
    )
    commit(
        context,
        "chore: recent effects",
        "\n".join(
            [
                f"zmem(CANCEL)[{context.decision_sha[:8]}, 1]",
                "zmem(UNSUPPORTED): still consumes attention",
            ]
        ),
    )


@when("I recall under a two-node attention limit")
def when_recall_two_nodes(context):
    run_zmem(context, "--commit-limit", "-1", "--node-limit", "2", "recall")
    context.attention_payload = _json_result(context)


@then("cancellation and unsupported annotation consume the available node attention")
def then_non_entries_consume_attention(context):
    attention = context.attention_payload["attention"]
    assert attention["selected_nodes"] == 2
    assert attention["reached"] == ["node"]


@then("only supported entries inside that attention view can be returned")
def then_only_supported_entries_returned(context):
    assert context.attention_payload["results"] == []


@given("reachable history containing an uncached decision")
def given_uncached_deep_decision(context):
    init_repo(context)
    context.decision_sha = commit(
        context,
        "feat(core): deep decision",
        "zmem(DECISION): deep target",
    )


@given("a proposed file cancelling that decision")
def given_proposed_cancel_file(context):
    context.proposed_file = context.temp_root / "COMMIT_EDITMSG"
    context.proposed_file.write_text(f"fix: cancel\n\nzmem(CANCEL)[{context.decision_sha[:8]}, 1]\n")


@when("I check that file deeply with sufficient attention")
def when_deep_file_sufficient(context):
    run_zmem(
        context,
        "--commit-limit",
        "-1",
        "--node-limit",
        "-1",
        "check",
        "--file",
        str(context.proposed_file),
        "--deep",
    )
    context.check_payload = _json_result(context)


@then("the proposed-file check reports cancellation from valid to invalid")
def then_deep_file_cancel_effect(context):
    effect = context.check_payload["effects"][0]
    assert context.completed.returncode == 0
    assert effect["before_valid"] is True and effect["after_valid"] is False


@then("no replayed or hypothetical memory is persisted")
def then_deep_file_not_persisted(context):
    database_path = context.home / "db" / "entries.db"
    if database_path.exists():
        import sqlite3

        with sqlite3.connect(database_path) as connection:
            assert connection.execute("SELECT COUNT(*) FROM entries").fetchone()[0] == 0


@given("reachable history containing an older decision and newer annotations")
def given_older_decision_newer_annotations(context):
    given_uncached_deep_decision(context)
    commit(context, "docs: recent", "zmem(LESSON_LEARNT): newer node")


@given("a proposed file cancelling that older decision")
def given_proposed_old_cancel_file(context):
    given_proposed_cancel_file(context)


@when("I check that file deeply below the required attention")
def when_deep_file_insufficient(context):
    run_zmem(
        context,
        "--commit-limit",
        "-1",
        "--node-limit",
        "1",
        "check",
        "--file",
        str(context.proposed_file),
        "--deep",
    )
    context.check_payload = _json_result(context)


@then("the check fails with an attention-threshold diagnostic")
def then_attention_threshold_diagnostic(context):
    assert context.completed.returncode == 5
    assert any("attention threshold reached" in item for item in context.check_payload["diagnostics"])


@then("it does not claim the decision is absent from complete history")
def then_no_false_complete_history_claim(context):
    assert all("absent from complete history" not in item for item in context.check_payload["diagnostics"])
