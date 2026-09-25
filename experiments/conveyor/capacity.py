"""Paired fresh-worker stability sweep with an explicitly supplied SLO.

python -m experiments.conveyor.capacity --profile costs.json --slo slo.json \
    --concurrency 4,8,12 --seeds 11,22,33 --slots 4 --gpu 3

The output is a maximum *tested* stable concurrency and a failure bracket,
never an extrapolated infinite-lifetime capacity or a presumed monotone curve.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import tempfile
from pathlib import Path

from infra.run.artifacts import RunStore, make_run_id, sha256_file, utc_now
from infra.run.workflow import execute
from infra.trace.service import ServiceSLO
from .config import ConveyorConfig, workload
from .runner import plan


def summarize(points, concurrency, seeds):
    result = {}
    for system in sorted({p['system'] for p in points}):
        states = {}
        for n in concurrency:
            trials = [p for p in points if p['system'] == system and p['concurrency'] == n]
            states[n] = ('pass' if len(trials) == len(seeds) and all(p['verdict'] == 'pass' for p in trials)
                         else 'invalid' if len(trials) != len(seeds) or any(p['verdict'] == 'invalid' for p in trials)
                         else 'fail')
        best = max((n for n, state in states.items() if state == 'pass'), default=None)
        higher = min((n for n, state in states.items() if state == 'fail' and (best is None or n > best)), default=None)
        result[system] = dict(maximum_tested_stable=best, next_tested_failure=higher, states=states,
                              all_repeats_required=True, finite_horizon=True)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', required=True)
    parser.add_argument('--slo', required=True)
    parser.add_argument('--concurrency', required=True)
    parser.add_argument('--seeds', required=True)
    parser.add_argument('--slots', type=int, required=True)
    parser.add_argument('--model-preset', choices=('qwen25_omni', 'minicpm_o45'), default='qwen25_omni')
    parser.add_argument('--gpu-memory-utilization', type=float, default=.9)
    parser.add_argument('--max-model-len', type=int, default=32768)
    parser.add_argument('--max-num-batched-tokens', type=int)
    parser.add_argument('--enforce-eager', action='store_true')
    parser.add_argument('--resident-slots', type=int, default=1)
    parser.add_argument('--gpu', type=int, required=True)
    parser.add_argument('--restore-lead-s', type=float, default=.15)
    parser.add_argument('--retained-prefix-blocks', type=int, default=1)
    parser.add_argument('--kv-pool-gib', type=float)
    parser.add_argument('--host-offload-gib', type=float, default=24)
    args = parser.parse_args(argv)
    ns = sorted(set(map(int, args.concurrency.split(','))))
    seeds = list(map(int, args.seeds.split(',')))
    if not ns or min(ns) < 1 or not seeds or len(set(seeds)) != len(seeds):
        parser.error('positive concurrency and distinct trial seeds required')
    slo = ServiceSLO.read(args.slo)
    costs = json.loads(Path(args.profile).read_text())
    period = workload.PERIOD_MS / 1000
    if slo.warmup_s < 2 * period:
        parser.error('warmup must cover at least two periods')
    duration = slo.warmup_s + slo.horizon_s + 2 * period
    points = []
    root = ConveyorConfig.root
    aggregate = RunStore.create(root / 'results/conveyor/aggregates', make_run_id('capacity'),
        dict(started_at=utc_now(), kind='paired_capacity_sweep', argv=argv or sys.argv,
             slo=vars(slo), profile=costs, concurrency=ns, seeds=seeds,
             note='Individual runs own source provenance and validation.'))
    try:
        with tempfile.TemporaryDirectory(prefix='omni-capacity-') as temporary:
            temporary = Path(temporary)
            for n in ns:
                for trial, seed in enumerate(seeds):
                    cohort = temporary / 'cohort.json'
                    cohort.write_text(json.dumps([dict(id=f'session-{i}', arrival_s=0,
                        duration_s=duration, seed=seed * 1_000_003 + i) for i in range(n)]))
                    profile = temporary / 'profile.json'
                    profile.write_text(json.dumps({**costs, 'max_sessions': n}))
                    systems = ['resident', 'pilarius'] if trial % 2 == 0 else ['pilarius', 'resident']
                    for system in systems:
                        resident = system == 'resident'
                        config = ConveyorConfig(cohort_manifest=str(cohort),
                            model_preset=args.model_preset, gpu_memory_utilization=args.gpu_memory_utilization,
                            max_model_len=args.max_model_len, max_num_batched_tokens=args.max_num_batched_tokens,
                            enforce_eager=args.enforce_eager,
                            admission_profile=None if resident else str(profile),
                            capacity_slo=str(Path(args.slo).resolve()), resident_control=resident,
                            resident_limit=n, session_manager=not resident,
                            retained_prefix_blocks=None if resident else args.retained_prefix_blocks,
                            slots=args.resident_slots if resident else args.slots,
                            restore_lead_s=args.restore_lead_s, gpu=args.gpu,
                            kv_pool_gib=args.kv_pool_gib, host_offload_gib=args.host_offload_gib,
                            duration_s=math.ceil(duration + 120),
                            label=f'capacity-{system}-n{n}-seed{seed}')
                        _, path = execute(plan(config, make_run_id(config.label)), argv or sys.argv)
                        status = json.loads((path / 'status.json').read_text())
                        metric = json.loads((path / 'service_metrics.json').read_text()) if (path / 'service_metrics.json').is_file() else {}
                        verdict = metric.get('verdict', 'invalid')
                        # Infrastructure/measurement failures do not define a
                        # capacity boundary even if remaining inputs meet SLO.
                        issues = status.get('validation', {}).get('issues', [])
                        if verdict == 'pass' and status['state'] != 'success':
                            verdict = 'invalid'
                        worker_text = (path / 'worker.log').read_text(errors='replace') if (path / 'worker.log').exists() else ''
                        if any(marker in worker_text for marker in ('AssertionError', 'ModuleNotFoundError',
                                'input identity gap', 'Invocation of session_plan method failed')):
                            verdict = 'invalid'
                        points.append(dict(system=system, concurrency=n, seed=seed, verdict=verdict,
                            run=str(path.relative_to(root)), status_sha256=sha256_file(path / 'status.json'),
                            service_metrics_sha256=sha256_file(path / 'service_metrics.json') if metric else None,
                            issues=issues))
        aggregate.write_json('capacity.json', dict(points=points, summary=summarize(points, ns, seeds)))
        status = aggregate.finalize(required=('capacity.json',), exit_code=0,
            extra_issues=['some points have invalid measurements'] if any(p['verdict'] == 'invalid' for p in points) else [])
        print(aggregate.path, flush=True)
        return int(status['state'] != 'success')
    except BaseException:
        aggregate.write_json('capacity.json', dict(points=points, incomplete=True))
        aggregate.finalize(required=('capacity.json',), exit_code=1, extra_issues=['sweep interrupted before completion'])
        raise


if __name__ == '__main__':
    raise SystemExit(main())
