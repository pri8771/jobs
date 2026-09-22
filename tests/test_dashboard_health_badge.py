"""Runtime regressions for the dashboard's health-bound status badge."""

from __future__ import annotations

import json
import re
import shutil
import subprocess

import pytest

from jobs_automation.dashboard.server import DASHBOARD_HTML

NODE = "node"

NODE_RUNNER = r"""
const fs = require('fs');
const vm = require('vm');
const input = JSON.parse(fs.readFileSync(0, 'utf8'));

class Element {
  constructor(id, text = '', className = '') {
    this.id = id;
    this._text = text;
    this.className = className;
    this.innerHTML = '';
    this.style = {};
    this.attributes = {};
    this.classList = {
      add: (...names) => {
        const values = new Set(this.className.split(/\s+/).filter(Boolean));
        names.forEach(name => values.add(name));
        this.className = [...values].join(' ');
      },
      remove: (...names) => {
        const removed = new Set(names);
        this.className = this.className.split(/\s+/).filter(name => name && !removed.has(name)).join(' ');
      },
    };
  }
  get innerText() { return this._text; }
  set innerText(value) { this._text = String(value); }
  get textContent() { return this._text; }
  set textContent(value) { this._text = String(value); }
  setAttribute(name, value) { this.attributes[name] = String(value); }
  getAttribute(name) { return this.attributes[name] ?? null; }
}

const elements = new Map();
const initial = input.initial;
const badge = new Element('system-health-badge', initial.text, initial.className);
for (const [name, value] of Object.entries(initial.attributes)) badge.setAttribute(name, value);
elements.set(badge.id, badge);
const element = id => {
  if (!elements.has(id)) elements.set(id, new Element(id));
  return elements.get(id);
};
const calls = [];
const goodFunnel = {
  total_jobs_discovered: 0, total_submitted: 0, total_screening: 0,
  total_interviewing: 0, total_offers: 0, pending_reviews: 0,
  conversion_rates: {
    discovery_to_submission_pct: 0, submission_to_screen_pct: 0,
    screen_to_interview_pct: 0, interview_to_offer_pct: 0,
  },
};
async function fetchStub(url) {
  calls.push(url);
  if (url === '/api/funnel') return {ok: true, status: 200, json: async () => goodFunnel};
  if (url === '/api/sources') return {ok: true, status: 200, json: async () => ({})};
  if (url !== '/api/health') throw new Error(`unexpected fetch ${url}`);
  if (input.scenario.kind === 'fetch_reject') throw new Error('synthetic fetch failure');
  if (input.scenario.kind === 'non_2xx') {
    return {ok: false, status: 503, json: async () => ({overall_status: 'HEALTHY'})};
  }
  if (input.scenario.kind === 'json_reject') {
    return {ok: true, status: 200, json: async () => { throw new SyntaxError('synthetic json'); }};
  }
  return {ok: true, status: 200, json: async () => input.scenario.payload};
}
const context = {
  fetch: fetchStub,
  document: {getElementById: element, querySelectorAll: () => []},
  console: {error: () => {}, log: () => {}},
  Date, Object, JSON, Promise, Set,
  setTimeout, clearTimeout,
};
vm.createContext(context);
vm.runInContext(input.script, context);
(async () => {
  for (let i = 0; i < 8; i += 1) await new Promise(resolve => setImmediate(resolve));
  const current = element('system-health-badge');
  process.stdout.write(JSON.stringify({
    text: current.textContent,
    className: current.className,
    attributes: current.attributes,
    calls,
  }));
})().catch(error => { console.error(error); process.exit(1); });
"""


def _script() -> str:
    match = re.search(r"<script>(.*?)</script>", DASHBOARD_HTML, re.DOTALL)
    assert match is not None
    return match.group(1)


def _initial_badge() -> dict[str, object]:
    match = re.search(
        r"<span(?P<attrs>[^>]*\bid=[\"']system-health-badge[\"'][^>]*)>(?P<text>.*?)</span>",
        DASHBOARD_HTML,
        re.DOTALL,
    )
    assert match is not None, "dashboard must expose a stable system-health-badge id"
    attrs = match.group("attrs")

    def attr(name: str) -> str | None:
        found = re.search(rf"\b{name}=[\"']([^\"']*)[\"']", attrs)
        return found.group(1) if found else None

    return {
        "text": re.sub(r"<[^>]+>", "", match.group("text")).strip(),
        "className": attr("class") or "",
        "attributes": {"role": attr("role"), "aria-live": attr("aria-live")},
    }


def _run(scenario: dict[str, object]) -> dict[str, object]:
    if shutil.which(NODE) is None:
        pytest.fail(f"required existing Node runtime is missing: {NODE}")
    proc = subprocess.run(
        [NODE, "-e", NODE_RUNNER],
        input=json.dumps({"script": _script(), "scenario": scenario, "initial": _initial_badge()}),
        text=True,
        capture_output=True,
        check=False,
        timeout=10,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def test_health_badge_initial_state_is_accessible_neutral_and_not_live() -> None:
    initial = _initial_badge()

    assert "System Live" not in DASHBOARD_HTML
    assert initial == {
        "text": "Unknown",
        "className": "status-badge health-unknown",
        "attributes": {"role": "status", "aria-live": "polite"},
    }


@pytest.mark.parametrize(
    ("scenario", "expected_text", "expected_class"),
    [
        ({"kind": "response", "payload": {"overall_status": "HEALTHY"}}, "Healthy", "health-healthy"),
        ({"kind": "response", "payload": {"overall_status": "DEGRADED"}}, "Degraded", "health-degraded"),
        ({"kind": "response", "payload": {"overall_status": "UNHEALTHY"}}, "Unhealthy", "health-unhealthy"),
        ({"kind": "fetch_reject"}, "Unknown", "health-unknown"),
        ({"kind": "non_2xx"}, "Unknown", "health-unknown"),
        ({"kind": "json_reject"}, "Unknown", "health-unknown"),
        ({"kind": "response", "payload": None}, "Unknown", "health-unknown"),
        ({"kind": "response", "payload": []}, "Unknown", "health-unknown"),
        ({"kind": "response", "payload": {}}, "Unknown", "health-unknown"),
        ({"kind": "response", "payload": {"overall_status": "SURPRISING"}}, "Unknown", "health-unknown"),
        ({"kind": "response", "payload": {"overall_status": 7}}, "Unknown", "health-unknown"),
    ],
)
def test_health_badge_executes_embedded_script_once_and_fails_closed(
    scenario: dict[str, object], expected_text: str, expected_class: str
) -> None:
    result = _run(scenario)

    assert result["calls"].count("/api/health") == 1
    assert result["text"] == expected_text
    assert expected_class in result["className"].split()
    assert result["attributes"] == {"role": "status", "aria-live": "polite"}
