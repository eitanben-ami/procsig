# procsig

Inspect local processes by PID or name and render concise signatures.

## About

`procsig` reads the current host's process table through stdlib wrappers, then lets you inspect one process or search by executable name. It is intended for quick local audits, debugging mismatched process state, and lightweight automation when you only need a few process fields rather than a full `ps`/`top` workflow.

## Features

- Inspect a single process by PID.
- Search processes by executable name.
- Stable text and JSON output modes.
- Works on Linux, macOS, and Windows via stdlib backends.
- Zero external dependencies.

## Installation

```bash
git clone https://github.com/eitanben-ami/procsig.git
cd procsig
python -m pip install -e .
```

## Usage

Inspect by PID:

```bash
procsig inspect 1234
```

Search by executable name:

```bash
procsig find python
```

JSON output for automation:

```bash
procsig inspect 1234 --json
procsig find node --json
```

### Exit codes

- `0` — output rendered successfully.
- `1` — invalid arguments.
- `2` — no matching process found.

## Project structure

```
.
├── README.md
├── pyproject.toml
├── .gitignore
├── procsig.py
└── tests
    └── test_procsig.py
```

## Tags

cli, process, inspection, devtools, python, stdlib
