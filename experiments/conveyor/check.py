"""Check a new machine with real two-member session groups.

This is functional validation, not a calibrated capacity experiment. Successful
temporary runs are removed after a compact report is saved outside results/.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

from experiments.shared import model, platform
from infra.env.verify import collect_device, collect_software, runtime_issues
from infra.run.artifacts import make_run_id, sha256_file
from infra.run.probes import collect_git, model_snapshot_issues, resolve_model_snapshot
from infra.run.workflow import execute
from infra.trace.groups import analyze
from .config import ConveyorConfig
from .runner import plan


def check_config(preset, gpu, cohort, profile, gpu_trace=False):
    return ConveyorConfig(model_preset=preset, session_manager=True, retained_prefix_blocks=1,
        slots=1, restore_lead_s=.25, admission_profile=str(profile), cohort_manifest=str(cohort),
        gpu=gpu, kv_pool_gib=1, host_offload_gib=1, gpu_trace=gpu_trace, trace=True,
        duration_s=90, label=f'machine-check-{preset}', gpu_memory_utilization=.75,
        max_model_len=4096, max_num_seqs=4, enforce_eager=True, max_num_batched_tokens=512)


def audit_run(path, config):
    status = json.loads((path / 'status.json').read_text())
    issues = list(status.get('validation', {}).get('issues', []))
    if status.get('state') != 'success' or not status.get('validation', {}).get('valid'):
        issues.append('run did not reach validated success')
    if issues:
        return {'valid': False, 'issues': issues}
    events = [json.loads(line) for line in (path / 'service_events.jsonl').read_text().splitlines()]
    completed = [event for event in events if event['event'] == 'compute_complete']
    tokens = Counter(event['tokens'] for event in completed)
    if len(completed) != 14 or set(tokens) != {config.output_token_cap}:
        issues.append(f'expected fourteen inputs with the selected output budget, found {dict(tokens)}')
    groups = analyze(json.loads(line) for line in (path / 'transfer_events.jsonl').read_text().splitlines())
    if (groups['maximum_group_members'].get(0) != 2 or groups['released_sessions'] != 2
            or not groups['windows'] or groups['cap_violations']
            or groups['unmatched_h2d'] or groups['unpublished_h2d']):
        issues.append('two-member group, bounded restoration and release checks failed')
    client = json.loads((path / 'client.json').read_text())
    if client['completed'] != 2 or client['err']:
        issues.append('cohort failed to complete and drain both sessions')
    return dict(valid=not issues, issues=issues, model=config.model_preset,
        output_token_cap=config.output_token_cap, completed_inputs=len(completed),
        generated_token_counts=dict(tokens), client=client,
        groups={key: value for key, value in groups.items() if key != 'windows'},
        restoration_windows=len(groups['windows']),
        timing_note='Restoration timing uses deliberately uncalibrated diagnostic costs; not a capacity SLO.',
        manifest_sha256=sha256_file(path / 'manifest.json'), status_sha256=sha256_file(path / 'status.json'))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gpu', type=int, default=platform.DEFAULT_GPU_INDEX)
    parser.add_argument('--model-preset', choices=(*model.PRESETS, 'all'), default='all')
    parser.add_argument('--gpu-trace', action='store_true', help='capture each entire business run')
    parser.add_argument('--keep-results', action='store_true', help='retain successful raw checks for review')
    args = parser.parse_args(argv)
    root = ConveyorConfig.root
    python = platform.worker_python(root)
    selected = list(model.PRESETS) if args.model_preset == 'all' else [args.model_preset]
    report = dict(kind='machine_functional_check', formal_evidence=False,
                  source=collect_git(root), models=selected, runs=[], issues=[])
    target = root / '.build' / 'checks' / f'{time.time_ns()}.json'
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        report['software'] = collect_software(python)
        report['issues'].extend(runtime_issues(report['software']))
        report['gpu'] = collect_device(python, args.gpu)
        report['issues'].extend(report['gpu']['issues'])
        for binary in ('metronome-gateway', 'conveyor-gateway'):
            if not os.access(root / '.build' / binary, os.X_OK):
                report['issues'].append(f'missing gateway {binary}; rerun infra/env/setup.sh')
        for preset in selected:
            spec = model.PRESETS[preset]
            try:
                report['issues'].extend(model_snapshot_issues(resolve_model_snapshot(spec['id'], spec['revision'])))
            except RuntimeError as exc:
                report['issues'].append(str(exc))
        if not report['issues']:
            # Verify the exact descriptor/event backend on this architecture,
            # not just torch.copy_ or a CUDA version string.
            env = {**os.environ, 'CUDA_VISIBLE_DEVICES': report['gpu']['uuid'], 'OMNI_TEST_CUDA': '1'}
            physical = subprocess.run([str(python), '-m', 'unittest',
                'tests.test_session_manager_gpu', '-v'], cwd=root, env=env,
                text=True, capture_output=True, timeout=120)
            report['physical_kv_roundtrip'] = dict(returncode=physical.returncode,
                                                  log=physical.stdout + physical.stderr)
            if physical.returncode:
                report['issues'].append('physical KV roundtrip failed; see report')
        if not report['issues']:
            with tempfile.TemporaryDirectory(prefix='omni-machine-check-') as temporary:
                temporary = Path(temporary)
                cohort, costs = temporary / 'cohort.json', temporary / 'costs.json'
                cohort.write_text(json.dumps([dict(id=f'check-{i}', arrival_s=0, duration_s=14,
                                                   seed=4500+i) for i in range(2)]))
                costs.write_text(json.dumps(dict(compute_s=.6, h2d_blocks_per_s=2000,
                    d2h_blocks_per_s=2000, gpu_reserve_blocks=16, growth_blocks_per_period=6,
                    horizon_s=6, host_reserve_blocks=16, initial_blocks=16, max_evict_blocks=8,
                    max_sessions=2, safety_s=.01, transfer_overhead_s=.003)))
                for preset in selected:
                    config = check_config(preset, args.gpu, cohort, costs, args.gpu_trace)
                    code, path = execute(plan(config, make_run_id(config.label)), argv or sys.argv)
                    result = audit_run(path, config)
                    result['result_directory'] = str(path.relative_to(root))
                    if code or not result['valid']:
                        report['issues'].append(f'{preset} serving check failed; retained {path}')
                    elif not args.keep_results:
                        shutil.rmtree(path)
                        result['raw_removed'] = True
                    report['runs'].append(result)
                    if report['issues']:
                        break
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        report['issues'].append(str(exc))
    finally:
        report['valid'] = not report['issues'] and len(report['runs']) == len(selected)
        target.write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(dict(valid=report['valid'], report=str(target), issues=report['issues']), indent=2))
    return 0 if report['valid'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
