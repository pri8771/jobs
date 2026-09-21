#!/usr/bin/env python3
"""Detached heartbeat watcher for the Jobs Automation single active worker session.

Default Epoch: FIVE_MIN_2026_09_21
Mode: ACTIVE_5M (fixed 5-minute cadence while active).

A separate lightweight clone is used so heartbeat commits never dirty the
implementation worker's working tree.
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path

LANES = {
    "1": ("worker/v14-real-proof", Path("coordination/heartbeats/LANE_1.md")),
    "2": ("worker/v15-assisted-application", Path("coordination/heartbeats/LANE_2.md")),
    "3": ("worker/recruiting-ops", Path("coordination/heartbeats/LANE_3.md")),
}

DEFAULT_TASKS = {
    "1": "V1.4 real-proof tooling RP14-T1..T7",
    "2": "V1.5 assisted-application safety A-R15-06..09",
    "3": "V1.7/V2.0 post-integration verification",
}

DEFAULT_EPOCH = "FIVE_MIN_2026_09_21"
INTERVAL_SECONDS = 300
MIN_INTERVAL_SECONDS = 240
MAX_INTERVAL_SECONDS = 420


def run(*args: str, cwd: Path | None = None, capture: bool = False) -> str:
    proc = subprocess.run(
        list(args),
        cwd=str(cwd) if cwd else None,
        check=True,
        text=True,
        capture_output=capture,
    )
    return proc.stdout.strip() if capture else ""


def git_root() -> Path:
    return Path(run("git", "rev-parse", "--show-toplevel", capture=True)).resolve()


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.UTC).replace(microsecond=0)


def iso_z(value: dt.datetime | None) -> str:
    if value is None:
        return "null"
    return value.astimezone(dt.UTC).isoformat().replace("+00:00", "Z")


def parse_utc(value: str | None) -> dt.datetime | None:
    if not value or value.strip().lower() == "null":
        return None
    try:
        return dt.datetime.fromisoformat(value.strip().replace("Z", "+00:00")).astimezone(dt.UTC)
    except ValueError:
        return None


def read_metadata(text: str, key: str) -> str | None:
    match = re.search(rf"(?m)^{re.escape(key)}:\s*(.*?)\s*$", text)
    return match.group(1) if match else None


def replace_metadata(text: str, key: str, value: str) -> str:
    pattern = rf"(?m)^{re.escape(key)}:\s*.*$"
    if re.search(pattern, text):
        return re.sub(pattern, f"{key}: {value}", text, count=1)
    lines = text.splitlines()
    insert_at = 1 if lines and lines[0].startswith("#") else 0
    lines.insert(insert_at, f"{key}: {value}")
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def metadata_int(text: str, key: str, default: int = 0) -> int:
    try:
        return int(read_metadata(text, key) or str(default))
    except ValueError:
        return default


def append_entry(text: str, entry: str) -> str:
    marker = "## Entries"
    if marker not in text:
        return text.rstrip() + f"\n\n{marker}\n\n{entry}\n"
    before, after = text.split(marker, 1)
    return before.rstrip() + f"\n\n{marker}\n\n{entry}\n\n" + after.lstrip("\n")


def ensure_clone(source_root: Path, clone_root: Path, branch: str) -> None:
    remote = run("git", "remote", "get-url", "origin", cwd=source_root, capture=True)
    if not (clone_root / ".git").exists():
        clone_root.parent.mkdir(parents=True, exist_ok=True)
        run("git", "clone", "--single-branch", "--branch", branch, remote, str(clone_root))
    else:
        run("git", "remote", "set-url", "origin", remote, cwd=clone_root)


def sync_clone(clone_root: Path, branch: str) -> None:
    run("git", "fetch", "origin", branch, cwd=clone_root)
    run("git", "checkout", "-B", branch, f"origin/{branch}", cwd=clone_root)
    run("git", "reset", "--hard", f"origin/{branch}", cwd=clone_root)


def reset_epoch(text: str, lane: str, branch: str, epoch: str, task: str) -> str:
    now = utc_now()
    values = {
        "lane": lane,
        "branch": branch,
        "heartbeat_epoch": epoch,
        "mode": "ACTIVE_5M",
        "interval_minutes": "5",
        "heartbeat_count": "0",
        "last_check_in_utc": "null",
        "current_task": task,
        "progress_note": "active 5-minute heartbeat watcher started",
        "review_state": "WORKING",
        "lead_action_requested": "NONE",
    }
    for key, value in values.items():
        text = replace_metadata(text, key, value)
    return append_entry(
        text,
        f"### {iso_z(now)} — Lane {lane} 5-MINUTE HEARTBEAT RESET\n\n"
        f"Epoch: {epoch}\n\n"
        "Mode: ACTIVE_5M (fixed 5-minute interval while active).\n\n"
        "Review state:\n- WORKING",
    )


def heartbeat_transform(
    lane: str,
    branch: str,
    epoch: str,
    task: str,
) -> Callable[[str], tuple[str, bool, int]]:
    def apply(text: str) -> tuple[str, bool, int]:
        now = utc_now()
        if read_metadata(text, "heartbeat_epoch") != epoch:
            text = reset_epoch(text, lane, branch, epoch, task)

        previous = parse_utc(read_metadata(text, "last_check_in_utc"))
        gap_seconds = None if previous is None else (now - previous).total_seconds()

        if gap_seconds is not None and gap_seconds < MIN_INTERVAL_SECONDS:
            return text, False, 30

        count = metadata_int(text, "heartbeat_count", 0) + 1
        current_task = read_metadata(text, "current_task") or task
        progress_note = read_metadata(text, "progress_note") or "still working on assigned task"
        review_state = read_metadata(text, "review_state") or "WORKING"
        lead_action = read_metadata(text, "lead_action_requested") or "NONE"

        text = replace_metadata(text, "heartbeat_epoch", epoch)
        text = replace_metadata(text, "mode", "ACTIVE_5M")
        text = replace_metadata(text, "interval_minutes", "5")
        text = replace_metadata(text, "heartbeat_count", str(count))
        text = replace_metadata(text, "last_check_in_utc", iso_z(now))
        text = replace_metadata(text, "current_task", current_task)
        text = replace_metadata(text, "progress_note", progress_note)
        text = replace_metadata(text, "review_state", review_state)
        text = replace_metadata(text, "lead_action_requested", lead_action)

        gap_text = "first check-in" if gap_seconds is None else f"{gap_seconds / 60:.1f} minutes"
        text = append_entry(
            text,
            f"### {iso_z(now)} — Lane {lane} ACTIVE 5-MINUTE HEARTBEAT #{count}\n\n"
            f"Cadence gap: {gap_text}\n\n"
            f"Mode: ACTIVE_5M\n\n"
            f"Task: {current_task}\n\n"
            f"Update: {progress_note}\n\n"
            f"Review state: {review_state}\n\n"
            f"Lead action requested: {lead_action}",
        )
        return text, True, INTERVAL_SECONDS

    return apply


def write_heartbeat(
    clone_root: Path,
    branch: str,
    path: Path,
    transform: Callable[[str], tuple[str, bool, int]],
    lane: str,
) -> tuple[bool, int]:
    for attempt in range(1, 5):
        sync_clone(clone_root, branch)
        target = clone_root / path
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(f"# Lane {lane} Heartbeat\n\n## Entries\n", encoding="utf-8")

        original = target.read_text(encoding="utf-8")
        updated, should_write, next_sleep = transform(original)
        if not should_write or updated == original:
            return False, next_sleep

        target.write_text(updated, encoding="utf-8")
        run("git", "add", str(path), cwd=clone_root)
        diff = subprocess.run(
            ["git", "diff", "--cached", "--quiet", "--", str(path)],
            cwd=str(clone_root),
            check=False,
        )
        if diff.returncode == 0:
            return False, next_sleep

        try:
            count_str = read_metadata(updated, "heartbeat_count") or "1"
            run("git", "commit", "-m", f"heartbeat({lane}): active 5m #{count_str}", cwd=clone_root)
            run("git", "push", "origin", f"HEAD:{branch}", cwd=clone_root)
            return True, next_sleep
        except subprocess.CalledProcessError:
            if attempt == 4:
                raise
            time.sleep(5)
    return False, 30


def run_watch(lane: str, epoch: str, task: str | None = None) -> int:
    source_root = git_root()
    branch, hb_path = LANES[lane]
    clone_root = source_root / ".local" / "heartbeat-watch" / lane
    task_name = task or DEFAULT_TASKS[lane]
    ensure_clone(source_root, clone_root, branch)
    transform = heartbeat_transform(lane, branch, epoch, task_name)

    while True:
        _wrote, next_sleep = write_heartbeat(clone_root, branch, hb_path, transform, lane)
        time.sleep(next_sleep)


def detach(lane: str, epoch: str, task: str | None = None) -> int:
    root = git_root()
    log_dir = root / ".local" / "heartbeat-watch-logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{lane}-{epoch}.log"
    cmd = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--lane",
        lane,
        "--epoch",
        epoch,
        "--task",
        task or DEFAULT_TASKS[lane],
        "--child",
    ]
    log_handle = open(log_path, "a", encoding="utf-8")
    kwargs: dict[str, object] = {
        "cwd": str(root),
        "stdout": log_handle,
        "stderr": subprocess.STDOUT,
        "stdin": subprocess.DEVNULL,
        "close_fds": True,
    }
    if os.name == "nt":
        kwargs["creationflags"] = (
            subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS  # type: ignore[attr-defined]
        )
    else:
        kwargs["start_new_session"] = True
    proc = subprocess.Popen(cmd, **kwargs)
    log_handle.close()
    print(f"HEARTBEAT_WATCH_STARTED lane={lane} pid={proc.pid} epoch={epoch} log={log_path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lane", required=True, choices=LANES.keys())
    parser.add_argument("--epoch", default=DEFAULT_EPOCH)
    parser.add_argument("--detach", action="store_true")
    parser.add_argument("--task", default=None)
    parser.add_argument("--child", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()

    if args.detach and not args.child:
        return detach(args.lane, args.epoch, args.task)
    return run_watch(args.lane, args.epoch, args.task)


if __name__ == "__main__":
    raise SystemExit(main())
