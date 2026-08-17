from pathlib import Path

import pytest

from zmem.service import ServiceManagementError, install_or_upgrade
from zmem.utils.runtime import RuntimeAssemblyError, ServiceIdentity, resolve_runtime_paths


def test_upgrade_reports_host_assembly_failure_without_touching_active_runtime(monkeypatch, tmp_path: Path) -> None:
    paths = resolve_runtime_paths(tmp_path / "home", tmp_path / "runtime", environ={})
    source = tmp_path / "zmem-svc"
    source.write_bytes(b"replacement")
    paths.binary.parent.mkdir(parents=True)
    paths.binary.write_bytes(b"active binary")
    paths.manifest.write_bytes(b"active manifest")
    stopped: list[Path] = []

    monkeypatch.setattr("zmem.service.find_service_binary", lambda *args, **kwargs: source)
    monkeypatch.setattr(
        "zmem.service._binary_identity",
        lambda *args, **kwargs: ServiceIdentity("1.0.0", "1.0.0", 2, 2),
    )
    monkeypatch.setattr("zmem.service._stop_binary", lambda binary, paths: stopped.append(binary))

    def fail(*args: object, **kwargs: object) -> None:
        raise RuntimeAssemblyError("extension-host Python probe terminated by SIGABRT (6)")

    monkeypatch.setattr("zmem.service.stage_runtime", fail)

    with pytest.raises(ServiceManagementError, match=r"could not assemble managed runtime.*SIGABRT \(6\)"):
        install_or_upgrade(paths, binary=source, register=False, upgrade=True)

    assert paths.binary.read_bytes() == b"active binary"
    assert paths.manifest.read_bytes() == b"active manifest"
    assert stopped == []
