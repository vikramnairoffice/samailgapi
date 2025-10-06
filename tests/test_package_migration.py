import importlib
import pathlib

import pytest

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_simple_mailer_mailer_module_is_available():
    module = importlib.import_module('simple_mailer.mailer')
    module_path = pathlib.Path(module.__file__)
    assert module_path.parent.name == 'simple_mailer'


@pytest.mark.parametrize('path', [
    PROJECT_ROOT / 'mailer.py',
    PROJECT_ROOT / 'ui.py',
    PROJECT_ROOT / 'ui_token_helpers.py',
    PROJECT_ROOT / 'content.py',
    PROJECT_ROOT / 'colab_setup.py',
])
def test_legacy_module_files_removed(path):
    assert not path.exists()


@pytest.mark.parametrize('path', [
    PROJECT_ROOT / 'core',
    PROJECT_ROOT / 'manual',
    PROJECT_ROOT / 'orchestrator',
    PROJECT_ROOT / 'senders',
    PROJECT_ROOT / 'exec',
    PROJECT_ROOT / 'credentials',
])
def test_legacy_namespace_directories_removed(path):
    assert not path.exists()

