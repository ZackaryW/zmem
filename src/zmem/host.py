"""Versioned subprocess host for built-in and trusted Python extensions."""

from __future__ import annotations

import importlib.util
import json
import os
import sys
from dataclasses import asdict
from pathlib import Path

from zmem.builtin import CancelExpander, DecayExpander, DecisionExpander, LessonLearntExpander
from zmem.ext.expander import ExpanderRegistry, ExpansionContext, RegistryError
from zmem.ext.hooks import HookRegistry
from zmem.utils.annotations import parse_annotations, parse_scope
from zmem.utils.discovery import discover, module_kind, module_mode
from zmem.utils.protocol import PROTOCOL_VERSION, ProtocolError, decode_request, encode_response


def _load_module(path: Path, expanders: ExpanderRegistry, hooks: HookRegistry) -> None:
    spec = importlib.util.spec_from_file_location(f"zmem_ext_{abs(hash(path))}", path)
    if spec is None or spec.loader is None:
        raise RegistryError(f"cannot import extension: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if getattr(module, "API_VERSION", None) != 1 or not callable(getattr(module, "register", None)):
        raise RegistryError(f"invalid extension API: {path}")
    if module_kind(path) == "hook":
        module.register(hooks)
    else:
        module.register(expanders, mode=module_mode(path))


def expand_request(payload: dict) -> dict:
    repo = Path(payload["repo"]).resolve()
    global_root = Path(payload.get("global_extension_root", Path.home() / ".zmem" / "ext"))
    custom_root = payload.get("custom_extension_root") or os.getenv("ZMEM_CUSTOM_EXT_ROOT", ".zmem")
    manifest = discover(global_root, repo, custom_root, bool(payload.get("trusted_extensions")))
    expanders = ExpanderRegistry()
    for built_in in (DecisionExpander(), LessonLearntExpander(), DecayExpander(), CancelExpander()):
        expanders.extend(built_in.extension_id, built_in)
    hooks = HookRegistry()
    diagnostics = list(manifest.diagnostics)
    run_hooks = bool(payload.get("run_hooks", True))
    for path in manifest.global_modules + manifest.repo_modules:
        try:
            _load_module(path, expanders, hooks)
        except Exception as exc:
            raise RegistryError(f"failed loading {path}: {exc}") from exc

    parsed = parse_annotations(payload["message"])
    diagnostics.extend(parsed.diagnostics)
    actions: list[dict] = []
    commit = {
        "sha": payload["commit_sha"],
        "commit_time": payload.get("commit_time", 0),
        "scope": parse_scope(payload["message"]),
        "preview": bool(payload.get("preview", False)),
    }
    for annotation in parsed.annotations:
        expander = expanders.get(annotation.type)
        if expander is None:
            diagnostics.append(f"unsupported annotation type: {annotation.type}")
            continue
        context = ExpansionContext(annotation, commit, repo)
        returned = expander.expand(context)
        if returned is not None:
            raise RegistryError(f"expander {annotation.type} returned a value instead of acting on context")
        actions.extend({"kind": action.kind, **dict(action.payload)} for action in context.actions)
        if run_hooks:
            diagnostics.extend(
                hooks.run(
                    "after_expand",
                    {
                        "repo": str(repo),
                        "commit_sha": payload["commit_sha"],
                        "annotation": asdict(annotation),
                        "actions": context.actions,
                    },
                )
            )
    if run_hooks:
        diagnostics.extend(
            hooks.run(
                "after_index", {"repo": str(repo), "commit_sha": payload["commit_sha"], "actions": tuple(actions)}
            )
        )
    return {
        "extension_hash": manifest.identity,
        "journal": {"version": 1, "origin": "zmem-expansion-context", "actions": actions},
        "hook_diagnostics": diagnostics,
        "annotation_count": len(parsed.annotations),
    }


def identity_request(payload: dict) -> dict:
    repo = Path(payload["repo"]).resolve()
    global_root = Path(payload.get("global_extension_root", Path.home() / ".zmem" / "ext"))
    custom_root = payload.get("custom_extension_root") or os.getenv("ZMEM_CUSTOM_EXT_ROOT", ".zmem")
    manifest = discover(global_root, repo, custom_root, bool(payload.get("trusted_extensions")))
    return {
        "extension_hash": manifest.identity,
        "journal": {"version": 1, "origin": "zmem-expansion-context", "actions": []},
        "hook_diagnostics": list(manifest.diagnostics),
        "annotation_count": 0,
    }


def inspect_request(payload: dict) -> dict:
    parsed = parse_annotations(payload["message"])
    return {
        "annotation_count": len(parsed.annotations),
        "parser_diagnostics": list(parsed.diagnostics),
    }


def main() -> None:
    try:
        request = decode_request(sys.stdin.buffer.read())
        if request["operation"] == "expand":
            response = expand_request(request)
        elif request["operation"] == "identity":
            response = identity_request(request)
        elif request["operation"] == "inspect":
            response = inspect_request(request)
        else:
            raise ProtocolError("unsupported operation")
        sys.stdout.buffer.write(encode_response(response))
    except Exception as exc:
        sys.stdout.write(json.dumps({"protocol_version": PROTOCOL_VERSION, "error": str(exc)}))
        raise SystemExit(4) from exc


if __name__ == "__main__":
    main()
