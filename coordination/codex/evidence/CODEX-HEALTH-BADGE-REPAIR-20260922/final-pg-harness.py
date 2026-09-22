"""Reproduce static live badge against truthful degraded health."""

from __future__ import annotations

import json
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from tests.test_dashboard import DummyRequestHandler
from tests.test_dashboard_health_badge import _run


engine = create_engine(os.environ["DATABASE_URL"])
factory = sessionmaker(bind=engine)

index = DummyRequestHandler("GET", "/", session_factory=factory)
index.do_GET()
html = index.mock_wfile.getvalue().decode("utf-8")

health_handler = DummyRequestHandler("GET", "/api/health", session_factory=factory)
health_handler.do_GET()
health = json.loads(health_handler.mock_wfile.getvalue())

result = {
    "result": "HEALTH_BADGE_MATCHES_ACTUAL_DEGRADED_HEALTH",
    "source_sha": os.environ["SOURCE_SHA"],
    "source_tree": os.environ["SOURCE_TREE"],
    "index_status": index.status_code,
    "health_status": health_handler.status_code,
    "header_claim": "System Live" if "System Live" in html else None,
    "header_has_health_fetch": "fetch('/api/health'," in html,
    "overall_health": health["overall_status"],
    "rendered": _run({"kind": "response", "payload": health}),
    "component_statuses": {
        name: component["status"] for name, component in health["components"].items()
    },
    "gmail_readiness": health["components"]["gmail"]["details"]["readiness_state"],
    "ats_live_capable": health["components"]["adapters"]["details"][
        "live_capable_platforms"
    ],
}
assert result["index_status"] == result["health_status"] == 200
assert result["header_claim"] is None
assert "fetch('/api/health'," in html
assert result["rendered"]["text"] == "Degraded"
assert "health-degraded" in result["rendered"]["className"]
assert result["rendered"]["calls"].count("/api/health") == 1
assert result["overall_health"] in {"DEGRADED", "UNHEALTHY"}
assert result["gmail_readiness"] != "PROVEN"
assert result["ats_live_capable"] == []
print(json.dumps(result, indent=2, sort_keys=True))
engine.dispose()
