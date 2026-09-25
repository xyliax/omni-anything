"""Hash-verified aggregation and export for the prepared evaluation matrix."""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

from infra.run.artifacts import RunStore, make_run_id, sha256_file, utc_now

MODEL_LABELS = {'minicpm_o45':'MiniCPM-o 4.5', 'qwen25_omni':'Qwen2.5-Omni 7B'}
SYSTEM_LABELS = {'resident':'Fully resident', 'on_demand':'On-demand', 'pilarius':'Pilarius',
                 'natural_pre_tick':'Natural phase', 'after_submit':'After submission'}

def events(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []


def load_point(point, entry, *, formal=False):
    path = Path(entry['run_path'])
    if sha256_file(path/'status.json') != entry['status_sha256']:
        raise ValueError('terminal status changed: ' + str(path))
    status = json.loads((path/'status.json').read_text())
    for name, artifact in status['artifacts'].items():
        if sha256_file(path/name) != artifact['sha256']:
            raise ValueError('retained artifact changed: ' + str(path/name))
    manifest = json.loads((path/'manifest.json').read_text())
    if formal and manifest['git']['dirty']:
        raise ValueError('dirty run cannot supply formal evidence')
    if formal and entry.get('source_commit') and manifest['git'].get('commit') != entry['source_commit']:
        raise ValueError('run source differs from execution checkpoint')
    if formal and manifest['config']['observations'].get('verify_copies'):
        raise ValueError('intrusive copy checking cannot supply performance evidence')
    metrics = json.loads((path/'replay_metrics.json').read_text())
    config = manifest['config']
    if 'config' in point:
        requested = point['config']
        if requested['model_preset'] != config['model']['preset']:
            raise ValueError('run model differs from prepared point')
        for key,value in requested.items():
            if key in config['engine'] and config['engine'][key] != value:
                raise ValueError('run configuration differs from prepared point: ' + key)
        schedule = json.loads(Path(requested['cohort_manifest']).read_text())
        if schedule != config['admission']['cohort']:
            raise ValueError('run used a different input schedule')
        if requested.get('admission_profile'):
            costs=json.loads(Path(requested['admission_profile']).read_text())
            if costs != config['admission']['profile']:
                raise ValueError('run used different admission costs')
    client = json.loads((path/'client.json').read_text())
    source_ids = {row['sid']: row['id'] for row in client['sessions'] if 'sid' in row}
    output = {(source_ids[row['session']], row['frame']): row['output_token_sha256']
              for row in events(path/'service_events.jsonl') if row['event']=='compute_complete'
              and row['frame'] > 0 and row.get('output_token_sha256') and row['session'] in source_ids}
    transfers = events(path/'transfer_events.jsonl')
    warmup = config['admission']['cohort']['configuration'].get('measurement_start_s', 0)
    start = client['start_ns']/1e9 + warmup
    last = max((frame['deadline_ns'] for frame in metrics.get('frames', [])), default=client['start_ns'])/1e9
    copies = [row for row in transfers if row['event']=='submitted' and start <= row['time'] <= last]
    scalar = dict(model=config['model']['preset'], experiment=point['experiment'], axis=point['axis'],
        seed=point['seed'], system=point['system'], valid=status['state']=='success' and status['validation']['valid'] and not metrics['invalid_reasons'],
        run_path=str(path), offered_sessions=metrics['offered_sessions'], admitted_sessions=metrics['admitted_sessions'],
        rejected_sessions=metrics['rejected_sessions'], completed_sessions=metrics['completed_sessions'],
        offered_frames=metrics['offered_frames'], admitted_frames=metrics['admitted_frames'],
        on_time=metrics['on_time'], late=metrics['late'], unfinished=metrics['unfinished'],
        on_time_offered_fraction=metrics['on_time_offered_fraction'], on_time_admitted_fraction=metrics['on_time_admitted_fraction'],
        completion_p95_ms=metrics['completion_from_release_ms']['p95'],
        source_ready_p95_ms=metrics['completion_from_source_ready_ms']['p95'],
        history_wait_p95_ms=metrics['preprocessing_to_engine_enqueue_ms']['p95'],
        peak_allocated_gpu_blocks=metrics['peak_allocated_gpu_blocks'], gpu_pool_blocks=metrics['gpu_pool_blocks'],
        peak_allocated_gpu_gib=(metrics['peak_allocated_gpu_blocks'] * metrics['bytes_per_gpu_block'] / 2**30
                               if metrics.get('bytes_per_gpu_block') else None),
        peak_valid_host_backing_gib=(metrics['peak_valid_host_backing_blocks'] * metrics['bytes_per_gpu_block'] / 2**30
                                    if metrics.get('bytes_per_gpu_block') else None),
        maximum_context_tokens=config['engine']['max_model_len'], actual_context_max=metrics['observed_context_tokens']['maximum'],
        actual_context_min=min((row['context_tokens'] for row in events(path/'service_events.jsonl')
                              if row['event']=='compute_complete' and row['time_ns'] >= round(start*1e9)), default=None),
        kv_pool_gib=config['engine']['kv_pool_gib'], host_pool_gib=config['engine']['host_offload_gib'] if not config['engine']['resident_control'] else 0,
        h2d_bytes=sum(row['bytes'] for row in copies if row['direction']=='H2D'),
        d2h_bytes=sum(row['bytes'] for row in copies if row['direction']=='D2H'))
    end_source = client['start_ns'] + round(max(s['start_time_s']+s['duration_s']
        for s in config['admission']['cohort']['sessions'])*1e9)
    ended = [s['completed_ns'] for s in client['sessions'] if s.get('completed')]
    scalar['drain_after_source_end_s'] = max(0, (max(ended)-end_source)/1e9) if ended and len(ended)==metrics['admitted_sessions'] else None
    return scalar, output


def timeline(path):
    """Physical allocation and active lifetimes on the original source clock."""
    client = json.loads((path/'client.json').read_text())
    metrics = json.loads((path/'replay_metrics.json').read_text())
    origin = client['start_ns']
    worker = events(path/'service_events.jsonl')
    end = max((r['time_ns'] for r in worker), default=origin)
    active, backlog = [], []
    for row in client['sessions']:
        if row.get('admitted'):
            active.append((row['admitted_ns'],1))
            if row.get('completed'):
                active.append((row['completed_ns'],-1))
    for row in metrics['frames']:
        backlog.append((row['source_ready_ns'],1))
        if row['complete_ns'] is not None:
            backlog.append((row['complete_ns'],-1))
    def accumulated(changes):
        value, result = 0, [[0,0]]
        for when, delta in sorted(changes):
            value += delta
            result.append([(when-origin)/1e9,value])
        return result
    allocations = [[(r['time_ns']-origin)/1e9,r['allocated_blocks']]
                   for r in worker if r['event']=='gpu_allocation']
    return dict(active=accumulated(active), pending_inputs=accumulated(backlog), allocated_blocks=allocations,
                bytes_per_block=metrics['bytes_per_gpu_block'])


def aggregate(plan_path, output_root):
    plan_path = Path(plan_path)
    plan = json.loads(plan_path.read_text())
    for name,digest in plan.get('files',{}).items():
        if sha256_file(Path(name)) != digest:
            raise ValueError('frozen experiment input changed: ' + name)
    journal = plan_path.parent/'execution.jsonl'
    entries = {row['point_id']: row for row in events(journal)}
    if len(entries) != len(plan['points']):
        raise ValueError('matrix is incomplete; do not silently summarize only finished points')
    rows, outputs, sources, timelines, admissions = [], {}, [], {}, {}
    for point in plan['points']:
        entry = entries[point['point_id']]
        scalar, tokens = load_point(point, entry, formal=plan['evidence_role']=='formal')
        rows.append(scalar)
        outputs[point['point_id']] = tokens
        sources.append(dict(entry, manifest_sha256=sha256_file(Path(entry['run_path'])/'manifest.json')))
        client = json.loads((Path(entry['run_path'])/'client.json').read_text())
        admissions[point['point_id']] = {row['id'] for row in client['sessions'] if row.get('admitted')}
        if point['experiment']=='dynamic':
            timelines[point['point_id']] = timeline(Path(entry['run_path']))
    for point in plan['points']:
        if point['system'] in ('natural_pre_tick','after_submit'):
            prefix = '/'.join(point['point_id'].split('/')[:-1])
            reference = admissions[prefix+'/pilarius']
            if admissions[point['point_id']] != reference or admissions[prefix+'/on_demand'] != reference:
                raise ValueError('ablation admitted different sessions: ' + point['point_id'])
    groups = defaultdict(list)
    for row in rows:
        groups[(row['model'], row['experiment'], row['axis'], row['system'])].append(row)
    grouped = []
    for (model, experiment, axis, system), trials in groups.items():
        summary = dict(model=model, experiment=experiment, axis=axis, system=system, repeats=len(trials),
                       all_measurements_valid=all(row['valid'] for row in trials))
        for key in ('admitted_sessions','on_time','late','unfinished','on_time_offered_fraction',
                    'completion_p95_ms','source_ready_p95_ms','history_wait_p95_ms','peak_allocated_gpu_blocks'):
            values = [row[key] for row in trials if row[key] is not None]
            summary[key] = dict(mean=sum(values)/len(values) if values else None,
                                minimum=min(values) if values else None, maximum=max(values) if values else None)
        grouped.append(summary)
    paired = []
    for point in plan['points']:
        if point['system']=='resident':
            continue
        reference = '/'.join(point['point_id'].split('/')[:-1]+['resident'])
        if reference not in outputs:
            continue
        common = outputs[point['point_id']].keys() & outputs[reference].keys()
        mismatches = [list(key) for key in sorted(common) if outputs[reference][key] != outputs[point['point_id']][key]]
        paired.append(dict(point_id=point['point_id'], reference=reference, compared_inputs=len(common),
                           differing_output_hashes=mismatches,
                           interpretation='Diagnostic exact-token comparison, not a KV-correctness acceptance gate. KV contents, logical placement and readiness are checked separately.'))
    store = RunStore.create(Path(output_root), make_run_id('evaluation'),
        dict(schema_version=1, started_at=utc_now(), kind='paired_open_loop_evaluation', evidence_role=plan['evidence_role'],
             plan_sha256=sha256_file(plan_path), journal_sha256=sha256_file(journal), sources=sources,
             analysis_source_sha256={__file__:sha256_file(Path(__file__))},
             scope='Actual configured audio-input/fixed-text-output path and KV budget; no native speech-output or full-device capacity inference.'))
    store.write_json('summary.json', dict(points=rows, groups=grouped, paired_output_tokens=paired))
    with store.file('points.csv').open('x') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    store.write_json('plan.json', plan)
    store.write_json('dynamic_timelines.json', timelines)
    store.file('README.md').write_text(
        'Paired evaluation exports\n\n'
        'Dots/bars show means across the configured independent seeds; error bars show the full run-to-run range, not confidence intervals. '
        'Periodic inputs from the same run are not independent repeats.\n\n'
        'Completion is observed at the inference engine for the declared fixed text budget. Source latency includes initial phase alignment; it is not audio playback or client delivery latency. '
        'Preprocessing-to-enqueue time includes KV readiness and control handoff, not pure DMA.\n\n'
        'Read points.csv and summary.json together with the figures: rejection, late and unfinished work remain visible. '
        'Host backing includes reclaimable cached content. All dynamic seeds have individual trajectory PDFs.\n\n'
        'Exact configurations and evidence scope are in plan.json and manifest.json. A controlled KV pool and the actually observed context lengths do not establish full-device or longer-context capacity. '
        'Output hashes are auxiliary diagnostics; KV correctness is checked separately.\n', encoding='utf-8')
    plot(rows, store.path)
    plot_additional(rows, timelines, store.path)
    status = store.finalize(required=['summary.json','points.csv','plan.json','capacity.pdf'], exit_code=0,
                          extra_issues=[] if all(row['valid'] for row in rows) else ['one or more invalid measurements'])
    return store.path, status


def plot_additional(rows, timelines, output):
    import matplotlib.pyplot as plt
    colors = dict(resident='#444444', on_demand='#d47716', pilarius='#1765ab', natural_pre_tick='#6e4796', after_submit='#26966f')
    for experiment, systems, keys, labels, filename in (
        ('dynamic', ('resident','pilarius'), ('on_time_offered_fraction','admitted_sessions','source_ready_p95_ms'),
         ('On-time fraction of offered inputs','Admitted sessions','Completion p95 from source (ms)'), 'dynamic'),
        ('capacity', ('on_demand','after_submit','pilarius','natural_pre_tick'), ('history_wait_p95_ms','completion_p95_ms','source_ready_p95_ms'),
         ('Preprocessing to enqueue p95 (ms)','Completion p95 from tick (ms)','Completion p95 from source (ms)'), 'ablation')):
        trials = [r for r in rows if r['experiment']==experiment]
        if filename=='ablation':
            points={(r['model'],r['axis']) for r in trials if r['system']=='after_submit'}
            trials=[r for r in trials if (r['model'],r['axis']) in points]
        models=sorted({r['model'] for r in trials})
        if not models:
            continue
        if filename=='ablation':
            pairs=sorted({(r['model'],r['axis']) for r in trials})
            fig,axes=plt.subplots(len(pairs),3,figsize=(11,3.3*len(pairs)),squeeze=False)
            for index,(model,concurrency) in enumerate(pairs):
                for axis,key,label in zip(axes[index],keys,labels):
                    means,lower,upper=[],[],[]
                    for system in systems:
                        values=[r[key] for r in trials if r['model']==model and r['axis']==concurrency
                                and r['system']==system and r[key] is not None]
                        mean=sum(values)/len(values) if values else float('nan')
                        means.append(mean);lower.append(mean-min(values) if values else 0);upper.append(max(values)-mean if values else 0)
                    axis.bar(range(len(systems)),means,yerr=[lower,upper],capsize=3,color=[colors[s] for s in systems])
                    axis.set_xticks(range(len(systems)),[SYSTEM_LABELS[s] for s in systems],rotation=22,ha='right',fontsize=8)
                    axis.set(ylabel=label,title=f'{MODEL_LABELS.get(model,model)}, N={concurrency}')
                    axis.grid(axis='y',alpha=.2)
            fig.tight_layout();fig.savefig(output/'ablation.pdf',bbox_inches='tight');fig.savefig(output/'ablation.png',dpi=180,bbox_inches='tight');plt.close(fig)
            continue
        fig, axes=plt.subplots(len(models),3,figsize=(11,3*len(models)),squeeze=False)
        for index, model in enumerate(models):
            for system in systems:
                selected=[r for r in trials if r['model']==model and r['system']==system]
                for axis,key,label in zip(axes[index],keys,labels):
                    groups=defaultdict(list)
                    for row in selected:
                        if row[key] is not None:
                            groups[row['axis']].append(row[key])
                    xs=sorted(groups); means=[sum(groups[x])/len(groups[x]) for x in xs]
                    errors=[[v-min(groups[x]) for x,v in zip(xs,means)],[max(groups[x])-v for x,v in zip(xs,means)]]
                    axis.errorbar(xs,means,yerr=errors,marker='o',capsize=3,color=colors[system],label=SYSTEM_LABELS[system])
                    axis.set(xlabel='Arrival rate (sessions/s)' if experiment=='dynamic' else 'Offered sessions',ylabel=label,title=MODEL_LABELS.get(model,model))
                    axis.grid(alpha=.2)
            axes[index,0].legend(frameon=False,fontsize=8)
        fig.tight_layout()
        fig.savefig(output/f'{filename}.pdf',bbox_inches='tight');fig.savefig(output/f'{filename}.png',dpi=180,bbox_inches='tight');plt.close(fig)
    if timelines:
        # Every dynamic run is shown; no selection of a favorable seed.
        pairs=sorted({'/'.join(key.split('/')[:-1]) for key in timelines})
        for prefix in pairs:
            fig,axes=plt.subplots(3,1,figsize=(8,6),sharex=True)
            for system in ('resident','pilarius'):
                data=timelines[prefix+'/'+system]
                for axis,key,label in zip(axes,('active','pending_inputs','allocated_blocks'),('Active admitted sessions','Pending source inputs','Allocated GPU KV (GiB)')):
                    points=data[key]
                    scale=data['bytes_per_block']/2**30 if key=='allocated_blocks' else 1
                    axis.step([p[0] for p in points],[p[1]*scale for p in points],where='post',label=SYSTEM_LABELS[system],color=colors[system],linewidth=.8)
                    axis.set(ylabel=label,xlim=(0,None));axis.grid(alpha=.2)
            axes[0].set_title(prefix);axes[0].legend(frameon=False);axes[-1].set_xlabel('Time from original source clock (s)')
            fig.tight_layout();fig.savefig(output/('trajectory-'+prefix.replace('/','-')+'.pdf'),bbox_inches='tight');plt.close(fig)


def plot(rows, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size': 9, 'pdf.fonttype': 42, 'ps.fonttype': 42})
    models = sorted({row['model'] for row in rows})
    fig, axes = plt.subplots(len(models), 3, figsize=(10, 2.9*len(models)), squeeze=False)
    colors = dict(resident='#444444', on_demand='#d47716', pilarius='#1765ab', natural_pre_tick='#6e4796', after_submit='#26966f')
    for index, model in enumerate(models):
        for system in ('resident','on_demand','pilarius'):
            trials = [row for row in rows if row['model']==model and row['experiment']=='capacity' and row['system']==system]
            for axis, key, ylabel in zip(axes[index], ('on_time','completion_p95_ms','source_ready_p95_ms'),
                                        ('On-time input cycles', 'Completion p95 from tick (ms)', 'Completion p95 from source (ms)')):
                grouped = defaultdict(list)
                for trial in trials:
                    if trial[key] is not None:
                        grouped[trial['axis']].append(trial[key])
                xs = sorted(grouped)
                means = [sum(grouped[x])/len(grouped[x]) for x in xs]
                error = [[m-min(grouped[x]) for x,m in zip(xs,means)], [max(grouped[x])-m for x,m in zip(xs,means)]]
                axis.errorbar(xs, means, yerr=error, marker='o', capsize=3, label=SYSTEM_LABELS[system], color=colors[system])
                axis.set(xlabel='Offered sessions', ylabel=ylabel, title=MODEL_LABELS.get(model,model))
                axis.grid(alpha=.2)
        axes[index,0].legend(frameon=False)
    fig.tight_layout()
    fig.savefig(output/'capacity.pdf', bbox_inches='tight')
    fig.savefig(output/'capacity.png', dpi=180, bbox_inches='tight')
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('plan')
    parser.add_argument('--output-root', required=True)
    args = parser.parse_args()
    path, status = aggregate(args.plan, args.output_root)
    print(json.dumps(dict(path=str(path), state=status['state'])))


if __name__ == '__main__':
    main()
