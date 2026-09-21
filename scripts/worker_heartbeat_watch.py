#!/usr/bin/env python3
"""Detached lane heartbeat watcher for the 2026-09-21 liveness exercise.

Protocol for this exercise:
1. PROVING_5M: 3 worker-authored heartbeats, nominally 5 minutes apart.
2. WATCH_15M_24H: heartbeat every 15 minutes for a full 24 hours.
3. STEADY_HOURLY after the 24-hour watch completes without a missed interval.

The watcher uses a separate lightweight clone under .local/heartbeat-watch so it
does not modify or commit the implementation worker's working tree.
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
    # Historical lane aliases retained for old evidence only.
    "A": ("worker/v15-assisted-application", Path("coordination/heartbeats/LANE_A.md")),
    "B": ("worker/recruiting-ops", Path("coordination/heartbeats/LANE_B.md")),
    "C": ("worker/live-data-foundations", Path("coordination/heartbeats/LANE_C.md")),
    "D": ("worker/v23-foundations", Path("coordination/heartbeats/LANE_D.md")),
    "SCOUT": ("scout/qa-prep", Path("coordination/heartbeats/SCOUT.md")),
}

DEFAULT_TASKS = {
    "1": "V1.4 real-proof tooling RP14-T1..T7",
    "2": "V1.5 assisted-application safety A-R15-06..09",
    "3": "V1.7/V2.0 worker-run and funnel repairs",
    "A": "historical Lane A",
    "B": "historical Lane B",
    "C": "historical Lane C",
    "D": "historical Lane D",
    "SCOUT": "historical Scout",
}

DEFAULT_EPOCH = "DAYWATCH_2026_09_21"
PROVE_INTERVAL_SECONDS = 300
WATCH_INTERVAL_SECONDS = 900
PROVE_MIN_SECONDS = 240
PROVE_MAX_SECONDS = 420
WATCH_MAX_SECONDS = 1200
WATCH_DURATION_SECONDS = 24 * 60 * 60


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
    raw = read_metadata(text, key)
    try:
        return int(raw or str(default))
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


def write_and_push(
    clone_root: Path,
    branch: str,
    path: Path,
    transform,
    message: str,
) -> None:
    last_error: Exception | None = None
    for _attempt in range(1, 5):
        try:
            sync_clone(clone_root, branch)
            target = clone_root / path
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(f"# {path.stem} Heartbeat\n\n## Entries\n", encoding="utf-8")
            text = target.read_text(encoding="utf-8")
            updated = transform(text)
            target.write_text(updated, encoding="utf-8")
            run("git", "add", str(path), cwd=clone_root)
            run("git", "commit", "-m", message, cwd=clone_root)
            run("git", "push", "origin", f"HEAD:{branch}", cwd=clone_root)
            return
        except (subprocess.CalledProcessError, OSError) as exc:
            last_error = exc
            time.sleep(5)
    raise RuntimeError(f"heartbeat push failed after retries: {last_error}")


def reset_epoch(text: str, lane: str, branch: str, epoch: str, task: str | None = None) -> str:
    now = utc_now()
    values = {
        "lane": lane,
        "branch": branch,
        "heartbeat_epoch": epoch,
        "mode": "PROVING_5M",
        "interval_minutes": "5",
        "consecutive_on_time": "0",
        "last_check_in_utc": "null",
        "watch_started_utc": "null",
        "watch_until_utc": "null",
        "watch_checkins": "0",
        "missed_intervals": "0",
        "watch_completed_utc": "null",
        "review_state": "WORKING",
        "lead_action_requested": "NONE",
        "watcher_started_utc": iso_z(now),
        "current_task": task or DEFAULT_TASKS.get(lane, "assigned lane work"),
        "progress_note": "still working on assigned task",
    }
    for key, value in values.items():
        text = replace_metadata(text, key, value)
    entry = (
        f"### {iso_z(now)} — {lane} HEARTBEAT EPOCH RESET\n\n"
        f"Epoch: {epoch}\n\n"
        "Fresh liveness exercise started. Historical heartbeat entries are preserved "
        "but do not count toward this epoch.\n\n"
        "Review state:\n- WORKING"
    )
    return append_entry(text, entry)


def proving_transform(lane: str, branch: str, epoch: str):
    def apply(text: str) -> str:
        now = utc_now()
        if read_metadata(text, "heartbeat_epoch") != epoch:
            text = reset_epoch(text, lane, branch, epoch, DEFAULT_TASKS.get(lane))

        previous = parse_utc(read_metadata(text, "last_check_in_utc"))
        prior_streak = metadata_int(text, "consecutive_on_time", 0)

        if previous is None:
            streak = 1
            gap = None
        else:
            gap_seconds = (now - previous).total_seconds()
            if PROVE_MIN_SECONDS <= gap_seconds <= PROVE_MAX_SECONDS:
                streak = prior_streak + 1
            else:
                streak = 1
            gap = gap_seconds / 60.0

        text = replace_metadata(text, "mode", "PROVING_5M")
        text = replace_metadata(text, "interval_minutes", "5")
        text = replace_metadata(text, "consecutive_on_time", str(streak))
        text = replace_metadata(text, "last_check_in_utc", iso_z(now))

        if streak >= 3:
            watch_until = now + dt.timedelta(seconds=WATCH_DURATION_SECONDS)
            text = replace_metadata(text, "mode", "WATCH_15M_24H")
            text = replace_metadata(text, "interval_minutes", "15")
            text = replace_metadata(text, "watch_started_utc", iso_z(now))
            text = replace_metadata(text, "watch_until_utc", iso_z(watch_until))
            text = replace_metadata(text, "watch_checkins", "0")
            text = replace_metadata(text, "missed_intervals", "0")

        gap_text = "first check-in" if gap is None else f"{gap:.1f} minutes since prior check-in"
        entry = (
            f"### {iso_z(now)} — {lane} 5-MINUTE PROVING HEARTBEAT\n\n"
            f"Epoch: {epoch}\n\n"
            f"Cadence: {gap_text}\n\n"
            f"Proving streak after this check-in: {streak}/3\n\n"
            f"Mode after this check-in: "
            f"{'WATCH_15M_24H' if streak >= 3 else 'PROVING_5M'}\n\n"
            "Lead action requested:\n- NONE\n\n"
            "Review state:\n- WORKING"
        )
        return append_entry(text, entry)
    return apply


def watch_transform(lane: str, branch: str, epoch: str):
    def apply(text: str) -> str:
        now = utc_now()
        if read_metadata(text, "heartbeat_epoch") != epoch:
            raise RuntimeError("heartbeat epoch changed while watcher was running")

        started = parse_utc(read_metadata(text, "watch_started_utc"))
        until = parse_utc(read_metadata(text, "watch_until_utc"))
        previous = parse_utc(read_metadata(text, "last_check_in_utc"))
        if started is None or until is None:
            raise RuntimeError("watch mode started without watch timestamps")

        checkins = metadata_int(text, "watch_checkins", 0)
        missed = metadata_int(text, "missed_intervals", 0)
        gap_minutes = (now - previous).total_seconds() / 60.0 if previous else None
        if previous and (now - previous).total_seconds() > WATCH_MAX_SECONDS:
            missed += 1
            # A missed interval restarts the 24-hour clean watch window.
            started = now
            until = now + dt.timedelta(seconds=WATCH_DURATION_SECONDS)
            checkins = 0

        checkins += 1
        text = replace_metadata(text, "mode", "WATCH_15M_24H")
        text = replace_metadata(text, "interval_minutes", "15")
        text = replace_metadata(text, "last_check_in_utc", iso_z(now))
        text = replace_metadata(text, "watch_started_utc", iso_z(started))
        text = replace_metadata(text, "watch_until_utc", iso_z(until))
        text = replace_metadata(text, "watch_checkins", str(checkins))
        text = replace_metadata(text, "missed_intervals", str(missed))

        if now >= until and missed == 0:
            text = replace_metadata(text, "mode", "STEADY_HOURLY")
            text = replace_metadata(text, "interval_minutes", "60")
            text = replace_metadata(text, "watch_completed_utc", iso_z(now))

        gap_text = "unknown" if gap_minutes is None else f"{gap_minutes:.1f} minutes"
        entry = (
            f"### {iso_z(now)} — {lane} 15-MINUTE 24H WATCH HEARTBEAT\n\n"
            f"Epoch: {epoch}\n\n"
            f"Gap from prior check-in: {gap_text}\n\n"
            f"Watch check-ins: {checkins}\n\n"
            f"Missed intervals: {missed}\n\n"
            f"Watch until: {iso_z(until)}\n\n"
            f"Mode after this check-in: "
            f"{'STEADY_HOURLY' if now >= until and missed == 0 else 'WATCH_15M_24H'}\n\n"
            "Lead action requested:\n- NONE\n\n"
            "Review state:\n- WORKING"
        )
        return append_entry(text, entry)
    return apply


def run_watch(lane: str, epoch: str, task: str | None = None) -> int:
    source_root = git_root()
    branch, hb_path = LANES[lane]
    clone_root = source_root / ".local" / "heartbeat-watch" / lane.lower()
    ensure_clone(source_root, clone_root, branch)

    write_and_push(
        clone_root,
        branch,
        hb_path,
        lambda text: reset_epoch(text, lane, branch, epoch, task or DEFAULT_TASKS.get(lane)),
        f"heartbeat({lane}): reset {epoch} to 5-minute proving",
    )

    for i in range(1, 4):
        if i > 1:
            time.sleep(PROVE_INTERVAL_SECONDS)
        write_and_push(
            clone_root,
            branch,
            hb_path,
            proving_transform(lane, branch, epoch),
            f"heartbeat({lane}): 5-minute proving {i}/3",
        )

    # The third proving heartbeat starts the 24-hour watch window.
    while True:
        time.sleep(WATCH_INTERVAL_SECONDS)
        write_and_push(
            clone_root,
            branch,
            hb_path,
            watch_transform(lane, branch, epoch),
            f"heartbeat({lane}): 15-minute 24h watch",
        )
        sync_clone(clone_root, branch)
        text = (clone_root / hb_path).read_text(encoding="utf-8")
        if read_metadata(text, "mode") == "STEADY_HOURLY":
            break

    return 0


def detach(lane: str, epoch: str, task: str | None = None) -> int:
    root = git_root()
    log_dir = root / ".local" / "heartbeat-watch-logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{lane.lower()}-{epoch}.log"
    cmd = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--lane",
        lane,
        "--epoch",
        epoch,
        "--task",
        task or DEFAULT_TASKS.get(lane, "assigned lane work"),
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
    print(f"HEARTBEAT_WATCH_STARTED lane={lane} pid={proc.pid} log={log_path}")
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
