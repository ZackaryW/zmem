"""JSON-first zmem command line."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from zmem.client import ServiceError
from zmem.client import check as service_check
from zmem.client import query as service_query
from zmem.service import ServiceManagementError
from zmem.service import dispatch as service_dispatch
from zmem.utils.attention import attention_metadata, combine_truncation, resolve_attention
from zmem.utils.commit_messages import validate_policy
from zmem.utils.output import envelope, render_human


def _repo_root(path: Path) -> Path:
    completed = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=False
    )
    if completed.returncode:
        raise ValueError(f"not a Git repository: {path}")
    return Path(completed.stdout.strip()).resolve()


def _resolve(repo: Path, value: str) -> str | None:
    completed = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--verify", f"{value}^{{commit}}"],
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.stdout.strip() if completed.returncode == 0 else None


def _emit(payload: dict, human: bool) -> None:
    print(render_human(payload) if human else json.dumps(payload, indent=2, sort_keys=True))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="zmem")
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--human", action="store_true")
    parser.add_argument("--commit-limit", type=int)
    parser.add_argument("--node-limit", type=int)
    sub = parser.add_subparsers(dest="command", required=True)
    recall = sub.add_parser("recall")
    recall.add_argument("--event", action="append")
    recall.add_argument("--scope")
    recall.add_argument("--since")
    recall.add_argument("--limit", type=int)
    recall.add_argument("--events", action="store_true")
    show = sub.add_parser("show")
    show.add_argument("sha")
    show.add_argument("--diff-content", action="store_true")
    search = sub.add_parser("search")
    search.add_argument("query", nargs="?")
    search.add_argument("--in", dest="domain", default="all")
    search.add_argument("--event", action="append")
    search.add_argument("--regex", action="store_true")
    search.add_argument("--include-invalid", action="store_true")
    search.add_argument("--limit", type=int)
    links = sub.add_parser("links")
    links.add_argument("--from", dest="source")
    links.add_argument("--to", dest="target")
    links.add_argument("--min-score", type=float)
    check = sub.add_parser("check")
    check.add_argument("reference", nargs="?")
    inputs = check.add_mutually_exclusive_group()
    inputs.add_argument("--file", type=Path)
    inputs.add_argument("--stdin", action="store_true")
    check.add_argument("--deep", action="store_true")
    check.add_argument("--conventional", action="store_true")
    check.add_argument("--max-subject-length", type=int)
    check.add_argument("--require-annotation", action="store_true")
    service = sub.add_parser("service")
    service.add_argument("--home", type=Path)
    service.add_argument("--runtime-root", type=Path)
    service_actions = service.add_subparsers(dest="service_action", required=True)
    for name in ("start", "status", "stop", "doctor"):
        service_actions.add_parser(name)
    for name in ("install", "upgrade"):
        action = service_actions.add_parser(name)
        action.add_argument("--binary", type=Path)
        action.add_argument("--no-register", action="store_true")
    uninstall = service_actions.add_parser("uninstall")
    uninstall.add_argument("--no-register", action="store_true")
    uninstall.add_argument("--remove-data", action="store_true")
    return parser


def run(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "service":
            options = vars(args).copy()
            for key in (
                "command",
                "human",
                "home",
                "repo",
                "runtime_root",
                "service_action",
                "commit_limit",
                "node_limit",
            ):
                options.pop(key, None)
            payload = service_dispatch(
                args.service_action,
                home=args.home,
                runtime_root=args.runtime_root,
                **options,
            )
            print(json.dumps(payload, indent=2, sort_keys=True))
            return 0
        attention_policy = resolve_attention(
            commit_limit=args.commit_limit,
            node_limit=args.node_limit,
            environ=os.environ,
        )
        repo = _repo_root(args.repo)
        if args.command == "check":
            if args.max_subject_length is not None and args.max_subject_length < 1:
                raise ValueError("--max-subject-length must be positive")
            if args.reference is not None:
                if not args.deep:
                    raise ValueError("checking an existing commit requires --deep")
                if args.file is not None or args.stdin:
                    raise ValueError("a commit reference cannot be combined with --file or --stdin")
                resolved = _resolve(repo, args.reference)
                if resolved is None:
                    raise LookupError(f"commit not found: {args.reference}")
                message = subprocess.run(
                    ["git", "-C", str(repo), "show", "-s", "--format=%B", resolved],
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout.rstrip("\r\n")
                proposed = None
                reference = resolved
            else:
                if (args.file is None) == (not args.stdin):
                    raise ValueError("exactly one of --file or --stdin is required")
                if args.file is not None:
                    if not args.file.is_file():
                        raise ValueError(f"message file not found: {args.file}")
                    message = args.file.read_text()
                else:
                    message = sys.stdin.read()
                proposed = message
                reference = None
            native = service_check(
                repo,
                message=proposed,
                reference=reference,
                deep=args.deep,
                attention=attention_policy,
            )
            attention = attention_metadata(native)
            diagnostics = list(native.get("diagnostics", []))
            diagnostics.extend(
                validate_policy(
                    message,
                    int(native.get("annotation_count", 0)),
                    conventional=args.conventional,
                    max_subject_length=args.max_subject_length,
                    require_annotation=args.require_annotation,
                )
            )
            ok = bool(native.get("ok")) and not diagnostics
            payload = {
                "command": "check",
                "count": int(native.get("annotation_count", 0)),
                "results": native.get("actions", []),
                "truncated": combine_truncation(attention, False),
                **{
                    key: value
                    for key, value in native.items()
                    if key not in {"actions", "annotation_count", "ok", "diagnostics"}
                },
                "ok": ok,
                "diagnostics": diagnostics,
                "attention": attention,
            }
            _emit(payload, args.human)
            return 0 if ok else 5
        snapshot = service_query(repo, include_invalid=True, attention=attention_policy)
        attention = attention_metadata(snapshot["summary"])
        rows = snapshot["entries"]
        if args.command == "recall":
            if args.events:
                counts = Counter(row["type"] for row in rows if row["valid"])
                result = [{"event": event, "count": count} for event, count in counts.most_common()]
                _emit(envelope("recall", result, attention=attention), args.human)
                return 0
            rows = [row for row in rows if row["valid"]]
            if args.event:
                rows = [row for row in rows if row["type"] in set(args.event)]
            if args.scope is not None:
                rows = [row for row in rows if row.get("scope") == args.scope]
            if args.since:
                boundary = _resolve(repo, args.since)
                if boundary:
                    revision_command = ["git", "-C", str(repo), "rev-list"]
                    if attention_policy.commit_limit != -1:
                        revision_command.append(f"--max-count={attention_policy.commit_limit}")
                    revision_command.append(f"{boundary}..HEAD")
                    walked = subprocess.run(
                        revision_command,
                        capture_output=True,
                        text=True,
                        check=True,
                    ).stdout.splitlines()
                    allowed = {boundary, *walked}
                    rows = [row for row in rows if row["sha"] in allowed]
                else:
                    try:
                        stamp = (
                            datetime.fromisoformat(args.since).replace(tzinfo=UTC)
                            if "T" not in args.since
                            else datetime.fromisoformat(args.since)
                        )
                    except ValueError as exc:
                        raise LookupError(f"could not resolve --since: {args.since}") from exc
                    threshold = int(stamp.timestamp())
                    rows = [row for row in rows if row["commit_time"] >= threshold]
            truncated = args.limit is not None and len(rows) > args.limit
            if args.limit is not None:
                rows = rows[: args.limit]
            _emit(envelope("recall", rows, truncated, attention), args.human)
        elif args.command == "search":
            if not args.include_invalid:
                rows = [row for row in rows if row["valid"]]
            if args.event:
                rows = [row for row in rows if row["type"] in set(args.event)]
            if args.query:
                if args.regex:
                    pattern = re.compile(args.query, re.IGNORECASE)
                    rows = [row for row in rows if pattern.search(row["content"])]
                else:
                    needle = args.query.casefold()
                    rows = [row for row in rows if needle in row["content"].casefold()]
            truncated = args.limit is not None and len(rows) > args.limit
            if args.limit is not None:
                rows = rows[: args.limit]
            _emit(envelope("search", rows, truncated, attention), args.human)
        elif args.command == "show":
            sha = _resolve(repo, args.sha)
            if sha is None:
                raise LookupError(f"commit not found: {args.sha}")
            commit_rows = [row for row in rows if row["sha"] == sha]
            meta = subprocess.run(
                ["git", "-C", str(repo), "show", "-s", "--format=%H%x00%an%x00%aI%x00%B", sha],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.split("\0", 3)
            paths = subprocess.run(
                ["git", "-C", str(repo), "show", "--format=", "--name-status", sha],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.splitlines()
            result = {
                "sha": sha,
                "author": meta[1],
                "ts": meta[2],
                "message": meta[3].strip(),
                "annotations": commit_rows,
                "paths": paths,
            }
            if args.diff_content:
                result["diff"] = subprocess.run(
                    ["git", "-C", str(repo), "show", "--format=", sha], capture_output=True, text=True, check=True
                ).stdout
            _emit(envelope("show", [result], attention=attention), args.human)
        else:
            relationships = snapshot.get("relationships", [])
            if args.source is not None:
                relationships = [row for row in relationships if row["from"] == args.source]
            if args.target is not None:
                relationships = [row for row in relationships if row["to"] == args.target]
            if args.min_score is not None:
                relationships = [row for row in relationships if row["score"] >= args.min_score]
            _emit(envelope("links", relationships, attention=attention), args.human)
        return 0
    except ValueError as exc:
        print(json.dumps({"command": args.command, "error": str(exc)}))
        return 2
    except LookupError as exc:
        print(json.dumps({"command": args.command, "error": str(exc)}))
        return 3
    except (ServiceError, ServiceManagementError, OSError, subprocess.SubprocessError) as exc:
        print(json.dumps({"command": args.command, "error": str(exc)}))
        return 4


def main() -> None:
    raise SystemExit(run())
