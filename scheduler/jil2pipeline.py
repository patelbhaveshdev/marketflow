#!/usr/bin/env python3
"""jil2pipeline: migrate legacy AutoSys JIL definitions to MarketFlow pipeline JSON.

Born from a real-world migration of 300+ enterprise scheduler jobs to a
modern orchestration platform. Parses the practical subset of JIL used by
batch streams (insert_job, command, condition, start_times, n_retrys,
priority) and emits the JSON consumed by the MarketFlow .NET orchestrator.

Usage:
    python jil2pipeline.py jobs/daily_trades.jil jobs/eod_reconciliation.jil \
        --out ../src/MarketFlow.Api/pipelines/trades_pipeline.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_ATTR = re.compile(r"^\s*([a-z_]+)\s*:\s*(.+?)\s*$", re.IGNORECASE)
_COND_SUCCESS = re.compile(r"s\(([^)]+)\)", re.IGNORECASE)
_PRIORITY_MAP = {1: "Critical", 2: "High", 3: "Normal", 4: "Low"}


def strip_comments(text: str) -> str:
    """Remove /* ... */ block comments."""
    return re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)


def parse_jil(text: str) -> list[dict]:
    """Parse JIL text into a list of MarketFlow job dicts."""
    jobs: list[dict] = []
    current: dict | None = None

    for line in strip_comments(text).splitlines():
        match = _ATTR.match(line)
        if not match:
            continue
        key, value = match.group(1).lower(), match.group(2).strip().strip('"')

        if key == "insert_job":
            current = {"name": value, "command": "", "dependsOn": []}
            jobs.append(current)
        elif current is None:
            continue
        elif key == "command":
            current["command"] = value
        elif key == "description":
            current["description"] = value
        elif key == "machine":
            current["machine"] = value
        elif key == "condition":
            current["dependsOn"] = _COND_SUCCESS.findall(value)
        elif key == "start_times":
            hh_mm = value.strip().strip('"')
            current["startTime"] = hh_mm if hh_mm.count(":") == 2 else f"{hh_mm}:00"
        elif key == "run_calendar":
            current["calendar"] = value
        elif key == "n_retrys":
            current["maxRetries"] = int(value)
        elif key == "priority":
            current["priority"] = _PRIORITY_MAP.get(int(value), "Normal")

    return jobs


def validate(jobs: list[dict]) -> list[str]:
    """Return a list of validation errors (empty when clean)."""
    errors = []
    names = {j["name"] for j in jobs}
    for job in jobs:
        if not job.get("command"):
            errors.append(f"{job['name']}: missing command")
        for dep in job["dependsOn"]:
            if dep not in names:
                errors.append(f"{job['name']}: unknown dependency '{dep}'")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("jil_files", nargs="+", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--allow-external-deps", action="store_true",
                        help="Skip unknown-dependency validation (cross-stream conditions).")
    args = parser.parse_args(argv)

    jobs: list[dict] = []
    for path in args.jil_files:
        jobs.extend(parse_jil(path.read_text()))

    errors = [] if args.allow_external_deps else validate(jobs)
    if errors:
        for error in errors:
            print(f"ERROR {error}", file=sys.stderr)
        return 1

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(jobs, indent=2) + "\n")
    print(f"Migrated {len(jobs)} job(s) -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
