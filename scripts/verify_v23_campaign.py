#!/usr/bin/env python3
"""V23 Acceptance Campaign Report Verifier (V23-AC-02).

Validates engineering and live acceptance campaign reports against specification rules.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys


def get_git_sha() -> str:
    try:
        out = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True)
        return out.strip()
    except Exception:
        return ""


def verify_campaign(report_path: str, mode: str = "engineering", db_url: str | None = None) -> tuple[bool, str, dict]:
    if not os.path.exists(report_path):
        return False, f"Report file not found: {report_path}", {}

    try:
        with open(report_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return False, f"Failed to parse report JSON: {e}", {}

    # Validate required top-level keys
    required_keys = ["trace_id", "code_sha", "fixture_version", "simulated", "assertions", "status"]
    for k in required_keys:
        if k not in data:
            return False, f"Missing required key in report: {k}", data

    # Check assertions
    assertions = data.get("assertions", [])
    if not assertions:
        return False, "Report contains empty assertions list", data

    for a in assertions:
        if a.get("status") != "pass":
            return False, f"Assertion failed: {a.get('step')}", data

    if mode == "engineering":
        if not data.get("simulated"):
            return False, "Engineering mode requires simulated=True", data
        return True, "Engineering campaign verification PASSED", data

    elif mode == "live":
        if data.get("simulated"):
            return False, "Live mode requires simulated=False", data

        git_sha = get_git_sha()
        if git_sha and data.get("code_sha") != git_sha:
            return False, f"code_sha mismatch: report={data.get('code_sha')}, git={git_sha}", data

        if not db_url:
            return False, "Live mode requires --database-url (fail closed)", data

        return True, "Live campaign verification PASSED", data

    else:
        return False, f"Unknown mode: {mode}", data


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify V2.3 Acceptance Campaign Report")
    parser.add_argument("--report", required=True, help="Path to campaign report JSON")
    parser.add_argument("--mode", choices=["engineering", "live"], default="engineering", help="Verification mode")
    parser.add_argument("--database-url", default=None, help="Database URL for live verification")

    args = parser.parse_args()
    passed, message, data = verify_campaign(args.report, mode=args.mode, db_url=args.database_url)

    receipt = {
        "report_path": args.report,
        "mode": args.mode,
        "result": "V23_CAMPAIGN_PASS" if passed else "V23_CAMPAIGN_FAIL",
        "message": message,
        "verified_at": subprocess.check_output(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"], text=True).strip(),
    }

    print(json.dumps(receipt, indent=2))

    # Write v23_campaign_receipt.json
    with open("v23_campaign_receipt.json", "w", encoding="utf-8") as f:
        json.dump(receipt, f, indent=2)

    if not passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
