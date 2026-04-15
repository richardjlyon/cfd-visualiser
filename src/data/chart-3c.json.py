#!/usr/bin/env python3
"""Framework data loader — emit chart-3c view-model JSON to stdout."""
import sys
import tempfile
from pathlib import Path

from pipeline.build_chart_3c import build

out = Path(tempfile.mkstemp(suffix=".json")[1])
build("data/cfd.duckdb", out)
sys.stdout.write(out.read_text())
