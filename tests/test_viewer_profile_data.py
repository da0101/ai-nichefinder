from nichefinder_cli.viewer_profile_data import _resolved_slug


def test_resolved_slug_defaults_to_active_profile(monkeypatch):
    sentinel_settings = object()
    monkeypatch.setattr("nichefinder_cli.viewer_profile_data.resolve_runtime_settings", lambda: sentinel_settings)
    monkeypatch.setattr("nichefinder_cli.viewer_profile_data.get_active_profile", lambda settings: "restaurant")

    assert _resolved_slug(None) == "restaurant"
    assert _resolved_slug("") == "restaurant"
    assert _resolved_slug("default") == "default"
    assert _resolved_slug("salon") == "salon"
