import importlib
import pathlib


def test_simple_mailer_mailer_module_is_available():
    module = importlib.import_module('simple_mailer.mailer')
    module_path = pathlib.Path(module.__file__)
    assert module_path.parent.name == 'simple_mailer'


def test_mailer_shim_exports_package_function():
    pkg_mailer = importlib.import_module('simple_mailer.mailer')
    shim_mailer = importlib.import_module('mailer')
    assert shim_mailer.send_single_email is pkg_mailer.send_single_email

def test_simple_mailer_core_package_maps_to_legacy():
    pkg_core = importlib.import_module('simple_mailer.core')
    legacy_attachments = importlib.import_module('core.attachments')
    bridged = importlib.import_module('simple_mailer.core.attachments')
    assert pkg_core.__name__ == 'simple_mailer.core'
    assert bridged is legacy_attachments


def test_simple_mailer_orchestrator_maps_to_legacy():
    bridged_ui = importlib.import_module('simple_mailer.orchestrator.ui_shell')
    legacy_ui = importlib.import_module('orchestrator.ui_shell')
    assert bridged_ui is legacy_ui


def test_simple_mailer_exec_maps_to_legacy():
    bridged_pool = importlib.import_module('simple_mailer.exec.threadpool')
    legacy_pool = importlib.import_module('exec.threadpool')
    assert bridged_pool is legacy_pool
