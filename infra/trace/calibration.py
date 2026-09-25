"""Extract conservative cost samples; calibration is separate from evaluation."""
from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

from infra.run.artifacts import RunStore, make_run_id, sha256_file
from .replay import distribution


def read(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []


def measure(paths, *, ceiling_blocks, compute_margin=1.25, transfer_margin=1.25):
    if ceiling_blocks < 1 or compute_margin < 1 or transfer_margin < 1:
        raise ValueError('positive ceiling and conservative margins >= 1 required')
    groups, h2d_rates, backup, sources = defaultdict(list), [], [], []
    domain = None
    for path in map(Path, paths):
        status = json.loads((path/'status.json').read_text())
        if status['state'] != 'success' or not status['validation']['valid']:
            raise ValueError('calibration requires valid measurements')
        for name, info in status['artifacts'].items():
            if sha256_file(path/name) != info['sha256']:
                raise ValueError('calibration artifact changed')
        cfg = json.loads((path/'manifest.json').read_text())['config']
        if cfg['observations'].get('verify_copies') or cfg['observations'].get('gpu_trace'):
            raise ValueError('intrusive diagnostics cannot calibrate performance costs')
        current_domain = (cfg['model']['id'], cfg['model']['revision'], cfg['engine']['max_model_len'],
                          cfg['engine']['kv_pool_gib'], cfg['workload']['output_token_cap'])
        if domain is not None and current_domain != domain:
            raise ValueError('calibration cannot mix model/workload/resource domains')
        domain = current_domain
        client = json.loads((path/'client.json').read_text())
        cutoff = client['start_ns'] + round(cfg['admission']['cohort']['configuration'].get('measurement_start_s',0)*1e9)
        worker = read(path/'service_events.jsonl')
        inputs = {(r['session'],r['frame']):r for r in worker if r['event']=='engine_input'}
        done = {(r['session'],r['frame']):r for r in worker if r['event']=='compute_complete'}
        releases = defaultdict(list)
        for row in read(path/'gateway_frames.jsonl'):
            if row['event']=='input_release' and row['release_ns'] >= cutoff:
                releases[row['release_ns']].append((row['session'],row['frame']))
        for tick, keys in releases.items():
            if all(key in inputs and key in done for key in keys):
                elapsed = (max(done[key]['time_ns'] for key in keys) - min(inputs[key]['time_ns'] for key in keys))/1e9
                groups[len(keys)].append(elapsed)
        transfers = read(path/'transfer_events.jsonl')
        queued = {r['transfer_id']:r for r in transfers if r['event']=='queued'}
        for row in transfers:
            if row['event']!='published' or row['time']*1e9 < cutoff:
                continue
            q = queued[row['transfer_id']]
            elapsed = row['time']-q['time']
            if elapsed <= 0:
                raise ValueError('nonpositive copy service time')
            if row['direction']=='H2D' and q['blocks'] >= ceiling_blocks:
                h2d_rates.append(q['blocks']/elapsed)
            elif row['direction']=='D2H':
                backup.append(elapsed)
        sources.append(dict(path=str(path), status_sha256=sha256_file(path/'status.json')))
    if not groups or not h2d_rates or not backup:
        raise ValueError('calibration needs actual grouped computation, ceiling-size restores and incremental backups')
    costs = {}
    monotone = 0
    for count in sorted(groups):
        monotone = max(monotone, math.ceil(max(groups[count])*compute_margin*1000)/1000)
        costs[str(count)] = monotone
    return dict(schema_version=1, sources=sources,
        interpretation='CPU-observed service costs including queueing/interference; not pure DMA or a hard guarantee',
        compute_margin=compute_margin, transfer_margin=transfer_margin,
        compute_by_group=costs, compute_samples_s={str(k):distribution(v) for k,v in groups.items()},
        h2d_blocks_per_s=math.floor(min(h2d_rates)/transfer_margin), h2d_rate_samples=distribution(h2d_rates),
        backup_s=math.ceil(max(backup)*transfer_margin*1000)/1000,
        backup_samples_s=distribution(backup))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('runs', nargs='+')
    parser.add_argument('--ceiling-blocks', required=True, type=int)
    parser.add_argument('--output-root', required=True)
    args = parser.parse_args()
    result = measure(args.runs, ceiling_blocks=args.ceiling_blocks)
    store = RunStore.create(Path(args.output_root), make_run_id('cost-calibration'),
        dict(schema_version=1, kind='cost_calibration', sources=result['sources'],
             ceiling_blocks=args.ceiling_blocks, evidence_role='diagnostic'))
    store.write_json('costs.json', result)
    store.finalize(required=['costs.json'], exit_code=0)
    print(store.path)


if __name__ == '__main__':
    main()
