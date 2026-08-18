from __future__ import annotations

import hashlib
import io
from pathlib import Path

import pytest

from zmem.utils.release import (
    ReleaseAsset,
    ReleaseManifest,
    acquire_compatible_release_binary,
    copy_verified,
    iter_release_inventory,
    platform_target,
    select_compatible_release,
    stable_release_version,
)
from zmem.utils.runtime import find_service_binary


@pytest.mark.parametrize(
    ("system", "machine", "expected"),
    [
        ("win32", "AMD64", "x86_64-pc-windows-msvc"),
        ("win32", "ARM64", "aarch64-pc-windows-msvc"),
        ("win32", "i686", "i686-pc-windows-msvc"),
        ("darwin", "x86_64", "x86_64-apple-darwin"),
        ("darwin", "arm64", "aarch64-apple-darwin"),
        ("linux", "x86_64", "x86_64-unknown-linux-musl"),
        ("linux", "aarch64", "aarch64-unknown-linux-musl"),
    ],
)
def test_platform_target_alias_matrix(system: str, machine: str, expected: str) -> None:
    assert platform_target(system, machine) == expected


def test_unsupported_platform_is_actionable() -> None:
    with pytest.raises(ValueError, match="plan9.*mips"):
        platform_target("plan9", "mips")


def _manifest(asset: dict[str, object] | None = None) -> dict[str, object]:
    return {
        "manifest_version": 1,
        "release_version": "1.0.0",
        "protocol_version": 2,
        "schema_version": 2,
        "assets": [
            asset
            or {
                "target": "x86_64-pc-windows-msvc",
                "name": "zmem-svc-x86_64-pc-windows-msvc.exe",
                "size": 4,
                "sha256": hashlib.sha256(b"zmem").hexdigest(),
            }
        ],
    }


def test_release_manifest_is_strict_typed_and_version_matched() -> None:
    manifest = ReleaseManifest.from_mapping(_manifest(), expected_release="1.0.0")
    assert manifest.asset_for("x86_64-pc-windows-msvc").size == 4

    with pytest.raises(ValueError, match="unknown"):
        ReleaseManifest.from_mapping(_manifest() | {"unknown": True}, expected_release="1.0.0")
    with pytest.raises(ValueError, match="expected release"):
        ReleaseManifest.from_mapping(_manifest(), expected_release="0.2.0")
    with pytest.raises(ValueError, match="duplicate"):
        value = _manifest()
        value["assets"] = [value["assets"][0], value["assets"][0]]  # type: ignore[index]
        ReleaseManifest.from_mapping(value, expected_release="1.0.0")


@pytest.mark.parametrize("name", ["../zmem-svc", "folder/zmem-svc", ".", ""])
def test_release_asset_rejects_unsafe_names(name: str) -> None:
    with pytest.raises(ValueError, match="name"):
        ReleaseAsset.from_mapping(
            {
                "target": "x86_64-unknown-linux-musl",
                "name": name,
                "size": 1,
                "sha256": "0" * 64,
            }
        )


def test_copy_verified_streams_and_rejects_integrity_failures(tmp_path: Path) -> None:
    data = b"zmem"
    asset = ReleaseAsset.from_mapping(
        {
            "target": "x86_64-unknown-linux-musl",
            "name": "zmem-svc-x86_64-unknown-linux-musl",
            "size": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        }
    )
    destination = tmp_path / asset.name
    copy_verified(io.BytesIO(data), destination, asset)
    assert destination.read_bytes() == data

    with pytest.raises(ValueError, match="size"):
        copy_verified(io.BytesIO(data + b"!"), tmp_path / "oversize", asset)
    with pytest.raises(ValueError, match="SHA-256"):
        bad = ReleaseAsset(asset.target, asset.name, asset.size, "0" * 64)
        copy_verified(io.BytesIO(data), tmp_path / "bad", bad)


def test_local_discovery_can_report_absence_without_weakening_strict_sources(tmp_path: Path) -> None:
    assert find_service_binary(None, environ={}, package_root=tmp_path, which=lambda _: None) is None
    with pytest.raises(FileNotFoundError, match="ZMEM_SVC_SOURCE"):
        find_service_binary(
            None,
            environ={"ZMEM_SVC_SOURCE": str(tmp_path / "missing")},
            package_root=tmp_path,
            which=lambda _: None,
        )


@pytest.mark.parametrize(
    ("tag", "expected"),
    [("v1.2.3", (1, 2, 3)), ("v10.0.12", (10, 0, 12)), ("1.2.3", None), ("v1.2.3-rc1", None), ("v1.2", None)],
)
def test_stable_release_version_is_exact(tag: object, expected: tuple[int, int, int] | None) -> None:
    assert stable_release_version(tag) == expected


def test_compatible_release_selection_uses_greatest_valid_candidate() -> None:
    releases = [
        {"tag_name": "v2.0.0", "draft": False, "prerelease": False},
        {"tag_name": "v1.4.0", "draft": False, "prerelease": False},
        {"tag_name": "v1.3.0", "draft": False, "prerelease": False},
    ]
    manifests = {
        "v2.0.0": _manifest() | {"release_version": "2.0.0", "protocol_version": 99},
        "v1.4.0": _manifest() | {"release_version": "1.4.0"},
        "v1.3.0": _manifest() | {"release_version": "1.3.0"},
    }

    def opener(url: str, **_kwargs: object):
        tag = next(tag for tag in manifests if f"/{tag}/" in url)
        return io.BytesIO(__import__("json").dumps(manifests[tag]).encode())

    selected = select_compatible_release(
        releases,
        target="x86_64-pc-windows-msvc",
        protocol=2,
        schema=2,
        opener=opener,
    )
    assert selected.version == "1.4.0"


def test_release_inventory_follows_typed_next_page() -> None:
    class Response(io.BytesIO):
        def __init__(self, payload: bytes, link: str | None = None) -> None:
            super().__init__(payload)
            self.headers = {"Link": link} if link else {}

    pages = {
        "inventory": Response(b'[{"tag_name":"v1.0.0"}]', '<next>; rel="next"'),
        "next": Response(b'[{"tag_name":"v1.1.0"}]'),
    }
    releases = list(iter_release_inventory(lambda url, **_kwargs: pages[url], "inventory"))
    assert [release["tag_name"] for release in releases] == ["v1.0.0", "v1.1.0"]


def test_compatible_acquisition_verifies_selected_artifact(tmp_path: Path) -> None:
    manifest = _manifest() | {"release_version": "1.4.0"}

    def opener(url: str, **_kwargs: object):
        if url.endswith("release-manifest.json"):
            return io.BytesIO(__import__("json").dumps(manifest).encode())
        return io.BytesIO(b"zmem")

    with acquire_compatible_release_binary(
        tmp_path,
        expected_protocol=2,
        expected_schema=2,
        releases=iter([{"tag_name": "v1.4.0", "draft": False, "prerelease": False}]),
        environ={},
        system="windows",
        machine="amd64",
        opener=opener,
    ) as acquired:
        assert acquired.version == "1.4.0"
        assert acquired.path.read_bytes() == b"zmem"
