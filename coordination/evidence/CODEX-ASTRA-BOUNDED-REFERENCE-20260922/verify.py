import os,json,subprocess,time
from pathlib import Path
import psycopg
from psycopg import sql
repo=Path('/tmp/jobs-astra-bounded-reference-20260922');out=Path('/tmp/jobs-astra-bounded-reference-evidence-20260922')
socket='/var/folders/fg/lmdhrms177s93m879bkgvjzr0000gn/T/jobs-proof-pg-7_ashjwd'
pg={}
with psycopg.connect(dbname='postgres',user='pchordia',host=socket,port=56422,autocommit=True) as c:
    for k in ['data_directory','port','listen_addresses']:
        pg[k]=c.execute(sql.SQL('SHOW {}').format(sql.Identifier(k))).fetchone()[0]
    pg['user']=c.execute('select current_user').fetchone()[0]
    assert pg['user']=='pchordia' and pg['port']=='56422' and pg['listen_addresses']==''
    pg['before_dbs']=[r[0] for r in c.execute("select datname from pg_database where datname like 'proof_it_%'")]
    pg['before_roles']=[r[0] for r in c.execute("select rolname from pg_roles where rolname like 'proof_it_role_%'")]
env=os.environ.copy();env['PYTHONPATH']=f'{repo}/src:{repo}';env['PROOF_TEST_PG_ADMIN_URL']=f'postgresql+psycopg://pchordia@/postgres?host={socket}&port=56422'
start=time.monotonic();p=subprocess.run(['/tmp/jobs-v17-cli-gate-20260922/.venv/bin/python','-m','pytest','-q'],cwd=repo,env=env,capture_output=True,text=True)
(out/'full-pytest.log').write_text(p.stdout+p.stderr)
with psycopg.connect(dbname='postgres',user='pchordia',host=socket,port=56422,autocommit=True) as c:
    pg['after_dbs']=[r[0] for r in c.execute("select datname from pg_database where datname like 'proof_it_%'")]
    pg['after_roles']=[r[0] for r in c.execute("select rolname from pg_roles where rolname like 'proof_it_role_%'")]
pg['new_remaining_dbs']=sorted(set(pg['after_dbs'])-set(pg['before_dbs']));pg['new_remaining_roles']=sorted(set(pg['after_roles'])-set(pg['before_roles']))
(out/'postgres.json').write_text(json.dumps(pg,indent=2)+'\n')
(out/'full-check.json').write_text(json.dumps({'exit_code':p.returncode,'seconds':time.monotonic()-start,'tree':subprocess.check_output(['git','write-tree'],cwd=repo,text=True).strip()},indent=2)+'\n')
print(p.stdout[-2000:]);print(json.dumps(pg));raise SystemExit(p.returncode)
