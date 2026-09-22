import datetime
import io
import json

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from jobs_automation.dashboard.server import DashboardRequestHandler
from jobs_automation.db.base import Base
from jobs_automation.db.models import AuditLogModel
from jobs_automation.health import HealthCheckService


class Handler(DashboardRequestHandler):
    def __init__(self, path, factory):
        self.path = path
        self.session_factory = factory
        self.mock_wfile = io.BytesIO()
        self.wfile = self.mock_wfile
        self.headers = {}
        self.status_code = None

    def send_response(self, code, message=None):
        self.status_code = code

    def send_header(self, *_args):
        pass

    def end_headers(self):
        pass

    def log_message(self, *_args):
        pass


engine = create_engine("sqlite:///:memory:")
Base.metadata.create_all(engine)
factory = sessionmaker(bind=engine)
run_id = "fixture-current-worker-run"
now = datetime.datetime.now(datetime.UTC)
with factory() as session:
    session.add(AuditLogModel(
        action_type="worker_run",
        entity_type="worker",
        actor="worker_daemon",
        result="RUNNING",
        external_reference=run_id,
        occurred_at=now - datetime.timedelta(seconds=1),
        metadata_json={"run_id": run_id},
    ))
    session.add(AuditLogModel(
        action_type="worker_run_finished",
        entity_type="worker",
        actor="worker_daemon",
        result="SUCCESS",
        external_reference=run_id,
        occurred_at=now,
        metadata_json={"run_id": run_id, "error_count": 0},
    ))
    session.commit()

handler = Handler("/api/worker", factory)
handler.do_GET()
api_worker = json.loads(handler.mock_wfile.getvalue())
health_worker = HealthCheckService(factory).check_worker().model_dump(mode="json")
print(json.dumps({
    "api_status": handler.status_code,
    "api_worker": api_worker,
    "health_worker": health_worker,
}, indent=2, sort_keys=True))
