from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import procsig  # noqa: E402


def _current_pid() -> int:
    return os.getpid()


def _inject_process_store(monkeypatch):
    fake_pid = _current_pid()
    monkeypatch.setattr("os.getpid", lambda: fake_pid)
    procsig.set_process_store([
        {
            "pid": str(fake_pid),
            "name": "python",
            "cpu": "0.1",
            "mem": "0.2",
            "status": "Ss",
        }
    ])


def test_get_processes_returns_list():
    assert isinstance(procsig.get_processes(), list)


def test_inspect_current_process_contains_fields(monkeypatch):
    _inject_process_store(monkeypatch)
    pid = _current_pid()
    proc = procsig.inspect_pid(pid)
    assert proc is not None
    assert "pid" in proc
    assert "name" in proc
    assert str(proc["pid"]) == str(pid)


def test_find_current_process_by_current_exe_name(monkeypatch):
    _inject_process_store(monkeypatch)
    proc = procsig.inspect_pid(_current_pid())
    assert proc is not None
    matches = procsig.find_by_name(proc["name"])
    assert any(str(m["pid"]) == str(_current_pid()) for m in matches)


def test_inspect_unknown_pid_returns_none(monkeypatch):
    _inject_process_store(monkeypatch)
    assert procsig.inspect_pid(999999) is None


def test_find_unknown_name_returns_empty(monkeypatch):
    _inject_process_store(monkeypatch)
    assert procsig.find_by_name("__no_such_process__procsig__") == []


def test_format_human_contains_pid(monkeypatch):
    _inject_process_store(monkeypatch)
    proc = procsig.inspect_pid(_current_pid())
    assert proc is not None
    human = procsig._format_human(proc)
    assert f"pid={proc['pid']}" in human
    assert "cpu=" in human
    assert "mem=" in human


def test_format_json_is_valid_json(monkeypatch):
    _inject_process_store(monkeypatch)
    proc = procsig.inspect_pid(_current_pid())
    assert proc is not None
    raw = procsig._format_json(proc)
    parsed = json.loads(raw)
    assert parsed["pid"] == proc["pid"]
    assert parsed["name"] == proc["name"]


def test_main_inspect_positive_exit_zero(monkeypatch):
    _inject_process_store(monkeypatch)
    assert procsig.main(["inspect", str(_current_pid())]) == 0


def test_main_inspect_missing_negative_exit_two(monkeypatch):
    _inject_process_store(monkeypatch)
    assert procsig.main(["inspect", "999999"]) == 2


def test_main_find_positive_exit_zero(monkeypatch):
    _inject_process_store(monkeypatch)
    proc = procsig.inspect_pid(_current_pid())
    assert proc is not None
    assert procsig.main(["find", proc["name"]]) == 0


def test_main_find_negative_exit_two(monkeypatch):
    _inject_process_store(monkeypatch)
    assert procsig.main(["find", "__no_such_process__procsig__"]) == 2


def test_main_no_command_exits_one():
    assert procsig.main([]) == 1


def test_main_help_exits_zero():
    assert procsig.main(["--help"]) == 0
