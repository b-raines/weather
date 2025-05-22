#!/bin/bash
cd "$(dirname "$0")"
source .venv/bin/activate
mcp run weather.py 