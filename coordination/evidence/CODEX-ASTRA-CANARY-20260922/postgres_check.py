from pathlib import Path
import json, os, subprocess, sys, uuid
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from tests.test_gmail_adapter_bounded import test_independent_malformed_header_cannot_hide_canary
admin_url='postgresql+psycopg://pchordia@/postgres?host=/var/folders/fg/lmdhrms177s93m879bkgvjzr0000gn/T/jobs-proof-pg-7_ashjwd&port=56422'
admin=create_engine(admin_url,isolation_level='AUTOCOMMIT')
results=[]
for case in ['From','Cc','To']:
    name='jobs_astra_canary_'+uuid.uuid4().hex[:10]
    with admin.connect() as conn:conn.execute(text(f'CREATE DATABASE "{name}"'))
    db_url=admin_url.replace('/postgres?',f'/{name}?')
    engine=None
    try:
        migration=subprocess.run([sys.executable,'-m','alembic','upgrade','head'],env={**os.environ,'DATABASE_URL':db_url},capture_output=True,text=True)
        if migration.returncode:raise RuntimeError(migration.stderr)
        engine=create_engine(db_url)
        with Session(engine) as session:test_independent_malformed_header_cannot_hide_canary(session,case)
        engine.dispose()
        readback=subprocess.run([sys.executable,'-c',"import os; from sqlalchemy import create_engine,text; e=create_engine(os.environ['DATABASE_URL']); c=e.connect(); assert c.execute(text(\"select count(*) from inbound_message where headers_json::jsonb -> '_provider' ->> 'canary' = 'true'\")).scalar()==1; c.close(); e.dispose(); print('fresh-process durable canary count=1')"],env={**os.environ,'DATABASE_URL':db_url},capture_output=True,text=True)
        if readback.returncode:raise RuntimeError(readback.stderr)
        results.append({'case':case,'migration_exit':migration.returncode,'fresh_process_exit':readback.returncode,'result':'pass'})
    finally:
        if engine:engine.dispose()
        with admin.connect() as conn:
            conn.execute(text(f'DROP DATABASE "{name}"'))
            count=conn.execute(text('select count(*) from pg_database where datname=:n'),{'n':name}).scalar()
            assert count==0
            print(json.dumps({'case':case,'database':name,'remaining_databases':count}),flush=True)
admin.dispose()
print(json.dumps(results,indent=2))
