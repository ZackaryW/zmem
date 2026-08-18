from __future__ import annotations

import os
import signal
import subprocess
from pathlib import Path

import pytest

from zmem.utils.runtime import (
    RuntimeAssemblyError,
    RuntimeManifest,
    RuntimePaths,
    ServiceIdentity,
    StagedRuntime,
    activate_runtime,
    assemble_host,
    discover_service_binary,
    resolve_runtime_paths,
    sha256_file,
    stage_runtime,
)


def test_runtime_path_precedence(tmp_path: Path) -> None:
    environment = {
        "ZMEM_HOME": str(tmp_path / "environment-home"),
        "ZMEM_RUNTIME_ROOT": str(tmp_path / "environment-runtime"),
    }
    selected = resolve_runtime_paths(environ=environment)
    assert selected.home == (tmp_path / "environment-home").resolve()
    assert selected.root == (tmp_path / "environment-runtime").resolve()

    explicit = resolve_runtime_paths(
        tmp_path / "explicit-home",
        tmp_path / "explicit-runtime",
        environ=environment,
    )
    assert explicit.home == (tmp_path / "explicit-home").resolve()
    assert explicit.root == (tmp_path / "explicit-runtime").resolve()


def test_runtime_root_defaults_beneath_selected_home(tmp_path: Path) -> None:
    paths = resolve_runtime_paths(tmp_path / "home", environ={})
    assert paths.root == (tmp_path / "home" / "runtime").resolve()
    assert paths.binary.parent == paths.root / "binary"
    assert paths.manifest == paths.root / "runtime.json"


@pytest.mark.skipif(os.name != "nt", reason="packaged .exe discovery is Windows-specific")
def test_binary_discovery_ladder(tmp_path: Path) -> None:
    explicit = tmp_path / "explicit.exe"
    environment_binary = tmp_path / "environment.exe"
    packaged = tmp_path / "package" / "_native" / "zmem-svc.exe"
    path_binary = tmp_path / "path.exe"
    for candidate in (explicit, environment_binary, packaged, path_binary):
        candidate.parent.mkdir(parents=True, exist_ok=True)
        candidate.write_bytes(b"binary")

    assert (
        discover_service_binary(explicit, environ={}, package_root=tmp_path / "package", which=lambda _: None)
        == explicit
    )
    assert (
        discover_service_binary(
            None,
            environ={"ZMEM_SVC_SOURCE": str(environment_binary)},
            package_root=tmp_path / "package",
            which=lambda _: str(path_binary),
        )
        == environment_binary
    )
    assert (
        discover_service_binary(None, environ={}, package_root=tmp_path / "package", which=lambda _: str(path_binary))
        == packaged
    )
    packaged.unlink()
    assert (
        discover_service_binary(None, environ={}, package_root=tmp_path / "package", which=lambda _: str(path_binary))
        == path_binary
    )


def test_explicit_or_environment_binary_must_exist(tmp_path: Path) -> None:
    fallback = tmp_path / "fallback.exe"
    fallback.write_bytes(b"fallback")
    with pytest.raises(FileNotFoundError, match="explicit"):
        discover_service_binary(
            tmp_path / "missing.exe", environ={}, package_root=tmp_path, which=lambda _: str(fallback)
        )
    with pytest.raises(FileNotFoundError, match="ZMEM_SVC_SOURCE"):
        discover_service_binary(
            None,
            environ={"ZMEM_SVC_SOURCE": str(tmp_path / "missing.exe")},
            package_root=tmp_path,
            which=lambda _: str(fallback),
        )


def _manifest(paths: RuntimePaths, **updates: object) -> RuntimeManifest:
    values = {
        "manifest_version": 1,
        "release_version": "1.0.0",
        "binary_version": "1.0.0",
        "host_version": "1.0.0",
        "protocol_version": 2,
        "schema_version": 2,
        "sha256": "a" * 64,
        "installation_id": "install-1",
        "binary": str(paths.binary),
        "host": str(paths.host_python),
        "installed_at": "2026-08-15T00:00:00+00:00",
    }
    values.update(updates)
    return RuntimeManifest.from_mapping(values)


def test_manifest_is_strict_typed_and_atomic(tmp_path: Path) -> None:
    paths = resolve_runtime_paths(tmp_path / "home", tmp_path / "runtime", environ={})
    manifest = _manifest(paths)
    manifest.write_atomic(paths.manifest)
    assert RuntimeManifest.read(paths.manifest) == manifest
    assert not paths.manifest.with_suffix(".json.tmp").exists()

    invalid = manifest.to_mapping() | {"unknown": True}
    with pytest.raises(ValueError, match="unknown"):
        RuntimeManifest.from_mapping(invalid)
    with pytest.raises(ValueError, match="protocol_version"):
        RuntimeManifest.from_mapping(manifest.to_mapping() | {"protocol_version": "1"})


