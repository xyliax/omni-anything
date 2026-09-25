"""Prepare and execute the three paired evaluation experiments.

Preparation freezes schedules, costs and point order in a new directory.
Execution uses the shared fresh-worker runner and an append-only checkpoint.
Formal execution requires clean source at one unchanged commit for every point.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import subprocess
import sys
from pathlib import Path

from infra.run.artifacts import sha256_file
from .config import ConveyorConfig
from experiments.shared.workload import PERIOD_MS
from .schedule import audio_asset, generate_fixed_schedule, generate_schedule


def write_new(path, data):
    with Path(path).open('x') as stream:
        json.dump(data, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')


def prepare(spec_path, output):
    spec_path, output = Path(spec_path).resolve(), Path(output).resolve()
    spec = json.loads(spec_path.read_text())
    if spec.get('schema_version') != 1 or spec.get('evidence_role') not in ('diagnostic', 'formal'):
        raise ValueError('version 1 and explicit evidence_role required')
    output.mkdir(parents=True, exist_ok=False)
    resolve = lambda path: (spec_path.parent / path).resolve()
    assets = [audio_asset(resolve(path)) for path in spec['audio']]
    points, frozen = [], []
    for model in spec['models']:
        if spec['evidence_role'] == 'formal' and model['common'].get('verify_copies'):
            raise ValueError('intrusive physical copy checks cannot measure formal performance')
        preset = model['common']['model_preset']
        costs = {}
        for name in ('pilarius', 'on_demand'):
            value = json.loads(resolve(model[name + '_profile']).read_text())
            required_mode = 'maximum_context' if name == 'pilarius' else 'static_limit'
            if value.get('planning_mode') != required_mode:
                raise ValueError(f'{name} requires {required_mode} profile')
            target = output / f'{preset}-{name}-costs.json'
            write_new(target, value)
            costs[name] = str(target)
            frozen.append(target)
        # Trigger and natural-phase controls hold eviction/copy costs fixed.
        planned = json.loads(Path(costs['pilarius']).read_text())
        demand = json.loads(Path(costs['on_demand']).read_text())
        if planned['max_evict_blocks'] != demand['max_evict_blocks']:
            raise ValueError('matched systems need the same eviction ceiling')
        variant = output / f'{preset}-ablation-costs.json'
        write_new(variant, dict(planned, planning_mode='static_limit', max_sessions=demand['max_sessions']))
        frozen.append(variant)

        def add(experiment, axis, seed, schedule, systems):
            target = output / f'{preset}-{experiment}-{axis}-{seed}.json'
            write_new(target, schedule)
            frozen.append(target)
            last = max(row['start_time_s'] + row['duration_s'] for row in schedule['sessions'])
            order = list(systems)
            random.Random(f'{seed}:{experiment}:{axis}').shuffle(order)
            for system in order:
                common = dict(model['common'], cohort_manifest=str(target), open_loop=True,
                              sync_scheduling=True, duration_s=math.ceil(last + model.get('drain_s', 30)))
                resident = system == 'resident'
                controls = dict(resident_control=resident, phase_policy='natural' if resident or system == 'natural_pre_tick' else 'assigned')
                if resident:
                    controls['resident_limit'] = model['resident_limit']
                else:
                    controls.update(session_manager=True, retained_prefix_blocks=1,
                        restore_policy={'on_demand': 'on_demand', 'after_submit': 'after_submit'}.get(system, 'pre_tick'),
                        admission_profile=costs.get(system, str(variant)))
                config = dict(common, **controls, label=f'{experiment}-{preset}-{system}-{axis}-s{seed}')
                ConveyorConfig(**config)  # validate every point before launching any worker
                points.append(dict(point_id=f'{preset}/{experiment}/{axis}/{seed}/{system}',
                    experiment=experiment, axis=axis, seed=seed, system=system, config=config))

        capacity = model.get('capacity')
        if capacity:
            for n in capacity['concurrency']:
                for seed in capacity['seeds']:
                    schedule = generate_fixed_schedule(seed=seed, sessions=n, duration_s=capacity['session_duration_s'],
                        period_s=PERIOD_MS/1000, assets=assets, measurement_start_s=capacity['measurement_start_s'])
                    systems = ['resident', 'on_demand', 'pilarius']
                    if n in model.get('ablation_concurrency', []):
                        if n > min(model['resident_limit'], demand['max_sessions'], planned['max_sessions']):
                            # Resident may reject; only the offload pairs need
                            # identical admitted work for mechanism ablation.
                            if n > min(demand['max_sessions'], planned['max_sessions']):
                                raise ValueError('ablation must fit both offload admission limits')
                        systems += ['natural_pre_tick', 'after_submit']
                    add('capacity', n, seed, schedule, systems)
        dynamic = model.get('dynamic')
        if dynamic:
            for rate in dynamic['arrival_rates']:
                for seed in dynamic['seeds']:
                    schedule = generate_schedule(seed=seed, arrival_rate=rate,
                        duration_s=dynamic['session_duration_s'], arrival_window_s=dynamic['arrival_window_s'], period_s=PERIOD_MS/1000, assets=assets)
                    add('dynamic', rate, seed, schedule, ['resident', 'pilarius'])
    plan = dict(schema_version=1, evidence_role=spec['evidence_role'], spec=spec,
        spec_sha256=sha256_file(spec_path), files={str(p): sha256_file(p) for p in frozen}, points=points)
    write_new(output / 'plan.json', plan)
    return output / 'plan.json'


def execute_plan(path):
    from .runner import run
    path = Path(path).resolve()
    plan = json.loads(path.read_text())
    for name, digest in plan['files'].items():
        if sha256_file(Path(name)) != digest:
            raise ValueError('frozen experiment input changed: ' + name)
    journal = path.parent / 'execution.jsonl'
    previous = [json.loads(line) for line in journal.read_text().splitlines()] if journal.exists() else []
    completed = {row['point_id'] for row in previous}
    source = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ConveyorConfig.root, text=True).strip()
    if previous and any(row['source_commit'] != source for row in previous):
        raise ValueError('resume cannot change the experiment source commit')
    for index, point in enumerate(plan['points']):
        if point['point_id'] in completed:
            continue  # a failed point is still a result, never silently retried
        if plan['evidence_role'] == 'formal':
            dirty = subprocess.check_output(['git', 'status', '--porcelain'], cwd=ConveyorConfig.root, text=True)
            if dirty:
                raise ValueError('formal execution requires clean source')
        print(json.dumps(dict(point=index+1, total=len(plan['points']), point_id=point['point_id'])), flush=True)
        code, result = run([sys.executable, '-m', 'experiments.conveyor.evaluate', 'run', str(path), point['point_id']], **point['config'])
        row = dict(point_id=point['point_id'], run_path=str(result.resolve()), exit_code=code, source_commit=source,
                   status_sha256=sha256_file(result/'status.json'))
        with journal.open('a') as stream:
            stream.write(json.dumps(row)+'\n')
        if code:
            raise RuntimeError('run validation failed; inspect before continuing the prepared matrix')
    return journal


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    create = commands.add_parser('prepare')
    create.add_argument('--spec', required=True)
    create.add_argument('--output', required=True)
    execute = commands.add_parser('run')
    execute.add_argument('plan')
    args = parser.parse_args()
    result = prepare(args.spec, args.output) if args.command == 'prepare' else execute_plan(args.plan)
    print(result)


if __name__ == '__main__':
    main()
