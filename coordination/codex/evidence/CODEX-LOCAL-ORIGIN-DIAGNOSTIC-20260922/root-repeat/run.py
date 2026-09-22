"""Source-bound J20-01 mutation/auth diagnostic. Synthetic PostgreSQL only."""
from __future__ import annotations

import ast
import contextlib
import io
import json
import os
import subprocess
import uuid
from datetime import UTC, datetime
from pathlib import Path

import psycopg
from psycopg import sql
from sqlalchemy import create_engine, select
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker

import jobs_automation.dashboard.server as server
from jobs_automation.db.base import Base
from jobs_automation.db.models import TaskModel
from tests.test_dashboard import DummyRequestHandler

SOURCE = Path('/Users/pchordia/Downloads/swarm_codex/review/jobs-config-status-source')
OUT = Path('/tmp/jobs-control-safety-root-20260922')
OUT.mkdir(exist_ok=True)
SOCKET = '/var/folders/fg/lmdhrms177s93m879bkgvjzr0000gn/T/jobs-proof-pg-7_ashjwd'
PORT = 56422
EXPECTED = ['413a18ee13ee049f57651ddd7060fd98fafad5f9', 'f40e443a084e4a2e5c6a4ac7cbc4f6dcf791cfa6']
git = lambda *args: subprocess.check_output(['git', *args], cwd=SOURCE, text=True).strip()
assert git('remote', 'get-url', 'origin') == 'https://github.com/pri8771/jobs.git'
assert git('rev-parse', 'HEAD', 'HEAD^{tree}').splitlines() == EXPECTED
assert git('status', '--porcelain') == ''
assert Path(server.__file__).resolve() == SOURCE / 'src/jobs_automation/dashboard/server.py'
source_text = Path(server.__file__).read_text()
tree = ast.parse(source_text)
methods = [{"method": n.name, "line": n.lineno} for n in ast.walk(tree)
           if isinstance(n, ast.FunctionDef) and n.name.startswith('do_')]
assert [m['method'] for m in methods] == ['do_GET', 'do_POST']
report = {
    'started_utc': datetime.now(UTC).isoformat(),
    'source_sha': EXPECTED[0], 'source_tree': EXPECTED[1],
    'source_module': str(Path(server.__file__).resolve()),
    'engineering_only': True,
    'handler_methods': methods,
    'mutation_inventory': [{
        'method': 'POST', 'route': '/api/reviews/{id}/resolve',
        'dispatch_line': 894, 'mutation_lines': [914, 919, 920],
        'mutation': 'Set task.status=completed and task.payload_json.resolution_notes; session.commit()',
        'authorization': 'Configured nonempty token requires exact X-Operator-Token or Bearer match; otherwise allow_local truthy and client_address in loopback/trusted tuple.',
    }],
    'cases': [],
}


@contextlib.contextmanager
def mode(token=None, allow=None):
    saved = {key: os.environ.get(key) for key in ('DASHBOARD_WRITE_TOKEN', 'DASHBOARD_ALLOW_LOCAL_WRITE')}
    for key, val in [('DASHBOARD_WRITE_TOKEN', token), ('DASHBOARD_ALLOW_LOCAL_WRITE', allow)]:
        if val is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = val
    try:
        yield
    finally:
        for key, val in saved.items():
            if val is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = val


