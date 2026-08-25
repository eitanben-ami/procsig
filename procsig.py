import argparse
import json
import platform
import subprocess
import sys
from typing import Dict, List, Optional


def _load_constants() -> Dict[str, str]:
    system = platform.system().lower()
    if system == "windows":
        return {"ps": "powershell.exe", "args": ["-NoProfile", "-Command", "Get-Process | ConvertTo-Json -Compress"]}
    if system == "darwin":
        return {"ps": "ps", "args": ["-A", "-o", "pid,comm,pcpu,pmem,stat"]}
    return {"ps": "ps", "args": ["-eo", "pid,comm,pcpu,pmem,stat"]}


def _run_ps() -> str:
    constants = _load_constants()
    stdout = ""
    try:
        completed = subprocess.run([constants["ps"]] + constants["args"], check=True, capture_output=True, text=True)
        stdout = completed.stdout
    except FileNotFoundError:
        stdout = ""
    except subprocess.CalledProcessError as exc:
        stdout = exc.output or ""
    return stdout


def _parse_lines(text: str) -> List[Dict[str, str]]:
    system = platform.system().lower()
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return []
    if system == "windows":
        try:
            payload = json.loads(text)
            if isinstance(payload, dict):
                payload = [payload]
            results = []
            for item in payload:
                results.append({
                    "pid": str(item.get("Id", "")),
                    "name": item.get("ProcessName", "") or item.get("Name", ""),
                    "cpu": str(item.get("CPU", "")),
                    "mem": str(item.get("PM", "") or item.get("WorkingSet", "")),
                    "status": str(item.get("Status", "")),
                })
            return results
        except json.JSONDecodeError:
            return []
    header = lines[0].split()
    records = []
    for line in lines[1:]:
        parts = line.split(None, len(header) - 1)
        if len(parts) != len(header):
            continue
        record = dict(zip(header, parts))
        records.append(record)
    return records


_PROCESS_STORE: List[Dict[str, str]] = []
_USE_PROCESS_STORE = False


def set_process_store(entries: List[Dict[str, str]]) -> None:
    global _PROCESS_STORE, _USE_PROCESS_STORE
    _PROCESS_STORE = entries
    _USE_PROCESS_STORE = True


def reset_process_store() -> None:
    global _USE_PROCESS_STORE
    _USE_PROCESS_STORE = False


def get_processes() -> List[Dict[str, str]]:
    if _USE_PROCESS_STORE:
        return list(_PROCESS_STORE)
    text = _run_ps()
    if not text:
        return []
    return _parse_lines(text)


def find_by_name(name: str) -> List[Dict[str, str]]:
    if not name:
        return []
    lowered = name.lower()
    return [proc for proc in get_processes() if lowered in str(proc.get("name", "")).lower()]


def inspect_pid(pid: int) -> Optional[Dict[str, str]]:
    for proc in get_processes():
        if str(proc.get("pid")) == str(pid):
            return proc
    return None


def _format_human(proc: Dict[str, str]) -> str:
    return (
        f"pid={proc.get('pid', '?')}\n"
        f"name={proc.get('name', '?')}\n"
        f"cpu={proc.get('cpu', '?')}\n"
        f"mem={proc.get('mem', '?')}\n"
        f"status={proc.get('status', '?')}"
    )


def _format_json(data) -> str:
    return json.dumps(data, ensure_ascii=True)


def _print_output(data, as_json: bool) -> None:
    if as_json:
        print(_format_json(data))
    else:
        if isinstance(data, dict):
            print(_format_human(data))
        else:
            for index, item in enumerate(data, 1):
                print(f"--- process {index} ---")
                print(_format_human(item))


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="procsig", description="Inspect local processes by PID or name.")
    subparsers = parser.add_subparsers(dest="command")

    inspect_parser = subparsers.add_parser("inspect", help="Inspect a process by PID.")
    inspect_parser.add_argument("pid", type=int, help="Process ID to inspect.")
    inspect_parser.add_argument("--json", action="store_true", help="Emit JSON output.")

    find_parser = subparsers.add_parser("find", help="Find processes by executable name.")
    find_parser.add_argument("name", help="Executable name substring.")
    find_parser.add_argument("--json", action="store_true", help="Emit JSON output.")

    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code) if exc.code is not None else 0
    if not args.command:
        parser.print_help()
        return 1

    if args.command == "inspect":
        proc = inspect_pid(args.pid)
        if proc is None:
            print(f"No process with PID {args.pid}", file=sys.stderr)
            return 2
        _print_output(proc, args.json)
        return 0

    matches = find_by_name(args.name)
    if not matches:
        print(f"No matching process for name '{args.name}'", file=sys.stderr)
        return 2
    _print_output(matches, args.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
