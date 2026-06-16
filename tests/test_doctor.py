from ccbox.doctor import check


def _errors(issues):
    return [i for i in issues if i.level == "error"]


def test_sensitive_mount_flagged():
    issues = check(
        {"mode": "accident", "mounts": [{"src": "/home/u/.ssh", "mode": "ro"}]}
    )
    assert any(i.level == "error" and "sensitive" in i.message for i in issues)


def test_unknown_runtime_flagged():
    issues = check({"runtime": "nope", "mounts": []})
    assert any(i.level == "error" and "runtime" in i.message for i in issues)


def test_adversarial_requires_network_lockdown():
    issues = check({"mode": "adversarial", "network": "allow", "mounts": []})
    assert any(i.level == "error" and "network" in i.message for i in issues)


def test_adversarial_network_deny_is_ok():
    assert (
        _errors(check({"mode": "adversarial", "network": "deny", "mounts": []})) == []
    )


def test_adversarial_rw_mount_warns():
    issues = check(
        {
            "mode": "adversarial",
            "network": "deny",
            "mounts": [{"src": "/data", "mode": "rw"}],
        }
    )
    assert any(i.level == "warn" for i in issues)


def test_accident_mode_rw_mount_clean():
    issues = check(
        {
            "mode": "accident",
            "network": "allow",
            "mounts": [{"src": "/data", "mode": "rw"}],
        }
    )
    assert _errors(issues) == []
