from ccbox.image import image_kind, pick_runtime, validate


def test_image_kind():
    assert image_kind("python:3.12") == "oci-tag"
    assert image_kind("myproj:latest") == "oci-tag"
    assert image_kind("docker://docker.io/library/python:3.12") == "url"
    assert image_kind("oras://reg/img:tag") == "url"
    assert image_kind("/path/to/env.sif") == "sif"
    assert image_kind("env.SIF") == "sif"  # case-insensitive


def test_validate_oci_runtime():
    assert validate("python:3.12", "docker") == "direct"
    assert validate("docker://x", "docker") == "direct"
    assert validate("env.sif", "docker") == "incompatible"


def test_validate_apptainer():
    assert validate("env.sif", "apptainer") == "direct"
    assert validate("docker://x", "apptainer") == "direct"
    assert validate("python:3.12", "apptainer") == "convert"  # oci tag -> sif


def test_validate_bwrap_incompatible():
    assert validate("python:3.12", "bwrap") == "incompatible"


def test_pick_runtime():
    # a .sif: only apptainer/singularity accept it
    assert (
        pick_runtime("env.sif", ["docker", "apptainer", "singularity"]) == "apptainer"
    )
    # an OCI tag: docker accepts it directly
    assert pick_runtime("python:3.12", ["docker", "apptainer"]) == "docker"
    # bwrap can't take anything
    assert pick_runtime("python:3.12", ["bwrap"]) is None
