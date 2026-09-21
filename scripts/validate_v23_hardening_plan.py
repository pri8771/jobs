#!/usr/bin/env python3
"""Validate/render the *plan*, never application correctness or live proof.

No network, scheduler, Git writes, credentials, or application execution.
Examples:
  python scripts/validate_v23_hardening_plan.py --check
  python scripts/validate_v23_hardening_plan.py --self-test
  python scripts/validate_v23_hardening_plan.py --task H-TOOL-01
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import sys
from typing import Any

VERSIONS = ['V1.4', 'V1.5', 'V1.6', 'V1.7', 'V2.0', 'V2.3', 'V3.0']


def validate(plan: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if plan.get('schema_version') != 1:
        errors.append('unsupported schema version')
    if plan.get('repository') != 'pri8771/jobs':
        errors.append('wrong repository')
    if plan.get('permission_grants') != []:
        errors.append('plan must not grant live permissions')
    defaults = plan.get('defaults', {})
    for field in ('one_active_implementation_session', 'one_heartbeat_owner', 'lead_acceptance_required'):
        if defaults.get(field) is not True:
            errors.append(f'{field} must be true')
    if defaults.get('heartbeat_minutes') != 5:
        errors.append('heartbeat must remain five minutes')
    for field in ('new_live_authorization_implied', 'engineering_evidence_is_live_proof'):
        if defaults.get(field) is not False:
            errors.append(f'{field} must be false')
    tasks = plan.get('tasks', [])
    if not isinstance(tasks, list) or not tasks:
        return errors + ['tasks must be a nonempty list']
    by_id: dict[str, dict[str, Any]] = {}
    inherited = plan.get('task_defaults', {})
    for raw in tasks:
        if not isinstance(raw, dict):
            errors.append('task must be an object')
            continue
        task = inherited | raw
        ident = task.get('id')
        if not isinstance(ident, str) or not ident:
            errors.append('task has no id')
            continue
        if ident in by_id:
            errors.append(f'duplicate id: {ident}')
        by_id[ident] = task
        for field in ('phase', 'artifact', 'objective', 'failure_behavior', 'worker_model_class', 'effort', 'activation'):
            if not isinstance(task.get(field), str) or not task[field].strip():
                errors.append(f'{ident}: missing {field}')
        for field in ('refines', 'code_surfaces', 'implementation_steps', 'proposed_test_cases', 'expected_output', 'non_goals'):
            value = task.get(field)
            if not isinstance(value, list) or not value or any(not isinstance(v, str) or not v.strip() for v in value):
                errors.append(f'{ident}: invalid {field}')
        if not isinstance(task.get('depends_on'), list):
            errors.append(f'{ident}: dependencies must be a list')
        if type(task.get('sp')) is not int or task['sp'] not in (1, 2):
            errors.append(f'{ident}: decompose task larger than SP2')
        if task.get('status') != 'PLANNED' or task.get('review_required') is not True:
            errors.append(f'{ident}: plan cannot self-accept task')
        if task.get('kind') not in ('ENGINEERING', 'DESIGN_CONTRACT'):
            errors.append(f'{ident}: unsupported task kind')
        if task.get('phase') == 'V3.0' and task.get('activation') != 'AFTER_V23_ACCEPTANCE_AND_V3_ASSIGNMENT':
            errors.append(f'{ident}: V3 must remain separately gated')
    for ident, task in by_id.items():
        for dep in task.get('depends_on', []):
            if dep not in by_id:
                errors.append(f'{ident}: missing dependency {dep}')
            elif task['phase'] != 'V3.0' and by_id[dep]['phase'] == 'V3.0':
                errors.append(f'{ident}: V3 cannot block V2.3 critical path')
    visiting: set[str] = set()
    done: set[str] = set()
    def visit(ident: str) -> None:
        if ident in visiting:
            errors.append(f'dependency cycle at {ident}')
            return
        if ident in done:
            return
        visiting.add(ident)
        for dep in by_id[ident].get('depends_on', []):
            if dep in by_id:
                visit(dep)
        visiting.remove(ident)
        done.add(ident)
    for ident in by_id:
        visit(ident)
    assigned: list[str] = []
    packet_ids: set[str] = set()
    for packet in plan.get('execution_packets', []):
        if packet.get('id') in packet_ids:
            errors.append('duplicate packet id')
        packet_ids.add(packet.get('id'))
        assigned.extend(packet.get('hardening_tasks', []))
    for ident in by_id:
        if assigned.count(ident) != 1:
            errors.append(f'{ident}: must appear in exactly one execution packet')
    for ident in assigned:
        if ident not in by_id:
            errors.append(f'unknown packet task: {ident}')
    gates = plan.get('release_gates', [])
    if [g.get('version') for g in gates] != VERSIONS:
        errors.append('required release gate sequence is incomplete')
    for i, gate in enumerate(gates):
        if not gate.get('engineering_artifacts') or not gate.get('live_artifact'):
            errors.append(f'{gate.get("version")}: engineering AND live evidence required')
        expected = [] if i == 0 else [VERSIONS[i-1]]
        if gate.get('required_previous') != expected:
            errors.append(f'{gate.get("version")}: prior live gate cannot be skipped')
    return errors


def self_test(plan: dict[str, Any]) -> int:
    cases = []
    def changed(name: str, fn: Any) -> None:
        clone = copy.deepcopy(plan)
        fn(clone)
        cases.append((name, clone))
    changed('duplicate id', lambda p: p['tasks'].append(copy.deepcopy(p['tasks'][0])))
    changed('missing dependency', lambda p: p['tasks'][0]['depends_on'].append('NO_SUCH_TASK'))
    changed('cycle', lambda p: p['tasks'][0]['depends_on'].append(p['tasks'][0]['id']))
    changed('oversize task', lambda p: p['tasks'][0].update(sp=3))
    changed('missing tests', lambda p: p['tasks'][0].update(proposed_test_cases=[]))
    changed('permission widening', lambda p: p.update(permission_grants=['ALL_EXTERNAL_ACTIONS']))
    changed('missing live gate', lambda p: p['release_gates'][1].update(live_artifact=None))
    changed('skip earlier milestone', lambda p: p['release_gates'][4].update(required_previous=[]))
    changed('V3 delays V2.3', lambda p: p['tasks'][0]['depends_on'].append('H-V3-01'))
    changed('self acceptance', lambda p: p['tasks'][0].update(status='ACCEPTED'))
    changed('heartbeat change', lambda p: p['defaults'].update(heartbeat_minutes=15))
    changed('unassigned task', lambda p: p['execution_packets'][0]['hardening_tasks'].pop())
    if validate(plan):
        raise ValueError('positive baseline failed')
    for name, clone in cases:
        if not validate(clone):
            raise AssertionError(f'negative case incorrectly passed: {name}')
    return len(cases)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, default=Path(__file__).resolve().parents[1] / 'coordination/V23_HARDENING_TASKS.json')
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--task')
    args = parser.parse_args()
    try:
        plan = json.loads(args.plan.read_text(encoding='utf-8'))
        errors = validate(plan)
        if errors:
            for error in errors:
                print(error, file=sys.stderr)
            return 2
        if args.task:
            matches = [t for t in plan['tasks'] if t['id'] == args.task]
            if not matches:
                raise ValueError(f'unknown task: {args.task}')
            task = plan['task_defaults'] | matches[0]
            print('PLANNED TASK ONLY. ChatGPT lead activates work; no live permission is granted.\n')
            print(json.dumps(task, indent=2, ensure_ascii=False))
        else:
            current = [t for t in plan['tasks'] if t['phase'] != 'V3.0']
            print(f'PLAN_STRUCTURE_PASS: {len(plan["tasks"])} tasks; {len(current)} through V2.3; {len(plan["tasks"])-len(current)} future V3 design tasks; {len(plan["release_gates"])} live gates')
            print('This does not validate implementation, provider access, tests or live proof.')
        if args.self_test:
            count = self_test(plan)
            print(f'PLAN_VALIDATOR_SELF_TEST_PASS: 1 positive + {count} negative cases')
        return 0
    except (OSError, ValueError, TypeError, KeyError, AssertionError) as exc:
        print(f'PLAN_VALIDATION_ERROR: {exc}', file=sys.stderr)
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
