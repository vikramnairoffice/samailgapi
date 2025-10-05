import gardio_ui


def test_blueprint_dimensions():
    image = gardio_ui.create_blueprint("email_manual")
    assert image.size == gardio_ui.CANVAS_SIZE


def test_guard_focus_is_subset():
    available = set(gardio_ui.FEATURE_CHOICES)
    for spec in gardio_ui.LAYOUT_SPECS.values():
        missing = [item for item in spec.guard_focus if item not in available]
        assert not missing, f"Guard focus not in feature choices: {missing}"
