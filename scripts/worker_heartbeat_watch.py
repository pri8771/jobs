#!/usr/bin/env python3
"""Detached continuous 5-minute heartbeat watcher for active Jobs lanes.

Exactly one rule: while an active lane session is running, publish a heartbeat
approximately every 5 minutes. There are no proving/watch/hourly transitions.

The watcher uses a separate lightweight clone under .local/heartbeat-watch so
heartbeat commits never dirty the implementation working tree.
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import subprocess
import sys
import time
from pathlib import Path

LANES = {
    "1": ("worker/v14-real-proof", Path("coordination/heartbeats/LANE_1.md")),
    "2": ("worker/v15-assisted-application", Path("coordination/heartbeats/LANE_2.md")),
    "3": ("worker/recruiting-ops", Path("coordination/heartbeats/LANE_3.md")),
}

DEFAULT_TASKS = {
    "1": "V1.4 real-proof tooling RP14-T1..T7",
    "2": "V1.5 assisted-application safety A-R15-06..09",
    "3": "V1.7/V2.0 worker-run and funnel repairs",
}

DEFAULT_EPOCH = "FIVE_MIN_2026_09_21"
INTERVAL_SECONDS = 300
MIN_GAP_SECONDS = 240


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
    replacement = f"{key}: {value}"
    if re.search(pattern, text):
        return re.sub(pattern, replacement, text, count=1)
    lines = text.splitlines()
    insert_at = 1 if lines and lines[0].startswith("#") else 0
    lines.insert(insert_at, replacement)
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def append_entry(text: str, entry: str) -> str:
    marker = "## Entries"
    if marker not in text:
        return text.rstrip() + f"\n\n{marker}\n\n{entry}\n"
    before, after = text.split(marker, 1)
    return before.rstrip() + f"\n\n{marker}\n\n{entry}\n\n" + after.lstrip("\n")


def metadata_int(text: str, key: str, default: int = 0) -> int:
    try:
        return int(read_metadata(text, key) or str(default))
    except ValueError:
        return default


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


def initialize(text: str, lane: str, branch: str, epoch: str, task: str) -> str:
    now = utc_now()
    if read_metadata(text, "heartbeat_epoch") != epoch:
        text = replace_metadata(text, "heartbeat_count", "0")
        text = replace_metadata(text, "last_check_in_utc", "null")
        text = append_entry(
            text,
            f"### {iso_z(now)} — Lane {lane} 5-MINUTE HEARTBEAT STANDARD\n\n"
            f"Epoch: {epoch}\n\n"
            "Continuous 5-minute heartbeat enabled. Prior cadence history is preserved "
            "but does not govern this epoch.\n\nReview state:\n- WORKING",
        )

    values = {
        "lane": lane,
        "branch": branch,
        "heartbeat_epoch": epoch,
        "mode": "ACTIVE_5M",
        "interval_minutes": "5",
        "current_task": task,
        "progress_note": read_metadata(text, "progress_note") or "still working on assigned task",
        "review_state": read_metadata(text, "review_state") or "WORKING",
        "lead_action_requested": read_metadata(text, "lead_action_requested") or "NONE",
    }
    for key, value in values.items():
        text = replace_metadata(text, key, value)
    return text


def heartbeat_transform(lane: str, branch: str, epoch: str, task: str):
    def apply(text: str) -> str:
        text = initialize(text, lane, branch, epoch, task)
        now = utc_now()
        previous = parse_utc(read_metadata(text, "last_check_in_utc"))
        if previous is not None and (now - previous).total_seconds() < MIN_GAP_SECONDS:
            return text

        count = metadata_int(text, "heartbeat_count", 0) + 1
        gap = None if previous is None else (now - previous).total_seconds() / 60.0

        text = replace_metadata(text, "mode", "ACTIVE_5M")
        text = replace_metadata(text, "interval_minutes", "5")
        text = replace_metadata(text, "heartbeat_count", str(count))
        text = replace_metadata(text, "last_check_in_utc", iso_z(now))

        gap_text = "first heartbeat" if gap is None else f"{gap:.1f} minutes since prior heartbeat"
        entry = (
            f"### {iso_z(now)} — Lane {lane} 5-MINUTE HEARTBEAT\n\n"
            f"Task: {task}\n\n"
            f"Update: {read_metadata(text, 'progress_note') or 'still working on assigned task'}\n\n"
            f"Cadence: {gap_text}\n\n"
            f"Heartbeat count: {count}\n\n"
            f"Lead action requested:\n- {read_metadata(text, 'lead_action_requested') or 'NONE'}\n\n"
            f"Review state:\n- {read_metadata(text, 'review_state') or 'WORKING'}"
        )
        return append_entry(text, entry)

    return apply


def write_heartbeat(clone_root: Path, branch: str, path: Path, transform, lane: str) -> bool:
    for attempt in range(1, 5):
        sync_clone(clone_root, branch)
        target = clone_root / path
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(f"# Lane {lane} Heartbeat\n\n## Entries\n", encoding="utf-8")

        original = target.read_text(encoding="utf-8")
        updated = transform(original)
        if updated == original:
            return False

        target.write_text(updated, encoding="utf-8")
        run("git", "add", str(path), cwd=clone_root)
        diff = subprocess.run(
            ["git", "diff", "--cached", "--quiet", "--", str(path)],
            cwd=str(clone_root),
            check=False,
        )
        if diff.returncode == 0:
            return False

        try:
            run("git", "commit", "-m", f"heartbeat({lane}): 5-minute update", cwd=clone_root)
            run("git", "push", "origin", f"HEAD:{branch}", cwd=clone_root)
            return True
        except subprocess.CalledProcessError:
            if attempt == 4:
                raise
            time.sleep(5)
    return False


def run_watch(lane: str, epoch: str, task: str | None = None) -> int:
    source_root = git_root()
    branch, hb_path = LANES[lane]
    clone_root = source_root / ".local" / "heartbeat-watch" / lane
    task_name = task or DEFAULT_TASKS[lane]
    ensure_clone(source_root, clone_root, branch)

    transform = heartbeat_transform(lane, branch, epoch, task_name)

    while True:
        wrote = write_heartbeat(clone_root, branch, hb_path, transform, lane)
        if wrote:
            time.sleep(INTERVAL_SECONDS)
        else:
            # Another watcher may have just written. Re-check soon without creating duplicates.
            time.sleep(30)


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
    print(f"HEARTBEAT_WATCH_STARTED lane={lane} pid={proc.pid} cadence=5m log={log_path}")
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
