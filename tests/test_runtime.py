import pytest

from ccbox.runtime import get_runtime
from ccbox.runtime.apptainer import ApptainerRuntime, mount_to_bind
from ccbox.runtime.oci import PodmanHpcRuntime, mount_to_volume


def test_mount_to_volume_default_dst():
    assert mount_to_volume({"src": "/x", "same_path": True, "mode": "ro"}) == "/x:/x:ro"


def test_mount_to_volume_explicit_dst():
    assert mount_to_volume({"src": "/a", "dst": "/data", "mode": "rw"}) == "/a:/data:rw"


def test_mount_to_volume_bad_mode():
    with pytest.raises(ValueError):
        mount_to_volume({"src": "/a", "mode": "x"})


def test_oci_build_command():
    config = {
        "mounts": [{"src": "/a", "mode": "ro"}],
        "env": ["FOO=bar"],
        "workdir": "/work",
        "network": "deny",
        "image": "img:latest",
    }
    cmd = PodmanHpcRuntime().build_run_command(config, ["bash"])
    assert cmd[:4] == ["podman-hpc", "run", "--rm", "-it"]
    assert "/a:/a:ro" in cmd
    assert "--network" in cmd and "none" in cmd
    assert cmd[-2:] == ["img:latest", "bash"]


def test_apptainer_build_command():
    config = {"mounts": [{"src": "/a", "dst": "/b", "mode": "rw"}], "image": "img.sif"}
    cmd = ApptainerRuntime().build_run_command(config, ["python"])
    assert cmd[:3] == ["apptainer", "exec", "--containall"]
    assert "/a:/b:rw" in cmd
    assert cmd[-2:] == ["img.sif", "python"]


def test_apptainer_requires_image():
    with pytest.raises(ValueError):
        ApptainerRuntime().build_run_command({"mounts": []}, ["python"])


def test_mount_to_bind_default_dst():
    assert mount_to_bind({"src": "/x", "mode": "ro"}) == "/x:/x:ro"


def test_get_runtime_unknown():
    with pytest.raises(ValueError):
        get_runtime("nope")
