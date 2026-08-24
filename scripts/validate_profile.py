#!/usr/bin/env python3
from __future__ import annotations

import json
import py_compile
import re
import sys
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
errors: list[str] = []

readme = ROOT / "README.md"
workflow = ROOT / ".github/workflows/refresh.yml"
if not readme.exists():
    errors.append("README.md is missing")
else:
    text = readme.read_text(encoding="utf-8")
    for asset in sorted(set(re.findall(r"(?:src|srcset)=\"(assets/[^\"]+)", text))):
        if not (ROOT / asset).exists():
            errors.append(f"README asset is missing: {asset}")

for config_name in ("assets/skills.json", "assets/projects.json"):
    try:
        json.loads((ROOT / config_name).read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"invalid JSON in {config_name}: {exc}")

for svg in sorted((ROOT / "assets").glob("*.svg")):
    try:
        ElementTree.parse(svg)
    except Exception as exc:
        errors.append(f"invalid SVG in {svg.name}: {exc}")

for script in (ROOT / "scripts/generate_profile.py", ROOT / "scripts/dotify.py"):
    try:
        py_compile.compile(str(script), doraise=True)
    except Exception as exc:
        errors.append(f"Python syntax error in {script.name}: {exc}")

workflow_text = workflow.read_text(encoding="utf-8")
for required in ("permissions:", "contents: write", "actions/checkout@v4", "actions/setup-python@v5", "GITHUB_TOKEN:"):
    if required not in workflow_text:
        errors.append(f"workflow missing required safety/setup marker: {required}")
if "placeholder" in workflow_text.lower():
    errors.append("workflow still contains placeholder text")

if errors:
    print("PROFILE VALIDATION FAILED")
    print("\n".join(f"- {error}" for error in errors))
    sys.exit(1)

print(f"PROFILE VALIDATION PASSED: {len(list((ROOT / 'assets').glob('*.svg')))} SVG assets, README paths, JSON, Python, and workflow checks")
