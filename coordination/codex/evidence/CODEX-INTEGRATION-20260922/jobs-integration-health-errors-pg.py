from __future__ import annotations
import json, subprocess, uuid
from sqlalchemy import URL, create_engine, text
from sqlalchemy.orm import sessionmaker
from jobs_automation.db.base import Base
from jobs_automation.health import HealthCheckService

socket='/var/folders/fg/lmdhrms177s93m879bkgvjzr0000gn/T/jobs-proof-pg-7_ashjwd'
name='jobs_health_errors_'+uuid.uuid4().hex[:12]
def url(db):
 return URL.create('postgresql+psycopg',username='pchordia',database=db,query={'host':socket,'port':'56422'})
admin=create_engine(url('postgres'),isolation_level='AUTOCOMMIT')
with admin.connect() as conn: conn.execute(text(f'CREATE DATABASE {name}'))
engine=create_engine(url(name));factory=sessionmaker(bind=engine)
try:
 Base.metadata.create_all(engine)
 normal=HealthCheckService(factory)
 assert normal.check_database().status in {'HEALTHY','DEGRADED'}
 assert normal.check_policy_registry().status=='HEALTHY'
 gmail=normal.check_gmail()
 assert gmail.details.get('readiness_state')!='PROVEN'
 markers=['password=synthetic-password','access_token=synthetic-token','Bearer synthetic-bearer','email_body=synthetic-private-body']
 def fail_with_real_pg_exception():
  with factory() as session:
   session.execute(text('SELECT CAST(:value AS INTEGER)'),{'value':' '.join(markers)})
  raise AssertionError('real PostgreSQL error was expected')
 faulty=HealthCheckService(fail_with_real_pg_exception)
 results={}
 for component,category in [('database','DATABASE_CHECK_FAILED'),('policy_registry','POLICY_HEALTH_CHECK_FAILED'),('worker','WORKER_HEALTH_CHECK_FAILED'),('gmail','GMAIL_HEALTH_CHECK_FAILED')]:
  result=getattr(faulty,'check_'+component)()
  assert result.status=='UNHEALTHY' and result.details=={'error_category':category}
  assert all(marker not in result.model_dump_json() for marker in markers)
  results[component]=result.model_dump()
 print(json.dumps({'source_sha':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'database':name,'actual_postgresql_exception_paths':results,'normal_gmail_non_proven':True},indent=2))
finally:
 engine.dispose()
 with admin.connect() as conn:
  conn.execute(text(f'DROP DATABASE {name}'))
  remaining=conn.scalar(text('SELECT count(*) FROM pg_database WHERE datname=:name'),{'name':name})
  print('CLEANUP_DATABASE_COUNT='+str(remaining));assert remaining==0
 admin.dispose()
