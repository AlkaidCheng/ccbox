import pytest

import ccbox.runtime as rt


def test_detect_prefers_order(monkeypatch):
    present = {"docker", "podman"}
    monkeypatch.setattr(
        rt.shutil, "which", lambda b: f"/usr/bin/{b}" if b in present else None
    )
    # podman ranks ahead of docker in DETECTION_ORDER
    assert rt.detect_runtime() == "podman"


def test_detect_skips_unimplemented(monkeypatch):
    monkeypatch.setattr(
        rt.shutil, "which", lambda b: f"/x/{b}" if b == "shifter" else None
    )
    assert rt.detect_runtime() is None
    assert rt.detect_runtime(include_unimplemented=True) == "shifter"


def test_detect_none(monkeypatch):
    monkeypatch.setattr(rt.shutil, "which", lambda b: None)
    assert rt.detect_runtime() is None


def test_resolve_explicit():
    assert rt.resolve_runtime({"runtime": "docker"}) == "docker"


def test_resolve_unknown():
    with pytest.raises(ValueError):
        rt.resolve_runtime({"runtime": "nope"})


def test_resolve_auto(monkeypatch):
    monkeypatch.setattr(
        rt.shutil, "which", lambda b: f"/x/{b}" if b == "docker" else None
    )
    assert rt.resolve_runtime({"runtime": "auto"}) == "docker"


def test_resolve_auto_none_found(monkeypatch):
    monkeypatch.setattr(rt.shutil, "which", lambda b: None)
    with pytest.raises(RuntimeError):
        rt.resolve_runtime({"runtime": "auto"})
