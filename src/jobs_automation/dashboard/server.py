"""HTTP server and REST API for the Jobs Automation Dashboard."""

from __future__ import annotations

import json
import logging
import os
import uuid
from collections.abc import Callable
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

from sqlalchemy import select
from sqlalchemy.orm import Session

from jobs_automation.dashboard.analytics import FunnelAnalyticsService
from jobs_automation.db.models import (
    ApplicationModel,
    AuditLogModel,
    ContactModel,
    InterviewModel,
    JobModel,
    PolicyRegistryModel,
    TaskModel,
)
from jobs_automation.health import HealthCheckService
from jobs_automation.lifecycle.crm import RecruiterCRMService

logger = logging.getLogger(__name__)

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Jobs Automation OS - Dashboard</title>
  <style>
    :root {
      --bg: #0f172a;
      --card-bg: #1e293b;
      --border: #334155;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --primary: #3b82f6;
      --primary-hover: #2563eb;
      --success: #10b981;
      --warning: #f59e0b;
      --danger: #ef4444;
      --accent: #8b5cf6;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    body { background-color: var(--bg); color: var(--text); padding: 24px; }
    header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; padding-bottom: 16px; border-bottom: 1px solid var(--border); }
    h1 { font-size: 1.5rem; font-weight: 700; display: flex; align-items: center; gap: 8px; }
    .status-badge { background: #064e3b; color: #34d399; font-size: 0.75rem; padding: 4px 8px; border-radius: 9999px; font-weight: 600; }
    nav { display: flex; gap: 8px; margin-bottom: 24px; flex-wrap: wrap; }
    nav button { background: var(--card-bg); border: 1px solid var(--border); color: var(--text-muted); padding: 8px 16px; border-radius: 6px; cursor: pointer; font-weight: 600; transition: all 0.2s; }
    nav button.active, nav button:hover { background: var(--primary); color: #fff; border-color: var(--primary); }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 24px; }
    .stat-card { background: var(--card-bg); border: 1px solid var(--border); border-radius: 8px; padding: 16px; }
    .stat-title { font-size: 0.85rem; color: var(--text-muted); text-transform: uppercase; margin-bottom: 8px; }
    .stat-value { font-size: 2rem; font-weight: 700; color: var(--text); }
    .stat-sub { font-size: 0.8rem; color: var(--text-muted); margin-top: 4px; }
    .kanban-board { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 16px; overflow-x: auto; }
    .kanban-col { background: var(--card-bg); border: 1px solid var(--border); border-radius: 8px; padding: 16px; min-height: 500px; }
    .col-title { font-size: 0.9rem; font-weight: 700; margin-bottom: 12px; display: flex; justify-content: space-between; border-bottom: 1px solid var(--border); padding-bottom: 8px; }
    .kanban-card { background: #0f172a; border: 1px solid var(--border); border-radius: 6px; padding: 12px; margin-bottom: 12px; }
    .card-company { font-size: 0.8rem; color: var(--text-muted); font-weight: 600; }
    .card-title { font-size: 0.95rem; font-weight: 700; margin: 4px 0 8px 0; color: var(--text); }
    .card-meta { display: flex; justify-content: space-between; align-items: center; font-size: 0.75rem; color: var(--text-muted); }
    .badge { font-size: 0.7rem; padding: 2px 6px; border-radius: 4px; font-weight: 600; text-transform: uppercase; }
    .badge-auto { background: #064e3b; color: #34d399; }
    .badge-assisted { background: #1e3a8a; color: #93c5fd; }
    .badge-manual { background: #78350f; color: #fcd34d; }
    .table-container { background: var(--card-bg); border: 1px solid var(--border); border-radius: 8px; overflow: hidden; margin-bottom: 24px; }
    table { width: 100%; border-collapse: collapse; text-align: left; font-size: 0.9rem; }
    th { background: #0f172a; padding: 12px 16px; font-weight: 600; color: var(--text-muted); border-bottom: 1px solid var(--border); }
    td { padding: 12px 16px; border-bottom: 1px solid var(--border); }
    tr:last-child td { border-bottom: none; }
    button.btn-sm { padding: 4px 10px; font-size: 0.8rem; border-radius: 4px; border: none; cursor: pointer; background: var(--primary); color: #fff; }
    button.btn-sm:hover { background: var(--primary-hover); }
    .tab-content { display: none; }
    .tab-content.active { display: block; }
    input.search-input { width: 100%; padding: 10px 14px; background: #0f172a; border: 1px solid var(--border); border-radius: 6px; color: var(--text); margin-bottom: 16px; }
  </style>
</head>
<body>
  <header>
    <h1>💼 Jobs Automation OS <span class="status-badge">System Live</span></h1>
    <div id="refresh-time" style="font-size: 0.85rem; color: var(--text-muted);">Loaded</div>
  </header>

  <nav>
    <button class="active" onclick="switchTab('analytics')">Funnel Analytics</button>
    <button onclick="switchTab('kanban')">Kanban Pipeline</button>
    <button onclick="switchTab('jobs')">Discovered Jobs</button>
    <button onclick="switchTab('reviews')">Review Queue <span id="review-pill" style="display:none; background:var(--danger); color:white; border-radius:10px; padding:1px 6px; font-size:0.75rem;"></span></button>
    <button onclick="switchTab('interviews')">Interviews</button>
    <button onclick="switchTab('crm')">Recruiter CRM</button>
    <button onclick="switchTab('audit')">Audit Trail</button>
  </nav>

  <main>
    <!-- TAB 1: Analytics -->
    <div id="tab-analytics" class="tab-content active">
      <div class="grid" id="stats-grid">
        <div class="stat-card">
          <div class="stat-title">Jobs Discovered</div>
          <div class="stat-value" id="stat-discovered">-</div>
          <div class="stat-sub">Across all sources</div>
        </div>
        <div class="stat-card">
          <div class="stat-title">Applications Submitted</div>
          <div class="stat-value" id="stat-submitted">-</div>
          <div class="stat-sub" id="stat-sub-rate">- conv rate</div>
        </div>
        <div class="stat-card">
          <div class="stat-title">Recruiter Screens</div>
          <div class="stat-value" id="stat-screening">-</div>
          <div class="stat-sub" id="stat-screen-rate">- conv rate</div>
        </div>
        <div class="stat-card">
          <div class="stat-title">Technical Interviews</div>
          <div class="stat-value" id="stat-interviewing">-</div>
          <div class="stat-sub" id="stat-interview-rate">- conv rate</div>
        </div>
        <div class="stat-card">
          <div class="stat-title">Job Offers</div>
          <div class="stat-value" style="color:var(--success);" id="stat-offers">-</div>
          <div class="stat-sub" id="stat-offer-rate">- conv rate</div>
        </div>
      </div>
      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>Discovery Source</th>
              <th>Jobs Ingested</th>
            </tr>
          </thead>
          <tbody id="sources-body">
            <tr><td colspan="2">Loading sources...</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- TAB 2: Kanban -->
    <div id="tab-kanban" class="tab-content">
      <div class="kanban-board" id="kanban-board">
        <!-- Dynamically rendered -->
      </div>
    </div>

    <!-- TAB 3: Jobs Inbox -->
    <div id="tab-jobs" class="tab-content">
      <input type="text" id="jobs-search" class="search-input" placeholder="Search discovered jobs by title, company, or remote type..." onkeyup="filterJobs()">
      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>Company</th>
              <th>Role Title</th>
              <th>Remote Type</th>
              <th>Status</th>
              <th>First Seen</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody id="jobs-body">
            <tr><td colspan="6">Loading discovered jobs...</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- TAB 4: Review Queue -->
    <div id="tab-reviews" class="tab-content">
      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Reason</th>
              <th>Details</th>
              <th>Due</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody id="reviews-body">
            <tr><td colspan="5">No pending human reviews. Pipeline operating smoothly.</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- TAB 5: Interviews -->
    <div id="tab-interviews" class="tab-content">
      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>Company</th>
              <th>Round Type</th>
              <th>Scheduled Time</th>
              <th>Meeting Link</th>
            </tr>
          </thead>
          <tbody id="interviews-body">
            <tr><td colspan="4">No scheduled interviews.</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- TAB 6: CRM -->
    <div id="tab-crm" class="tab-content">
      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>Contact Name</th>
              <th>Email</th>
              <th>Role</th>
              <th>Company</th>
              <th>Last Contacted</th>
            </tr>
          </thead>
          <tbody id="crm-body">
            <tr><td colspan="5">No recruiter contacts tracked.</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- TAB 7: Audit Trail -->
    <div id="tab-audit" class="tab-content">
      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Action</th>
              <th>Entity</th>
              <th>Actor</th>
              <th>Result</th>
              <th>Details</th>
            </tr>
          </thead>
          <tbody id="audit-body">
            <tr><td colspan="6">Loading audit entries...</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </main>

  <script>
    let allJobs = [];

    function switchTab(tabId) {
      document.querySelectorAll('nav button').forEach(b => b.classList.remove('active'));
      event.target.classList.add('active');
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      document.getElementById('tab-' + tabId).classList.add('active');
      if (tabId === 'kanban') loadKanban();
      if (tabId === 'jobs') loadJobs();
      if (tabId === 'reviews') loadReviews();
      if (tabId === 'interviews') loadInterviews();
      if (tabId === 'crm') loadCRM();
      if (tabId === 'audit') loadAudit();
    }

    async function loadFunnel() {
      try {
        const res = await fetch('/api/funnel');
        const data = await res.json();
        document.getElementById('stat-discovered').innerText = data.total_jobs_discovered;
        document.getElementById('stat-submitted').innerText = data.total_submitted;
        document.getElementById('stat-sub-rate').innerText = data.conversion_rates.discovery_to_submission_pct + '% conversion';
        document.getElementById('stat-screening').innerText = data.total_screening;
        document.getElementById('stat-screen-rate').innerText = data.conversion_rates.submission_to_screen_pct + '% conversion';
        document.getElementById('stat-interviewing').innerText = data.total_interviewing;
        document.getElementById('stat-interview-rate').innerText = data.conversion_rates.screen_to_interview_pct + '% conversion';
        document.getElementById('stat-offers').innerText = data.total_offers;
        document.getElementById('stat-offer-rate').innerText = data.conversion_rates.interview_to_offer_pct + '% conversion';

        if (data.pending_reviews > 0) {
          const pill = document.getElementById('review-pill');
          pill.style.display = 'inline';
          pill.innerText = data.pending_reviews;
        }

        const srcRes = await fetch('/api/sources');
        const sources = await srcRes.json();
        const srcBody = document.getElementById('sources-body');
        srcBody.innerHTML = '';
        if (Object.keys(sources).length === 0) {
          srcBody.innerHTML = '<tr><td colspan="2">No job sources recorded.</td></tr>';
        } else {
          for (const [src, count] of Object.entries(sources)) {
            srcBody.innerHTML += `<tr><td><strong>${src}</strong></td><td>${count}</td></tr>`;
          }
        }
      } catch (e) {
        console.error("Failed to load funnel:", e);
      }
    }

    async function loadKanban() {
      const res = await fetch('/api/kanban');
      const board = await res.json();
      const container = document.getElementById('kanban-board');
      container.innerHTML = '';
      for (const [col, cards] of Object.entries(board)) {
        let colHtml = `<div class="kanban-col"><div class="col-title"><span>${col}</span><span>${cards.length}</span></div>`;
        cards.forEach(card => {
          let badgeClass = card.policy_decision === 'allowed' || card.policy_decision === 'AUTO_ALLOWED' ? 'badge-auto' : (card.policy_decision === 'assisted' || card.policy_decision === 'ASSISTED' ? 'badge-assisted' : 'badge-manual');
          colHtml += `
            <div class="kanban-card">
              <div class="card-company">${card.company}</div>
              <div class="card-title">${card.title}</div>
              <div class="card-meta">
                <span class="badge ${badgeClass}">${card.policy_decision}</span>
                <span>${card.application_mode}</span>
              </div>
            </div>`;
        });
        colHtml += `</div>`;
        container.innerHTML += colHtml;
      }
    }

    async function loadJobs() {
      const res = await fetch('/api/jobs');
      allJobs = await res.json();
      renderJobs(allJobs);
    }

    function renderJobs(jobs) {
      const tbody = document.getElementById('jobs-body');
      tbody.innerHTML = '';
      if (jobs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6">No jobs matching criteria.</td></tr>';
        return;
      }
      jobs.forEach(j => {
        tbody.innerHTML += `
          <tr>
            <td><strong>${j.company}</strong></td>
            <td>${j.title}</td>
            <td>${j.remote_type || '-'}</td>
            <td><span class="badge badge-assisted">${j.status}</span></td>
            <td>${j.first_seen_at ? new Date(j.first_seen_at).toLocaleDateString() : '-'}</td>
            <td>${j.apply_url ? `<a href="${j.apply_url}" target="_blank" style="color:var(--primary); font-weight:600;">Apply Link</a>` : '-'}</td>
          </tr>`;
      });
    }

    function filterJobs() {
      const q = document.getElementById('jobs-search').value.toLowerCase();
      const filtered = allJobs.filter(j => 
        j.company.toLowerCase().includes(q) || 
        j.title.toLowerCase().includes(q) || 
        (j.remote_type && j.remote_type.toLowerCase().includes(q))
      );
      renderJobs(filtered);
    }

    async function loadReviews() {
      const res = await fetch('/api/reviews');
      const reviews = await res.json();
      const tbody = document.getElementById('reviews-body');
      tbody.innerHTML = '';
      if (reviews.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5">No pending human reviews. Pipeline operating smoothly.</td></tr>';
        return;
      }
      reviews.forEach(r => {
        tbody.innerHTML += `
          <tr>
            <td><code>${r.id.substring(0, 8)}</code></td>
            <td><strong>${r.reason}</strong></td>
            <td><pre style="font-size:0.75rem; max-width:300px; white-space:pre-wrap;">${JSON.stringify(r.payload)}</pre></td>
            <td>${r.due_at ? new Date(r.due_at).toLocaleDateString() : 'Immediate'}</td>
            <td><button class="btn-sm" onclick="resolveReview('${r.id}')">Approve / Resolve</button></td>
          </tr>`;
      });
    }

    async function resolveReview(id) {
      const notes = prompt("Enter resolution notes or approved answer:");
      if (!notes) return;
      await fetch(`/api/reviews/${id}/resolve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ resolution_notes: notes })
      });
      loadReviews();
      loadFunnel();
    }

    async function loadInterviews() {
      const res = await fetch('/api/interviews');
      const list = await res.json();
      const tbody = document.getElementById('interviews-body');
      tbody.innerHTML = '';
      if (list.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4">No scheduled interviews.</td></tr>';
        return;
      }
      list.forEach(i => {
        tbody.innerHTML += `
          <tr>
            <td><strong>${i.company}</strong></td>
            <td>${i.round_type}</td>
            <td>${i.scheduled_start ? new Date(i.scheduled_start).toLocaleString() : 'TBD'}</td>
            <td>${i.location_or_link ? `<a href="${i.location_or_link}" target="_blank" style="color:var(--primary);">Join Call</a>` : 'None'}</td>
          </tr>`;
      });
    }

    async function loadCRM() {
      const res = await fetch('/api/contacts');
      const list = await res.json();
      const tbody = document.getElementById('crm-body');
      tbody.innerHTML = '';
      if (list.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5">No recruiter contacts tracked.</td></tr>';
        return;
      }
      list.forEach(c => {
        tbody.innerHTML += `
          <tr>
            <td><strong>${c.name}</strong></td>
            <td>${c.email || '-'}</td>
            <td>${c.role || '-'}</td>
            <td>${c.company || '-'}</td>
            <td>${c.last_contact_at ? new Date(c.last_contact_at).toLocaleDateString() : '-'}</td>
          </tr>`;
      });
    }

    async function loadAudit() {
      const res = await fetch('/api/audit');
      const entries = await res.json();
      const tbody = document.getElementById('audit-body');
      tbody.innerHTML = '';
      if (entries.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6">No recent audit events.</td></tr>';
        return;
      }
      entries.forEach(e => {
        tbody.innerHTML += `
          <tr>
            <td>${new Date(e.occurred_at).toLocaleString()}</td>
            <td><strong>${e.action_type}</strong></td>
            <td>${e.entity_type}</td>
            <td>${e.actor}</td>
            <td><span class="badge ${e.result === 'success' ? 'badge-auto' : 'badge-manual'}">${e.result}</span></td>
            <td><pre style="font-size:0.7rem; max-width:250px; white-space:pre-wrap;">${JSON.stringify(e.metadata)}</pre></td>
          </tr>`;
      });
    }

    // Init
    loadFunnel();
    document.getElementById('refresh-time').innerText = 'Last updated: ' + new Date().toLocaleTimeString();
  </script>
</body>
</html>
"""


class DashboardRequestHandler(BaseHTTPRequestHandler):
    """Handles REST API and UI requests for the Jobs Automation Dashboard."""

    session_factory: Callable[[], Session]

    def _send_json(self, data: Any, status: int = HTTPStatus.OK) -> None:
        payload = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _send_html(self, html_text: str, status: int = HTTPStatus.OK) -> None:
        payload = html_text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:  # noqa: N802
        url = urlparse(self.path)
        path = url.path.rstrip("/")

        if path in ("", "/index.html"):
            self._send_html(DASHBOARD_HTML)
            return

        with self.session_factory() as session:
            if path == "/api/funnel":
                service = FunnelAnalyticsService(session)
                self._send_json(service.get_funnel_summary())
                return

            if path == "/api/sources":
                service = FunnelAnalyticsService(session)
                self._send_json(service.get_source_breakdown())
                return

            if path == "/api/kanban":
                service = FunnelAnalyticsService(session)
                self._send_json(service.get_kanban_board())
                return

            if path == "/api/jobs":
                jobs = session.scalars(
                    select(JobModel).order_by(JobModel.first_seen_at.desc()).limit(100)
                ).all()
                data = [
                    {
                        "id": str(j.id),
                        "company": j.company_name,
                        "title": j.title,
                        "remote_type": j.remote_type,
                        "status": j.status,
                        "apply_url": j.apply_url,
                        "first_seen_at": j.first_seen_at.isoformat()
                        if j.first_seen_at
                        else None,
                    }
                    for j in jobs
                ]
                self._send_json(data)
                return

            if path == "/api/reviews":
                tasks = session.scalars(
                    select(TaskModel)
                    .where(TaskModel.status == "pending")
                    .order_by(TaskModel.due_at.asc().nulls_last())
                ).all()
                review_data: list[dict[str, Any]] = [
                    {
                        "id": str(t.id),
                        "job_id": str(t.job_id) if t.job_id else None,
                        "reason": t.task_type,
                        "payload": t.payload_json,
                        "status": t.status,
                        "due_at": t.due_at.isoformat() if t.due_at else None,
                    }
                    for t in tasks
                ]
                self._send_json(review_data)
                return

            if path == "/api/interviews":
                interviews = session.scalars(
                    select(InterviewModel).order_by(
                        InterviewModel.scheduled_start.desc()
                    )
                ).all()
                data = [
                    {
                        "id": str(i.id),
                        "application_id": str(i.application_id),
                        "company": i.application.job.company_name
                        if i.application and i.application.job
                        else "Unknown",
                        "round_type": i.round_type,
                        "scheduled_start": i.scheduled_start.isoformat()
                        if i.scheduled_start
                        else None,
                        "scheduled_end": i.scheduled_end.isoformat()
                        if i.scheduled_end
                        else None,
                        "location_or_link": i.location_or_link,
                        "status": i.status,
                    }
                    for i in interviews
                ]
                self._send_json(data)
                return

            if path.startswith("/api/interviews/") and path.endswith("/brief"):
                parts = path.split("/")
                if len(parts) == 5:
                    app_id_str = parts[3]
                    try:
                        from jobs_automation.intelligence.interview_service import InterviewIntelligenceService
                        svc = InterviewIntelligenceService(session)
                        brief = svc.build_brief(app_id_str)
                        self._send_json(json.loads(brief.model_dump_json()))
                        return
                    except LookupError as e:
                        self._send_json({"error": str(e)}, status=HTTPStatus.NOT_FOUND)
                        return
                    except Exception as e:
                        self._send_json({"error": str(e)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
                        return

            if path == "/api/contacts":
                contacts = session.scalars(
                    select(ContactModel).order_by(
                        ContactModel.last_contact_at.desc().nulls_last()
                    )
                ).all()
                data = [
                    {
                        "id": str(c.id),
                        "name": c.name,
                        "email": c.email,
                        "role": c.role,
                        "company": c.company.normalized_name if c.company else None,
                        "last_contact_at": c.last_contact_at.isoformat()
                        if c.last_contact_at
                        else None,
                    }
                    for c in contacts
                ]
                self._send_json(data)
                return

            if path == "/api/audit":
                entries = session.scalars(
                    select(AuditLogModel)
                    .order_by(AuditLogModel.occurred_at.desc())
                    .limit(50)
                ).all()
                audit_data: list[dict[str, Any]] = [
                    {
                        "id": str(e.id),
                        "action_type": e.action_type,
                        "entity_type": e.entity_type,
                        "actor": e.actor,
                        "result": e.result,
                        "occurred_at": e.occurred_at.isoformat(),
                        "metadata": e.metadata_json,
                    }
                    for e in entries
                ]
                self._send_json(audit_data)
                return

            if path == "/api/health":
                checker = HealthCheckService(self.session_factory)
                self._send_json(checker.run_full_check().model_dump(mode="json"))
                return

            if path == "/api/followups":
                followup_types = (
                    "UNANSWERED_RECRUITER",
                    "STALE_APPLICATION_FOLLOW_UP",
                    "STALE_SCREENING_FOLLOW_UP",
                )
                tasks = session.scalars(
                    select(TaskModel)
                    .where(TaskModel.task_type.in_(followup_types))
                    .order_by(TaskModel.due_at.asc().nulls_last())
                ).all()
                followup_data: list[dict[str, Any]] = [
                    {
                        "id": str(t.id),
                        "application_id": str(t.application_id) if t.application_id else None,
                        "job_id": str(t.job_id) if t.job_id else None,
                        "task_type": t.task_type,
                        "status": t.status,
                        "due_at": t.due_at.isoformat() if t.due_at else None,
                        "payload": t.payload_json,
                    }
                    for t in tasks
                ]
                self._send_json(followup_data)
                return

            if path == "/api/briefing":
                from jobs_automation.intelligence.briefing_service import CareerBriefingService
                limit = int(params.get("limit", [10])[0]) if params.get("limit") else 10
                svc = CareerBriefingService(session)
                brief = svc.build(limit=limit)
                self._send_json(json.loads(brief.model_dump_json()))
                return

            if path == "/api/analytics/sources":
                service = FunnelAnalyticsService(session)
                self._send_json(service.get_source_performance())
                return

            if path == "/api/analytics/roles":
                service = FunnelAnalyticsService(session)
                self._send_json(service.get_role_family_performance())
                return

            if path == "/api/analytics/resumes":
                service = FunnelAnalyticsService(session)
                self._send_json(service.get_resume_performance())
                return

            if path == "/api/analytics/time-to-stage":
                service = FunnelAnalyticsService(session)
                self._send_json(service.get_time_to_stage())
                return

            if path == "/api/timeline":
                crm = RecruiterCRMService(session)
                params = parse_qs(url.query)
                app_ids = params.get("application_id", [])
                contact_ids = params.get("contact_id", [])
                if app_ids:
                    try:
                        timeline = crm.get_timeline_for_application(uuid.UUID(app_ids[0]))
                        self._send_json(timeline)
                        return
                    except ValueError:
                        self.send_error(HTTPStatus.BAD_REQUEST, "Invalid application UUID")
                        return
                elif contact_ids:
                    try:
                        timeline = crm.get_timeline_for_contact(uuid.UUID(contact_ids[0]))
                        self._send_json(timeline)
                        return
                    except ValueError:
                        self.send_error(HTTPStatus.BAD_REQUEST, "Invalid contact UUID")
                        return
                else:
                    # Default: return recent touchpoints
                    self._send_json([])
                    return

            if path == "/api/offers-rejections":
                terminal_or_offer = (
                    "OFFER_RECEIVED",
                    "OFFER_ACCEPTED",
                    "OFFER_DECLINED",
                    "ONBOARDING",
                    "REJECTED",
                    "WITHDRAWN",
                )
                apps = session.scalars(
                    select(ApplicationModel)
                    .where(ApplicationModel.status.in_(terminal_or_offer))
                    .order_by(ApplicationModel.last_activity_at.desc())
                ).all()
                data = [
                    {
                        "application_id": str(a.id),
                        "company": a.job.company_name if a.job else "Unknown",
                        "title": a.job.normalized_title if a.job else "Unknown",
                        "status": a.status,
                        "applied_at": a.applied_at.isoformat() if a.applied_at else None,
                        "closed_at": a.closed_at.isoformat() if a.closed_at else None,
                        "last_activity_at": a.last_activity_at.isoformat() if a.last_activity_at else None,
                    }
                    for a in apps
                ]
                self._send_json(data)
                return

            if path == "/api/policies":
                policies = session.scalars(select(PolicyRegistryModel)).all()
                data = [
                    {
                        "id": str(p.id),
                        "platform": p.platform,
                        "domain_pattern": p.domain_pattern,
                        "capability": p.capability,
                        "decision": p.decision,
                        "adapter": p.adapter,
                        "reviewed_at": p.reviewed_at.isoformat(),
                        "review_due_at": p.review_due_at.isoformat() if p.review_due_at else None,
                    }
                    for p in policies
                ]
                self._send_json(data)
                return

            if path == "/api/worker":
                sweeps = session.scalars(
                    select(AuditLogModel)
                    .where(AuditLogModel.action_type == "worker_sweep")
                    .order_by(AuditLogModel.occurred_at.desc())
                    .limit(20)
                ).all()
                worker_data: list[dict[str, Any]] = [
                    {
                        "id": str(s.id),
                        "result": s.result,
                        "occurred_at": s.occurred_at.isoformat(),
                        "metrics": s.metadata_json,
                    }
                    for s in sweeps
                ]
                self._send_json(worker_data)
                return

        self.send_error(HTTPStatus.NOT_FOUND, "Not Found")

    def _authorize_write_operation(self) -> bool:
        """Enforces operator write safety for state-changing endpoints (B-R20-06).

        Requirements:
        1. If DASHBOARD_WRITE_TOKEN environment variable is set:
           Request must provide matching 'X-Operator-Token' or 'Authorization: Bearer <token>' header.
        2. If DASHBOARD_WRITE_TOKEN is not set:
           Request must originate from a trusted local loopback address ('127.0.0.1', '::1', 'localhost')
           AND DASHBOARD_ALLOW_LOCAL_WRITE must not be explicitly disabled ('false').
        3. All other requests fail closed with 401 Unauthorized or 403 Forbidden.
        """
        configured_token = os.getenv("DASHBOARD_WRITE_TOKEN")
        if configured_token:
            provided_token = self.headers.get("X-Operator-Token")
            if not provided_token:
                auth_header = self.headers.get("Authorization", "")
                if auth_header.startswith("Bearer "):
                    provided_token = auth_header[7:].strip()

            if provided_token == configured_token:
                return True

            self._send_json(
                {"error": "Unauthorized: missing or invalid operator write token."},
                status=HTTPStatus.UNAUTHORIZED,
            )
            return False

        # If no token configured, check for local trusted loopback mode
        allow_local = os.getenv("DASHBOARD_ALLOW_LOCAL_WRITE", "true").lower() in ("true", "1", "yes")
        client_ip = self.client_address[0] if hasattr(self, "client_address") and self.client_address else "127.0.0.1"

        if allow_local and client_ip in ("127.0.0.1", "::1", "localhost", "testclient"):
            return True

        self._send_json(
            {
                "error": "Forbidden: write operations require DASHBOARD_WRITE_TOKEN or trusted local loopback origin."
            },
            status=HTTPStatus.FORBIDDEN,
        )
        return False

    def do_POST(self) -> None:  # noqa: N802
        url = urlparse(self.path)
        path = url.path.rstrip("/")

        # Enforce write safety gate before processing any state-changing mutations
        if not self._authorize_write_operation():
            return

        # Check for /api/reviews/{id}/resolve
        if path.startswith("/api/reviews/") and path.endswith("/resolve"):
            parts = path.split("/")
            if len(parts) == 5:
                review_id_str = parts[3]
                try:
                    review_uuid = uuid.UUID(review_id_str)
                except ValueError:
                    self.send_error(HTTPStatus.BAD_REQUEST, "Invalid UUID")
                    return

                content_len = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_len).decode("utf-8") if content_len > 0 else "{}"
                body_json = json.loads(body) if body else {}

                with self.session_factory() as session:
                    task = session.get(TaskModel, review_uuid)
                    if not task:
                        self.send_error(HTTPStatus.NOT_FOUND, "Task not found")
                        return

                    task.status = "completed"
                    updated_payload = dict(task.payload_json) if task.payload_json else {}
                    updated_payload["resolution_notes"] = body_json.get(
                        "resolution_notes", "Resolved via dashboard"
                    )
                    task.payload_json = updated_payload
                    session.commit()
                    self._send_json({"success": True, "id": review_id_str, "status": "completed"})
                    return

        self.send_error(HTTPStatus.NOT_FOUND, "Not Found")

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress standard BaseHTTPRequestHandler console stderr spam."""
        logger.debug(
            "%s - - [%s] %s",
            self.address_string(),
            self.log_date_time_string(),
            format % args,
        )


class DashboardServer:
    """Configures and runs the embedded threaded Dashboard HTTP server."""

    def __init__(
        self,
        session_factory: Callable[[], Session],
        host: str = "127.0.0.1",
        port: int = 8765,
    ) -> None:
        self.host = host
        self.port = port
        self.session_factory = session_factory

        # Create custom handler subclass with session_factory bound
        handler = type(
            "BoundDashboardRequestHandler",
            (DashboardRequestHandler,),
            {"session_factory": staticmethod(session_factory)},
        )
        self.httpd = ThreadingHTTPServer((self.host, self.port), handler)

    def serve_forever(self) -> None:
        logger.info("Serving Dashboard on http://%s:%s", self.host, self.port)
        self.httpd.serve_forever()

    def shutdown(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()