db_name = f'j20_safety_{uuid.uuid4().hex[:16]}'
admin = psycopg.connect(host=SOCKET, port=PORT, dbname='postgres', autocommit=True)
engine = None
created = False
try:
    host_info = admin.execute("select current_user, current_setting('port'), current_setting('listen_addresses')").fetchone()
    assert host_info[1:] == (str(PORT), '')
    report['postgres'] = {'socket': SOCKET, 'port': PORT, 'listen_addresses': host_info[2], 'database': db_name}
    admin.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(db_name)))
    created = True
    engine = create_engine(URL.create('postgresql+psycopg', username=host_info[0], database=db_name,
                                     query={'host': SOCKET, 'port': str(PORT)}))
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)

    def snapshot():
        with engine.connect() as conn:
            # Include every table and every column. All rows are synthetic.
            return {table.name: sorted((json.loads(json.dumps(dict(row), default=str, sort_keys=True))
                                       for row in conn.execute(select(table)).mappings()),
                                      key=lambda row: json.dumps(row, sort_keys=True))
                    for table in Base.metadata.sorted_tables}

    def seed():
        task_id = uuid.uuid4()
        with factory() as session:
            session.add(TaskModel(id=task_id, task_type='NEEDS_REVIEW', status='pending',
                                  payload_json={'synthetic': True, 'question': 'Synthetic approved range?'}))
            session.commit()
        return task_id

    def probe(name, *, client='198.51.100.23', token=None, allow=None, headers=None,
              expected=403, method='POST', raw_dispatch=False):
        task_id = seed()
        before = snapshot()
        opens = []
        def tracked_factory():
            opens.append(True)
            return factory()
        body = json.dumps({'resolution_notes': f'Synthetic diagnostic: {name}'}).encode()
        hdrs = {'Content-Length': str(len(body)), 'Content-Type': 'application/json'}
        hdrs.update(headers or {})
        route = f'/api/reviews/{task_id}/resolve'
        handler = DummyRequestHandler(method, route, body=body, headers=hdrs,
                                      session_factory=tracked_factory, client_address=(client, 12345))
        with mode(token, allow):
            if raw_dispatch:
                raw = f'{method} {route} HTTP/1.1\r\nHost: localhost:8765\r\nContent-Length: {len(body)}\r\n\r\n'.encode() + body
                handler.rfile = io.BytesIO(raw)
                handler.handle_one_request()
            else:
                handler.do_POST()
        after = snapshot()
        changes = {table: {'before': before[table], 'after': after[table]}
                   for table in before if before[table] != after[table]}
        wire = handler.mock_wfile.getvalue()
        result = {
            'name': name, 'method': method, 'route': route, 'client_ip': client,
            'token_configured': bool(token), 'allow_local': allow,
            'header_names': sorted(hdrs), 'origin': hdrs.get('Origin'),
            'expected_status': expected, 'actual_status': int(handler.status_code),
            'database_session_entries': len(opens),
            'changed_tables': sorted(changes), 'database_effect': changes,
            'response': json.loads(wire) if wire else None,
        }
        report['cases'].append(result)
        assert handler.status_code == expected, result
        if expected != 200:
            assert not changes and not opens, result
        else:
            assert sorted(changes) == ['task'] and len(opens) == 1, result
            old = next(row for row in before['task'] if row['id'] == str(task_id))
            new = next(row for row in after['task'] if row['id'] == str(task_id))
            assert new['status'] == 'completed'
            assert new['payload_json']['resolution_notes'] == f'Synthetic diagnostic: {name}'
            assert {key for key in old if old[key] != new[key]} == {'status', 'payload_json'}
            assert sum(a != b for a, b in zip(before['task'], after['task'])) == 1
        return result

    # One mutation route. Every negative proves no session entry/no change in any table.
    probe('remote_ipv4_no_token')
    probe('remote_ipv6_no_token', client='2001:db8::23')
    probe('remote_spoofed_loopback_headers', headers={'Host': 'localhost:8765', 'X-Forwarded-For': '127.0.0.1', 'X-Real-IP': '127.0.0.1', 'Origin': 'http://localhost:8765'})
    probe('remote_with_unconfigured_supplied_token', headers={'X-Operator-Token': 'synthetic-token'})
    probe('remote_configured_missing_token', token='synthetic-token', expected=401)
    probe('remote_configured_wrong_token', token='synthetic-token', headers={'X-Operator-Token': 'wrong'}, expected=401)
    probe('local_configured_missing_token', client='127.0.0.1', token='synthetic-token', expected=401)
    probe('local_ipv4_default', client='127.0.0.1', expected=200)
    probe('local_ipv6_default', client='::1', expected=200)
    probe('local_disabled', client='127.0.0.1', allow='false')
    probe('local_invalid_enable_fails_closed', client='127.0.0.1', allow='invalid')
    probe('remote_valid_operator_header', token='synthetic-token', headers={'X-Operator-Token': 'synthetic-token'}, expected=200)
    probe('remote_valid_bearer', token='synthetic-token', headers={'Authorization': 'Bearer synthetic-token'}, expected=200)
    probe('remote_valid_token_local_disabled', token='synthetic-token', allow='false', headers={'X-Operator-Token': 'synthetic-token'}, expected=200)
    for verb in ('PUT', 'PATCH', 'DELETE', 'OPTIONS', 'HEAD'):
        probe(f'{verb.lower()}_unavailable', method=verb, expected=501, raw_dispatch=True)

    # Origin/Content-Type are production header cases, not a browser exploitation claim.
    # Match a foreign-origin simple POST shape. A loopback peer alone does not establish
    # that the initiating origin is the trusted local operator.
    foreign = probe('foreign_origin_tokenless_loopback', client='127.0.0.1',
                    headers={'Origin': 'https://foreign-origin.example',
                             'Host': '127.0.0.1:8765', 'Content-Type': 'text/plain'}, expected=200)
    report['first_gap'] = {
        'name': 'Foreign-Origin tokenless loopback POST mutates a review',
        'reproduced_actual_status': foreign['actual_status'],
        'expected_safety_disposition': 'Foreign initiating origin should not acquire trusted local operator authorization solely because TCP peer is loopback; reject or require an operator token.',
        'root_cause': 'Authorization fallback at server.py:870-875 checks only allow-local environment and client_address; Origin, Host, and Sec-Fetch-Site are unused. POST then parses JSON without restricting Content-Type.',
        'scope_limit': 'Direct accepted production handler plus PostgreSQL proves header acceptance and committed mutation. No browser-origin execution, CORS/PNA reachability, DNS rebinding, or remote-TCP authentication bypass is claimed.',
        'smallest_repair_proposal': 'In tokenless local fallback, reject explicitly foreign Origin and cross-site browser metadata before accepting loopback. Preserve no-Origin local tools and same-origin UI; valid token remains explicit authority. Add focused synthetic direct-handler regressions only after repair release.',
    }
    report['stop_reason'] = 'First concrete local-authorization boundary gap; no remaining read completeness probes executed.'
finally:
    if engine is not None:
        engine.dispose()
    if created:
        admin.execute(sql.SQL('DROP DATABASE {}').format(sql.Identifier(db_name)))
    count = admin.execute('select count(*) from pg_database where datname=%s', (db_name,)).fetchone()[0]
    report['cleanup_database_count'] = count
    assert count == 0
    admin.close()
    report['finished_utc'] = datetime.now(UTC).isoformat()
    report['source_still_clean'] = git('status', '--porcelain') == ''
    (OUT / 'result.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'source_sha': EXPECTED[0], 'case_count': len(report['cases']),
                      'first_gap': report.get('first_gap'), 'cleanup_database_count': count,
                      'source_still_clean': report['source_still_clean']}, indent=2, sort_keys=True))