def test_manifest_reads_v1_and_writes_independent_version_2(tmp_path: Path) -> None:
    paths = resolve_runtime_paths(tmp_path / "home", tmp_path / "runtime", environ={})
    legacy = _manifest(paths, release_version="1.0.0", binary_version="0.9.0", host_version="1.0.0")
    assert legacy.host_version == "1.0.0"
    assert legacy.binary_version == "0.9.0"
    written = legacy.to_mapping()
    assert written["manifest_version"] == 2
    assert "release_version" not in written
    round_trip = RuntimeManifest.from_mapping(written)
    assert round_trip.host_version == "1.0.0"
    assert round_trip.binary_version == "0.9.0"


def test_sha256_streams_file(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact"
    artifact.write_bytes(b"zmem")
    assert sha256_file(artifact) == "c13a0f5ba8445a12152a8aa2e53da4eeb28a6533188713d242cfe8b5fdc22ca2"


def test_host_assembly_copies_package_outside_current_environment(tmp_path: Path) -> None:
    package_root = Path(__file__).parents[1] / "src" / "zmem"
    python = assemble_host(tmp_path / "host", package_root)
    if os.name != "nt":
        assert python.is_symlink()
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    completed = subprocess.run(
        [python, "-c", "import zmem; print(zmem.__file__)"],
        env=environment,
        capture_output=True,
        text=True,
        check=True,
    )
    assert Path(completed.stdout.strip()).is_relative_to(tmp_path / "host")


@pytest.mark.parametrize(
    ("returncode", "stderr", "expected"),
    [
        (-signal.SIGABRT, None, f"terminated by SIGABRT ({signal.SIGABRT})"),
        (7, "missing runtime library\n", "exited with status 7: missing runtime library"),
    ],
)
def test_host_assembly_reports_python_probe_failure(
    monkeypatch,
    tmp_path: Path,
    returncode: int,
    stderr: str | None,
    expected: str,
) -> None:
    def abort(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        raise subprocess.CalledProcessError(returncode, args[0], stderr=stderr)

    monkeypatch.setattr("zmem.utils.runtime.subprocess.run", abort)

    with pytest.raises(RuntimeAssemblyError) as exc_info:
        assemble_host(tmp_path / "host", Path(__file__).parents[1] / "src" / "zmem")

    assert expected in str(exc_info.value)


def test_stage_runtime_builds_complete_versionless_target(tmp_path: Path) -> None:
    paths = resolve_runtime_paths(tmp_path / "home", tmp_path / "runtime", environ={})
    binary = tmp_path / "source.exe"
    binary.write_bytes(b"native")
    staged = stage_runtime(
        paths,
        binary,
        Path(__file__).parents[1] / "src" / "zmem",
        ServiceIdentity("1.0.0", "1.0.0", 1, 1),
    )
    staged_paths = RuntimePaths.for_root(paths.home, staged.root)
    assert staged_paths.binary.read_bytes() == b"native"
    assert staged_paths.host_python.exists()
    assert RuntimeManifest.read(staged_paths.manifest) == staged.manifest
    assert staged.manifest.binary == paths.binary
    assert staged.manifest.host == paths.host_python


def test_stage_runtime_removes_partial_staging_after_host_failure(monkeypatch, tmp_path: Path) -> None:
    paths = resolve_runtime_paths(tmp_path / "home", tmp_path / "runtime", environ={})
    binary = tmp_path / "source.exe"
    binary.write_bytes(b"native")

    def fail(*args: object, **kwargs: object) -> Path:
        raise RuntimeAssemblyError("extension-host Python probe terminated by SIGABRT (6)")

    monkeypatch.setattr("zmem.utils.runtime.assemble_host", fail)

    with pytest.raises(RuntimeAssemblyError, match="SIGABRT"):
        stage_runtime(
            paths,
            binary,
            Path(__file__).parents[1] / "src" / "zmem",
            ServiceIdentity("1.0.0", "1.0.0", 1, 1),
        )

    assert not paths.staging_root.exists() or not any(paths.staging_root.iterdir())


def test_activation_rolls_back_failed_healthcheck(tmp_path: Path) -> None:
    paths = resolve_runtime_paths(tmp_path / "home", tmp_path / "runtime", environ={})
    paths.binary.parent.mkdir(parents=True)
    paths.binary.write_bytes(b"old")
    paths.host_dir.mkdir()
    paths.host_python.parent.mkdir(parents=True, exist_ok=True)
    paths.host_python.write_bytes(b"old host")
    old = _manifest(paths)
    old.write_atomic(paths.manifest)

    staged_root = paths.staging_root / "install-2"
    staged_paths = RuntimePaths.for_root(paths.home, staged_root)
    staged_paths.binary.parent.mkdir(parents=True)
    staged_paths.binary.write_bytes(b"new")
    staged_paths.host_python.parent.mkdir(parents=True)
    staged_paths.host_python.write_bytes(b"new host")
    new = _manifest(paths, installation_id="install-2", sha256="b" * 64)
    new.write_atomic(staged_paths.manifest)

    with pytest.raises(RuntimeError, match="health"):
        activate_runtime(paths, StagedRuntime(staged_root, new), lambda _manifest: False)

    assert paths.binary.read_bytes() == b"old"
    assert RuntimeManifest.read(paths.manifest) == old
    assert not paths.previous.exists()
