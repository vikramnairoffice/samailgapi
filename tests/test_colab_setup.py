import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import colab_setup


def _fake_playwright_module(tmp_path):
    fake_pkg = tmp_path / "playwright" / "__init__.py"
    fake_pkg.parent.mkdir(parents=True, exist_ok=True)
    fake_pkg.write_text("", encoding="utf-8")
    return types.SimpleNamespace(__file__=str(fake_pkg))


def _run_with_command_capture(monkeypatch, commands, side_effect=None):
    def fake_check_call(cmd, *args, **kwargs):
        commands.append(cmd)
        if side_effect is not None:
            return side_effect(cmd)
        return 0

    monkeypatch.setattr(colab_setup.subprocess, "check_call", fake_check_call)


def test_ensure_browsers_installs_with_deps(monkeypatch, tmp_path):
    fake_playwright = _fake_playwright_module(tmp_path)
    monkeypatch.setitem(sys.modules, "playwright", fake_playwright)
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(tmp_path / "browsers"))
    commands = []

    monkeypatch.setattr(colab_setup, "_chromium_browser_present", lambda root_path=None: False)
    _run_with_command_capture(monkeypatch, commands)

    colab_setup.ensure_playwright_browsers()

    assert commands[0] == colab_setup._playwright_command("install", "chromium", "--with-deps")
    assert commands[1] == colab_setup._playwright_command("install", "--check")


def test_ensure_browsers_falls_back_without_with_deps(monkeypatch, tmp_path):
    fake_playwright = _fake_playwright_module(tmp_path)
    monkeypatch.setitem(sys.modules, "playwright", fake_playwright)
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(tmp_path / "browsers"))

    commands = []

    def side_effect(cmd):
        if "--with-deps" in cmd:
            raise colab_setup.subprocess.CalledProcessError(returncode=1, cmd=cmd)
        return 0

    monkeypatch.setattr(colab_setup, "_chromium_browser_present", lambda root_path=None: False)
    _run_with_command_capture(monkeypatch, commands, side_effect=side_effect)

    colab_setup.ensure_playwright_browsers()

    assert commands[0] == colab_setup._playwright_command("install", "chromium", "--with-deps")
    assert commands[1] == colab_setup._playwright_command("install", "chromium")
    assert commands[2] == colab_setup._playwright_command("install", "--check")


def test_ensure_browsers_warns_when_install_fails(monkeypatch, tmp_path, capsys):
    fake_playwright = _fake_playwright_module(tmp_path)
    monkeypatch.setitem(sys.modules, "playwright", fake_playwright)
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(tmp_path / "browsers"))

    def side_effect(cmd):
        raise colab_setup.subprocess.CalledProcessError(returncode=1, cmd=cmd)

    monkeypatch.setattr(colab_setup, "_chromium_browser_present", lambda root_path=None: False)
    _run_with_command_capture(monkeypatch, [], side_effect=side_effect)

    colab_setup.ensure_playwright_browsers()

    out = capsys.readouterr().out
    assert "Could not download the Playwright Chromium bundle automatically" in out
    assert "playwright install chromium --with-deps" in out


def test_dependency_check_runs_when_browser_already_present(monkeypatch, tmp_path):
    fake_playwright = _fake_playwright_module(tmp_path)
    monkeypatch.setitem(sys.modules, "playwright", fake_playwright)
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(tmp_path / "browsers"))

    commands = []

    monkeypatch.setattr(colab_setup, "_chromium_browser_present", lambda root_path=None: True)
    _run_with_command_capture(monkeypatch, commands)

    colab_setup.ensure_playwright_browsers()

    assert commands == [colab_setup._playwright_command("install", "--check")]
