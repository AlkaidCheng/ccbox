import pytest

from ccbox.image_pull import pull_image_command, sif_filename, strip_scheme


def test_strip_scheme_removes_transport():
    assert strip_scheme("docker://registry/img:tag") == "registry/img:tag"
    assert strip_scheme("oras://host/img:1") == "host/img:1"


def test_strip_scheme_noop_without_scheme():
    assert strip_scheme("registry/img:tag") == "registry/img:tag"


def test_sif_filename_is_readable_and_hashed():
    name = sif_filename("docker://registry/org/img:tag")
    assert name.startswith("img_tag-")
    assert name.endswith(".sif")


def test_sif_filename_stable_and_distinct():
    a = sif_filename("docker://registry-a/img:tag")
    b = sif_filename("docker://registry-b/img:tag")
    assert a == sif_filename("docker://registry-a/img:tag")  # stable
    assert a != b  # distinct registries do not collide


def test_pull_command_oci_strips_scheme():
    assert pull_image_command("docker", "docker", "docker://img:tag") == [
        "docker",
        "pull",
        "img:tag",
    ]


def test_pull_command_sif_includes_destination():
    assert pull_image_command(
        "apptainer", "apptainer", "docker://img:tag", "/c/x.sif"
    ) == ["apptainer", "pull", "/c/x.sif", "docker://img:tag"]


def test_pull_command_sif_requires_destination():
    with pytest.raises(ValueError, match="destination .sif"):
        pull_image_command("apptainer", "apptainer", "docker://img:tag")


def test_pull_command_rejects_incapable_runtime():
    with pytest.raises(ValueError, match="cannot pull"):
        pull_image_command("bwrap", "bwrap", "docker://img:tag")
