#!/usr/bin/env python3
"""Framework data loader — emit meta artefact JSON to stdout."""
import sys
import tempfile
from pathlib import Path

from pipeline.build_meta import build

out = Path(tempfile.mkstemp(suffix=".json")[1])
build("data/cfd.duckdb", "src/content/captions.json", out)
sys.stdout.write(out.read_text())
