#!/usr/bin/env python3
"""Cross-platform worker heartbeat transport/proving probe.

SMOKE mode proves that a worker can edit its heartbeat file, commit, and push.
SMOKE heartbeats do NOT count toward the 15-minute proving streak.

PROVE mode performs real proving heartbeats. Default is 3 heartbeats, 900 seconds
apart. On the third consecutive on-time heartbeat it switches the file to
STEADY_HOURLY.

Run only from the assigned worker branch.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
import time
from pathlib import Path

LANES = {
    "A": ("worker/v15-assisted-application", Path("coordination/heartbeats/LANE_A.md")),
    "B": ("worker/recruiting-ops", Path("coordination/heartbeats/LANE_B.md")),
    "C": ("worker/live-data-foundations", Path("coordination/heartbeats/LANE_C.md")),
    "D": ("worker/v23-foundations", Path("coordination/heartbeats/LANE_D.md")),
    "SCOUT": ("scout/qa-prep", Path("coordination/heartbeats/SCOUT.md")),
}


def run(*args: str, capture: bool = False) -> str:
    proc = subprocess.run(
        list(args),
        check=True,
        text=True,
        capture_output=capture,
    )
    return proc.stdout.strip() if capture else ""


def replace_metadata(text: str, key: str, value: str) -> str:
    pattern = rf"(?m)^{re.escape(key)}:\s*.*$"
    replacement = f"{key}: {value}"
    if re.search(pattern, text):
        return re.sub(pattern, replacement, text, count=1)
    # Insert metadata after H1 when missing.
    lines = text.splitlines()
    insert_at = 1 if lines and lines[0].startswith("#") else 0
    lines.insert(insert_at, replacement)
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def read_metadata(text: str, key: str) -> str | None:
    m = re.search(rf"(?m)^{re.escape(key)}:\s*(.*?)\s*$", text)
    return m.group(1) if m else None


def parse_utc(value: str | None) -> dt.datetime | None:
    if not value or value.lower() == "null":
        return None
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.astimezone(dt.UTC)
    except ValueError:
        return None


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.UTC).replace(microsecond=0)


def iso_z(value: dt.datetime) -> str:
    return value.astimezone(dt.UTC).isoformat().replace("+00:00", "Z")


def append_entry(text: str, entry: str) -> str:
    marker = "## Entries"
    if marker not in text:
        return text.rstrip() + f"\n\n{marker}\n\n{entry}\n"
    before, after = text.split(marker, 1)
    after = after.lstrip("\n")
    return before.rstrip() + f"\n\n{marker}\n\n{entry}\n\n" + after


def commit_push(path: Path, message: str) -> None:
    run("git", "add", str(path))
    run("git", "commit", "-m", message)
    run("git", "push", "origin", "HEAD")


def ensure_branch(expected: str) -> None:
    actual = run("git", "branch", "--show-current", capture=True)
    if actual != expected:
        raise SystemExit(
            f"Wrong branch. Expected {expected!r}, current branch is {actual!r}. "
            "Switch to the assigned branch before running the probe."
        )


def do_smoke(lane: str, path: Path, index: int, count: int) -> None:
    now = utc_now()
    text = path.read_text(encoding="utf-8")
    entry = (
        f"### {iso_z(now)} — {lane} SMOKE PROBE {index}/{count}\n\n"
        "This is a transport smoke test only. It does not count toward PROVING_15M.\n\n"
        "Lead action requested:\n- NONE\n\n"
        "Review state:\n- WORKING"
    )
    text = append_entry(text, entry)
    text = replace_metadata(text, "smoke_last_check_in_utc", iso_z(now))
    text = replace_metadata(text, "smoke_probe_count", str(index))
    path.write_text(text, encoding="utf-8")
    commit_push(path, f"heartbeat-smoke({lane}): {index}/{count}")


def do_prove(lane: str, path: Path, index: int, count: int) -> None:
    now = utc_now()
    text = path.read_text(encoding="utf-8")
    previous = parse_utc(read_metadata(text, "last_check_in_utc"))
    previous_streak_raw = read_metadata(text, "consecutive_on_time")
    try:
        previous_streak = int(previous_streak_raw or "0")
    except ValueError:
        previous_streak = 0

    if previous is None:
        streak = 1
        gap_note = "first worker-authored proving heartbeat"
    else:
        gap_minutes = (now - previous).total_seconds() / 60.0
        gap_note = f"gap from prior worker heartbeat: {gap_minutes:.1f} minutes"
        if 10.0 <= gap_minutes <= 20.0:
            streak = previous_streak + 1
        elif gap_minutes > 20.0:
            streak = 1
        else:
            streak = previous_streak

    mode = "STEADY_HOURLY" if streak >= 3 else "PROVING_15M"
    interval = "60" if mode == "STEADY_HOURLY" else "15"

    text = replace_metadata(text, "mode", mode)
    text = replace_metadata(text, "interval_minutes", interval)
    text = replace_metadata(text, "consecutive_on_time", str(streak))
    text = replace_metadata(text, "last_check_in_utc", iso_z(now))

    entry = (
        f"### {iso_z(now)} — {lane} PROVING HEARTBEAT {index}/{count}\n\n"
        f"Cadence evidence: {gap_note}.\n\n"
        f"Verified local streak after this heartbeat: {streak}/3.\n\n"
        "Lead action requested:\n- NONE\n\n"
        "Review state:\n- WORKING"
    )
    text = append_entry(text, entry)
    path.write_text(text, encoding="utf-8")
    commit_push(path, f"heartbeat({lane}): {streak}/3 proving")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lane", required=True, choices=LANES.keys())
    parser.add_argument("--mode", required=True, choices=("smoke", "prove"))
    parser.add_argument("--count", type=int, default=3)
    parser.add_argument(
        "--interval-seconds",
        type=int,
        default=None,
        help="Smoke default: 60. Prove default: 900. Use 900 for real proving.",
    )
    args = parser.parse_args()

    branch, path = LANES[args.lane]
    ensure_branch(branch)
    if not path.exists():
        raise SystemExit(f"Heartbeat file missing: {path}. Pull/rebase latest main first.")

    if args.count < 1:
        raise SystemExit("--count must be >= 1")

    interval = args.interval_seconds
    if interval is None:
        interval = 60 if args.mode == "smoke" else 900

    if args.mode == "prove" and interval != 900:
        print(
            "WARNING: prove mode with interval other than 900 seconds is a mechanics test "
            "and will not satisfy the project's real 15-minute proving policy.",
            file=sys.stderr,
        )

    for i in range(1, args.count + 1):
        if args.mode == "smoke":
            do_smoke(args.lane, path, i, args.count)
        else:
            do_prove(args.lane, path, i, args.count)

        print(f"{args.lane}: pushed {args.mode} heartbeat {i}/{args.count}", flush=True)

        if i < args.count:
            time.sleep(interval)

    print(f"{args.lane}: probe complete", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
