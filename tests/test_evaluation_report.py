import json
from pathlib import Path

import pytest

from infra.run.artifacts import RunStore, sha256_file
from infra.trace.evaluation import load_point, aggregate, timeline
from infra.trace.calibration import measure


def fixture_run(tmp_path):
    config=dict(observations=dict(verify_copies=False), model=dict(preset='mini',id='model',revision='revision'),
        engine=dict(max_model_len=128,kv_pool_gib=1,host_offload_gib=4,resident_control=False),
        workload=dict(output_token_cap=8),admission=dict(cohort=dict(configuration=dict(measurement_start_s=0),
            sessions=[dict(session_id='a',start_time_s=0,duration_s=4)])))
    store=RunStore.create(tmp_path,'fixture',dict(git=dict(dirty=False),config=config))
    metrics=dict(invalid_reasons=[],offered_sessions=1,admitted_sessions=1,rejected_sessions=0,
        completed_sessions=0,offered_frames=2,admitted_frames=2,on_time=1,late=0,unfinished=1,
        on_time_offered_fraction=.5,on_time_admitted_fraction=.5,peak_allocated_gpu_blocks=4,
        gpu_pool_blocks=8,bytes_per_gpu_block=32,peak_valid_host_backing_blocks=3,
        completion_from_release_ms=dict(p95=200),completion_from_source_ready_ms=dict(p95=200),
        preprocessing_to_engine_enqueue_ms=dict(p95=10),observed_context_tokens=dict(maximum=64),
        frames=[dict(source_ready_ns=2*10**9,deadline_ns=4*10**9,complete_ns=2200000000),
                dict(source_ready_ns=4*10**9,deadline_ns=6*10**9,complete_ns=None)])
    store.write_json('replay_metrics.json',metrics)
    store.write_json('client.json',dict(start_ns=0,sessions=[dict(id='a',sid=1,admitted=True,admitted_ns=1,completed=False)]))
    worker=[dict(event='gpu_allocation',time_ns=0,allocated_blocks=0),
            dict(event='gpu_allocation',time_ns=10**9,allocated_blocks=4),
            dict(event='compute_complete',session=1,frame=1,time_ns=2200000000,context_tokens=64,output_token_sha256='token-hash')]
    store.file('service_events.jsonl').write_text('\n'.join(map(json.dumps,worker))+'\n')
    store.finalize(required=['client.json','replay_metrics.json','service_events.jsonl'],exit_code=0)
    entry=dict(run_path=str(store.path),status_sha256=sha256_file(store.file('status.json')))
    point=dict(experiment='capacity',axis=1,seed=11,system='pilarius')
    return store,point,entry


def test_report_preserves_unfinished_denominator_and_checks_retained_hashes(tmp_path):
    store,point,entry=fixture_run(tmp_path)
    result,_=load_point(point,entry,formal=True)
    assert result['valid']
    assert result['unfinished']==1
    assert result['on_time_offered_fraction']==.5
    assert result['drain_after_source_end_s'] is None
    times=timeline(store.path)
    assert times['active'][-1][1]==1  # unfinished is not an observed departure
    assert times['pending_inputs'][-1][1]==1
    store.file('service_events.jsonl').write_text('{}\n')
    with pytest.raises(ValueError,match='retained artifact changed'):
        load_point(point,entry)


def test_incomplete_matrix_cannot_silently_drop_points(tmp_path):
    plan=tmp_path/'plan.json'
    plan.write_text(json.dumps(dict(points=[dict(point_id='a')],evidence_role='formal')))
    (tmp_path/'execution.jsonl').write_text('')
    with pytest.raises(ValueError,match='matrix is incomplete'):
        aggregate(plan,tmp_path/'out')
