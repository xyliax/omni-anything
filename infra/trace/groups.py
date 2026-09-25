"""Audit planned group restoration budgets against physical transfer control.

Completion times are CPU publication observations, not pure DMA durations.
Unmatched H2D remains explicit; a missing match never becomes a zero cost.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import re


def identity(request):
    match = re.match(r'(s\d+e\d+)', request)
    return match[1] if match else request


def analyze(events):
    active, pending, jobs = {}, {}, {}
    windows = defaultdict(list)
    member_peaks = Counter()
    violations, unmatched = [], []
    reviews = Counter()
    maximum_active = releases = 0
    for row in events:
        event = row['event']
        if event == 'admitted':
            active[row['request']] = row['plan']['slot']
            maximum_active = max(maximum_active, len(active))
            for group, size in Counter(active.values()).items():
                member_peaks[group] = max(member_peaks[group], size)
        elif event == 'session_released':
            rid = identity(row['request'])
            if rid in active:
                del active[rid]
                releases += 1
        elif event == 'plan_review':
            reviews['feasible' if row['feasible'] else row.get('reason', 'infeasible')] += 1
        elif event == 'evicted':
            count = len(row['logical_blocks'])
            if row.get('ceiling_blocks') is not None and count > row['ceiling_blocks']:
                violations.append(dict(request=row['request'], time=row['time'], blocks=count,
                                       ceiling=row['ceiling_blocks']))
            pending[identity(row['request'])] = row
        elif event == 'queued' and row['direction'] == 'H2D':
            prior = pending.get(identity(row['requests'][0])) if len(row['requests']) == 1 else None
            if prior is not None and len(prior['logical_blocks']) == row['blocks']:
                jobs[row['transfer_id']] = dict(eviction=prior, queued=row)
                del pending[identity(row['requests'][0])]
            else:
                unmatched.append(row['transfer_id'])
        if row.get('transfer_id') in jobs:
            jobs[row['transfer_id']][event] = row
    incomplete = []
    for transfer, job in jobs.items():
        if 'published' not in job:
            incomplete.append(transfer)
            continue
        evicted = job['eviction']
        windows[(evicted['group'], round(evicted['restore_end_epoch'], 3))].append(job)
    details = []
    for (group, deadline), members in sorted(windows.items(), key=lambda x: x[0][1]):
        start = min(j['eviction']['restore_start_epoch'] for j in members)
        queued = min(j['queued']['time'] for j in members)
        complete = max(j['published']['time'] for j in members)
        details.append(dict(group=group, deadline_epoch=deadline, members=len(members),
            blocks=sum(j['queued']['blocks'] for j in members),
            all_members_at_ceiling=all(j['queued']['blocks'] == j['eviction']['ceiling_blocks'] for j in members),
            window_ms=(deadline-start)*1000, publication_lateness_ms=(complete-deadline)*1000,
            queued_to_published_ms=(complete-queued)*1000,
            launch_lateness_ms=(queued-start)*1000,
            transfer_ids=[j['queued']['transfer_id'] for j in members]))
    return dict(schema_version=1, timing_scope='CPU queue and valid-KV publication; not DMA',
        maximum_active_sessions=maximum_active, maximum_group_members=dict(member_peaks),
        released_sessions=releases, planner_reviews=dict(reviews), cap_violations=violations,
        unmatched_h2d=unmatched, unpublished_h2d=incomplete, windows=details,
        late_windows=sum(w['publication_lateness_ms']>0 for w in details))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    args = parser.parse_args()
    report = analyze(json.loads(line) for line in (args.run/'transfer_events.jsonl').read_text().splitlines())
    target = args.run/'derived/group_windows.json'
    target.parent.mkdir(exist_ok=True)
    with target.open('x') as f:
        json.dump(report, f, indent=2)
    print(target)


if __name__ == '__main__':
    main()
