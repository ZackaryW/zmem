import pytest

from zmem.utils.output import envelope
from zmem.utils.protocol import ProtocolError, decode_request, encode_response


def test_envelope_shape():
    assert envelope("recall", [{"id": "x"}], True) == {
        "command": "recall",
        "count": 1,
        "results": [{"id": "x"}],
        "truncated": True,
    }


def test_envelope_preserves_typed_trail_identity():
    trail = {"trail_id": "trail-1", "resolved_oid": "a" * 40}
    assert envelope("recall", [], trail=trail)["trail"] is trail


def test_protocol_rejects_wrong_version():
    with pytest.raises(ProtocolError):
        decode_request(b'{"protocol_version":99,"operation":"expand"}')


def test_response_is_json_bytes():
    assert b'"protocol_version":4' in encode_response({"entries": []})
