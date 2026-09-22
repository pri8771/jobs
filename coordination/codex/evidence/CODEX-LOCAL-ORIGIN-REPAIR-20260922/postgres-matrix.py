"""Source-bound J20-01 mutation/auth diagnostic. Synthetic PostgreSQL only."""
from __future__ import annotations

import ast
import hashlib
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

SOURCE = Path('/Users/pchordia/Downloads/swarm_codex/review/jobs-local-origin-source')
OUT = Path('/tmp/jobs-local-origin-pg-20260922')
OUT.mkdir(exist_ok=True)
SOCKET = '/var/folders/fg/lmdhrms177s93m879bkgvjzr0000gn/T/jobs-proof-pg-7_ashjwd'
PORT = 56422
EXPECTED = os.environ['JOBS_ORIGIN_EXPECTED'].split(':')
assert len(EXPECTED) == 2 and all(len(value) == 40 for value in EXPECTED)
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
        'authorization': 'Exact token, or enabled local peer plus mandatory loopback Host and strict optional matching HTTP Origin/fetch metadata.',
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
        hdrs = {'Content-Length': str(len(body)), 'Content-Type': 'application/json', 'Host': 'localhost:8765'}
        hdrs.update(headers or {})
        hdrs = {key: value for key, value in hdrs.items() if value is not None}
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
            'changed_tables': sorted(changes),
            'before_table_sha256': {table: hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest() for table,rows in before.items()},
            'after_table_sha256': {table: hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest() for table,rows in after.items()},
            'changed_rows': {table: [{'before': a, 'after': b} for a,b in zip(before[table],after[table]) if a != b] for table in changes},
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

    # Matrix required by native release 0f5522b. Every denial opens no DB session.
    probe('local_cli', client='127.0.0.1', expected=200)
    probe('same_origin_ui', client='127.0.0.1', headers={'Origin':'http://localhost:8765'}, expected=200)
    probe('ipv6_normalized', client='::1', headers={'Host':'[0:0:0:0:0:0:0:1]:8765','Origin':'http://[::1]:8765'}, expected=200)
    probe('default_port80', client='127.0.0.1', headers={'Host':'localhost','Origin':'http://LOCALHOST:80'}, expected=200)
    probe('explicit_port80', client='127.0.0.1', headers={'Host':'LOCALHOST:80','Origin':'http://localhost'}, expected=200)
    for name, host in [('missing',None),('empty',''),('path','localhost:8765/'),('userinfo','user@localhost:8765'),('foreign','foreign-origin.example:8765'),('bad_port','localhost:invalid'),('empty_port','localhost:'),('out_of_range','localhost:65536'),('space',' localhost:8765'),('malformed_ipv6','[:::1]:8765'),('unicode','localhoſt:8765')]:
        probe('host_'+name, client='127.0.0.1', headers={'Host':host})
    for name, origin in [('foreign','https://foreign-origin.example'),('null','null'),('empty',''),('path','http://localhost:8765/'),('multiple','http://localhost:8765 http://localhost:8765'),('https','https://localhost:8765'),('port_mismatch','http://localhost:8766'),('host_mismatch','http://127.0.0.1:8765'),('userinfo','http://user@localhost:8765')]:
        probe('origin_'+name, client='127.0.0.1', headers={'Origin':origin,'Content-Type':'text/plain'})
    for value in ('cross-site','same-site','unknown','', 'same-origin, none'):
        probe('fetch_denied_'+value, client='127.0.0.1', headers={'Sec-Fetch-Site':value})
    for value in ('same-origin','none'):
        probe('fetch_allowed_'+value, client='127.0.0.1', headers={'Origin':'http://localhost:8765','Sec-Fetch-Site':value}, expected=200)
    probe('remote_peer',headers={'Origin':'http://localhost:8765'})
    probe('synthetic_peer',client='testclient')
    probe('hostname_peer',client='localhost')
    probe('disabled',client='127.0.0.1',allow='false')
    probe('invalid_enable',client='127.0.0.1',allow='invalid')
    probe('valid_token',token='synthetic-token',headers={'X-Operator-Token':'synthetic-token','Host':'foreign-origin.example','Origin':'null','Sec-Fetch-Site':'cross-site'},expected=200)
    probe('valid_bearer',token='synthetic-token',headers={'Authorization':'Bearer synthetic-token','Host':None},expected=200)
    probe('wrong_token',client='127.0.0.1',token='synthetic-token',headers={'X-Operator-Token':'wrong'},expected=401)
    probe('missing_token',client='127.0.0.1',token='synthetic-token',expected=401)
    for verb in ('PUT','PATCH','DELETE','OPTIONS','HEAD'):
        probe('unsupported_'+verb,method=verb,raw_dispatch=True,expected=501)
    report['result']='PASS_STRICT_LOCAL_ORIGIN_MATRIX'
    report['scope_limit']='Direct handler plus synthetic PostgreSQL; no browser or external operation.'

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
                      'result': report.get('result'), 'cleanup_database_count': count,
                      'source_still_clean': report['source_still_clean']}, indent=2, sort_keys=True))
