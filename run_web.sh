#!/usr/bin/env bash
set -e
export PYTHONPATH="$(pwd)"
python -m db.database
python scripts/import_benchmark.py
python -m src.db_reconciliation
uvicorn api.app:app --reload --port 8000
