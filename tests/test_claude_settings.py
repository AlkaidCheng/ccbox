from ccbox.claude_settings import render_settings


def test_render_includes_rules():
    settings = render_settings(
        {"claude": {"deny": ["Read(/x/**)"], "allow": ["Bash(python *)"]}}
    )
    assert settings["permissions"]["deny"] == ["Read(/x/**)"]
    assert settings["permissions"]["allow"] == ["Bash(python *)"]


def test_render_handles_missing_claude_key():
    assert render_settings({})["permissions"] == {"deny": [], "allow": []}
