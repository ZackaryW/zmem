"""Stable CLI output helpers."""

from __future__ import annotations

from typing import Any

from zmem.utils.attention import combine_truncation


def envelope(
    command: str,
    rows: list[dict[str, Any]],
    truncated: bool = False,
    attention: dict[str, object] | None = None,
    trail: dict[str, object] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "command": command,
        "count": len(rows),
        "results": rows,
        "truncated": combine_truncation(attention or {}, truncated),
    }
    if attention is not None:
        payload["attention"] = attention
    if trail is not None:
        payload["trail"] = trail
    return payload


def render_human(payload: dict[str, Any]) -> str:
    if payload.get("command") == "check":
        status = "ok" if payload.get("ok") else "failed"
        lines = [f"check: {status}, mode={payload.get('mode')}, annotations={payload.get('count', 0)}"]
        for effect in payload.get("effects", []):
            lines.append(
                "  effect="
                + ", ".join(
                    f"{key}={value}"
                    for key, value in effect.items()
                    if value is not None and key in {"kind", "status", "resolved_sha", "before_score", "after_score"}
                )
            )
        lines.extend(f"  diagnostic={diagnostic}" for diagnostic in payload.get("diagnostics", []))
        return "\n".join(lines)
    suffix = " (truncated)" if payload.get("truncated") else ""
    lines = [f"{payload['command']}: {payload['count']} result(s){suffix}"]
    if attention := payload.get("attention"):
        lines.append(
            "  attention="
            + ", ".join(
                f"{key}={value}"
                for key, value in attention.items()
                if key in {"commit_limit", "node_limit", "selected_commits", "selected_nodes", "truncated"}
            )
        )
    if trail := payload.get("trail"):
        lines.append(
            "  trail="
            + ", ".join(
                f"{key}={value}"
                for key, value in trail.items()
                if key in {"requested_selector", "resolved_oid", "trail_id"}
            )
        )
    for row in payload["results"]:
        lines.append("  " + ", ".join(f"{key}={value}" for key, value in row.items() if value is not None))
    return "\n".join(lines)
