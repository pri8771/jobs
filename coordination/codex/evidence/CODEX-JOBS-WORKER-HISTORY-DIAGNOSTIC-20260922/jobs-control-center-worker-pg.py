import json, os
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from jobs_automation.adapters.gmail import MockEmailAdapter
from jobs_automation.worker import WorkerDaemon
from jobs_automation.db.models import AuditLogModel
from jobs_automation.health import HealthCheckService
from tests.test_dashboard import DummyRequestHandler

engine = create_engine(os.environ['DATABASE_URL'])
factory = sessionmaker(bind=engine)
worker = WorkerDaemon(factory, email_adapter=MockEmailAdapter([]))
run = worker.run_sweep()
handler = DummyRequestHandler('GET', '/api/worker', session_factory=factory)
handler.do_GET()
history = json.loads(handler.mock_wfile.getvalue())
health = HealthCheckService(factory).check_worker().model_dump(mode='json')
with factory() as session:
    rows = session.scalars(select(AuditLogModel).where(AuditLogModel.action_type.in_(['worker_run', 'worker_run_finished']))).all()
    durable = [{'type': r.action_type, 'status': r.result, 'run_id': r.external_reference} for r in rows]
assert len(durable) == 2 and run['errors'] == []
assert health['details']['last_attempt_status'] == 'SUCCESS'
assert handler.status_code == 200 and history == []
print(json.dumps({'result': 'REPRODUCED_WORKER_HISTORY_GAP', 'source_sha': os.environ['SOURCE_SHA'],
                  'actual_worker_run': run, 'durable_records': durable, 'http_status': handler.status_code,
                  'api_worker': history, 'worker_health': health}, indent=2, sort_keys=True))
engine.dispose()
