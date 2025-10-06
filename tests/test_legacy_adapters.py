import importlib
import pathlib

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_legacy_adapter_package_removed():
    assert not (PROJECT_ROOT / 'adapters').exists()


def test_manual_mode_defaults_reference_manual_modules():
    email_manual = importlib.import_module('simple_mailer.orchestrator.email_manual')
    manual_config_adapter = importlib.import_module('simple_mailer.manual.manual_config_adapter')
    manual_preview_adapter = importlib.import_module('simple_mailer.manual.manual_preview_adapter')

    adapters = email_manual.ManualModeAdapters.default()

    assert adapters.create_config.__module__ == manual_config_adapter.__name__
    assert adapters.preview_snapshot.__module__ == manual_preview_adapter.__name__
    assert adapters.random_sender_name.__module__ == 'simple_mailer.ui_token_helpers'
