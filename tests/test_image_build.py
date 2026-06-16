import ccbox.image_build as ib
from ccbox.image_build import build_image_command, detect_builder


def test_build_image_command():
    command = build_image_command("docker", "img:latest", "/p/Dockerfile", "/p")
    assert command == [
        "docker",
        "build",
        "-t",
        "img:latest",
        "-f",
        "/p/Dockerfile",
        "/p",
    ]


def test_detect_builder_prefers_order(monkeypatch):
    present = {"podman", "docker"}
    monkeypatch.setattr(
        ib.shutil, "which", lambda b: f"/x/{b}" if b in present else None
    )
    # podman-hpc ranks first but is absent; podman is preferred over docker
    assert detect_builder() == "podman"


def test_detect_builder_none(monkeypatch):
    monkeypatch.setattr(ib.shutil, "which", lambda b: None)
    assert detect_builder() is None
