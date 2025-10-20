#!/bin/bash
# Quick start script for Media Ingest Pi

cd "$(dirname "$0")"

# Activate virtual environment
source .venv/bin/activate

echo "Starting Media Ingest Pi..."
python3 -u src/main.py

