#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"
python_bin="${PYTHON:-python3}"
venv_python=".venv/bin/python"

if [[ ! -x "$venv_python" ]]; then
  "$python_bin" -m venv .venv
fi

if ! "$venv_python" -c 'import fastapi, uvicorn, multipart, pymupdf, PIL, pytesseract' >/dev/null 2>&1; then
  "$venv_python" -m pip install -r Requirements.txt
fi

host="${HOST:-127.0.0.1}"
port="${PORT:-8000}"
exec .venv/bin/uvicorn mortgage_processor.api:app --host "$host" --port "$port" --reload
