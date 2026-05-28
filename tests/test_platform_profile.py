from src.platforms.profile import load_platform_profile, resolve_platform_name


def test_load_android15_profile():
    profile = load_platform_profile("android15")

    assert profile.name == "android15"
    assert profile.test("ringer_mode")["module"] == "AUDIO"
    assert profile.command("ringer_mode", "disable_dnd", "") == "cmd notification set_dnd off"


def test_resolve_platform_name_from_android_version():
    assert resolve_platform_name("auto", "15") == "android15"
    assert resolve_platform_name("android16", "15") == "android16"
