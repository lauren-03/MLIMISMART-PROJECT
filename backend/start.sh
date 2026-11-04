#!/bin/sh
# Start-up for the hosted version: create the tables and demo data, then run the API.
set -e
python seed.py
exec python -m uvicorn app.main:app --host 0.0.0.0 --port 7860
