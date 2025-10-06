import importlib
import importlib.util
import sys


def module_exists(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except ModuleNotFoundError:
        return False


def test_legacy_adapter_package_removed():
    assert not module_exists("adapters"), "legacy adapters package should be removed"
    assert not module_exists("adapters.legacy_manual_mode")
    assert not module_exists("adapters.legacy_mailer")


def test_manual_mode_defaults_reference_manual_modules():
    sm_content = importlib.import_module("simple_mailer.content")
    sys.modules["content"] = sm_content
    email_manual = importlib.import_module("orchestrator.email_manual")
    manual_config_adapter = importlib.import_module("manual.manual_config_adapter")
    manual_preview_adapter = importlib.import_module("manual.manual_preview_adapter")

    adapters = email_manual.ManualModeAdapters.default()

    assert adapters.create_config.__module__ == manual_config_adapter.__name__
    assert adapters.preview_snapshot.__module__ == manual_preview_adapter.__name__
    assert adapters.random_sender_name.__module__ == "simple_mailer.ui_token_helpers"
