import pytest

from simple_mailer.orchestrator import modes


def _make_mode(mode_id, title="Title"):
    return modes.Mode(
        id=mode_id,
        title=title,
        build_ui=lambda: f"ui-{mode_id}",
        to_runner_config=lambda payload, adapters=None: {"payload": payload},
        run=lambda config, adapters=None: iter(()),
    )


def test_register_and_get_mode(monkeypatch):
    monkeypatch.setattr(modes, "_MODE_REGISTRY", {})

    mode = _make_mode("manual")
    modes.register_mode(mode)

    assert modes.get_mode("manual") is mode
    assert list(modes.iter_modes()) == [mode]


def test_register_mode_rejects_duplicates(monkeypatch):
    monkeypatch.setattr(modes, "_MODE_REGISTRY", {})

    modes.register_mode(_make_mode("manual"))

    with pytest.raises(ValueError):
        modes.register_mode(_make_mode("manual"))


def test_get_mode_unknown(monkeypatch):
    monkeypatch.setattr(modes, "_MODE_REGISTRY", {})

    with pytest.raises(KeyError):
        modes.get_mode("missing")

