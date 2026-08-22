"""Versioned JSON wire helpers."""

from __future__ import annotations

import json
from typing import Any

PROTOCOL_VERSION = 4


class ProtocolError(ValueError):
    pass


def decode_request(data: bytes) -> dict[str, Any]:
    try:
        payload = json.loads(data)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProtocolError("invalid JSON request") from exc
    if not isinstance(payload, dict) or payload.get("protocol_version") != PROTOCOL_VERSION:
        raise ProtocolError("unsupported protocol version")
    if not isinstance(payload.get("operation"), str):
        raise ProtocolError("missing operation")
    return payload


def encode_response(payload: dict[str, Any]) -> bytes:
    return json.dumps({"protocol_version": PROTOCOL_VERSION, **payload}, separators=(",", ":"), sort_keys=True).encode()
