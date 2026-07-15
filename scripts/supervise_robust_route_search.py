#!/usr/bin/env python3
"""Supervise the resumable robust route experiment on a remote GPU host.

The search runner checkpoints every completed route. This supervisor keeps the
two planned GPU lanes moving, restarts only a stopped stage, and then gates
finalization, controls, and analysis on their prerequisite artifacts.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import time

from vlm_bench.io import write_json


ROOT = Path("results/robust-route-search-qwen25-vl-3b")
LANES = (
    ("generic", "object", "spatial"),
    ("attribute", "counting", "ocr"),
)
MAX_ATTEMPTS = 2


def process_running(*needles: str) -> bool:
    """Return whether a live process command line contains every needle."""
    for entry in Path("/proc").glob("[0-9]*"):
        try:
            command = (entry / "cmdline").read_bytes().replace(b"\0", b" ").decode()
        except (FileNotFoundError, PermissionError, UnicodeDecodeError):
            continue
        if all(needle in command for needle in needles):
            return True
    return False


def family_status(family: str) -> str:
    path = ROOT / "families" / family / "state.json"
    if not path.exists():
        return "pending"
    return json.loads(path.read_text(encoding="utf-8")).get("status", "pending")


def load_state(path: Path) -> dict:
    if not path.exists():
        return {"schema_version": 1, "attempts": {}, "events": []}
    return json.loads(path.read_text(encoding="utf-8"))


def record(state: dict, message: str) -> None:
    stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    state["events"] = (state.get("events", []) + [{"at": stamp, "message": message}])[-100:]
    print(f"[{stamp}] {message}", flush=True)


def launch(command: list[str], log_path: Path, dry_run: bool) -> None:
    print("launch: " + " ".join(command), flush=True)
    if dry_run:
        return
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("ab", buffering=0) as handle:
        subprocess.Popen(command, stdout=handle, stderr=subprocess.STDOUT, start_new_session=True)


def maybe_launch(
    *,
    key: str,
    status: str,
    needles: tuple[str, ...],
    command: list[str],
    log_path: Path,
    state: dict,
    dry_run: bool,
) -> None:
    if status == "complete" or process_running(*needles):
        return
    attempts = int(state["attempts"].get(key, 0))
    if attempts >= MAX_ATTEMPTS:
        record(state, f"{key} is stopped after {attempts} launch attempts; manual review required")
        return
    state["attempts"][key] = attempts + 1
    record(state, f"launching {key} from its checkpoint (attempt {attempts + 1}/{MAX_ATTEMPTS})")
    launch(command, log_path, dry_run)


def python_command(script: str, *arguments: str) -> list[str]:
    return [str(Path(".venv/bin/python")), script, *arguments]


def supervise_once(state: dict, dry_run: bool) -> bool:
    for lane in LANES:
        next_family = next((family for family in lane if family_status(family) != "complete"), None)
        if next_family is None:
            continue
        maybe_launch(
            key=f"family:{next_family}",
            status=family_status(next_family),
            needles=("scripts/run_robust_route_search.py", "--family", next_family),
            command=python_command("scripts/run_robust_route_search.py", "--family", next_family),
            log_path=Path("logs") / f"robust-{next_family}.log",
            state=state,
            dry_run=dry_run,
        )

    families_complete = all(family_status(family) == "complete" for lane in LANES for family in lane)
    frozen = ROOT / "frozen_routes.json"
    if families_complete and not frozen.exists():
        maybe_launch(
            key="finalize",
            status="pending",
            needles=("scripts/run_robust_route_search.py", "--finalize"),
            command=python_command("scripts/run_robust_route_search.py", "--finalize"),
            log_path=Path("logs/robust-finalize.log"),
            state=state,
            dry_run=dry_run,
        )

    controls_state = ROOT / "controls" / "state.json"
    controls_complete = controls_state.exists() and json.loads(controls_state.read_text(encoding="utf-8")).get("status") == "complete"
    if frozen.exists() and not controls_complete:
        maybe_launch(
            key="controls",
            status="pending",
            needles=("scripts/run_robust_route_controls.py",),
            command=python_command("scripts/run_robust_route_controls.py"),
            log_path=Path("logs/robust-controls.log"),
            state=state,
            dry_run=dry_run,
        )

    analysis = ROOT / "analysis" / "analysis.json"
    if controls_complete and not analysis.exists():
        maybe_launch(
            key="analysis",
            status="pending",
            needles=("scripts/analyze_robust_route_search.py",),
            command=python_command("scripts/analyze_robust_route_search.py"),
            log_path=Path("logs/robust-analysis.log"),
            state=state,
            dry_run=dry_run,
        )
    return analysis.exists()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interval-seconds", type=int, default=60)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.interval_seconds < 5:
        raise ValueError("interval must be at least five seconds")

    os.environ.setdefault("PYTHONPATH", "src")
    state_path = ROOT / "supervisor-state.json"
    while True:
        state = load_state(state_path)
        complete = supervise_once(state, args.dry_run)
        if not args.dry_run:
            write_json(state_path, state)
        if args.once or complete:
            return
        time.sleep(args.interval_seconds)


if __name__ == "__main__":
    main()
