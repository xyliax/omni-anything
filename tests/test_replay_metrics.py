from copy import deepcopy

import pytest

from infra.trace.replay import evaluate


def example():
    config = dict(engine=dict(max_model_len=4096), workload=dict(output_token_cap=8), admission=dict(cohort=dict(
        configuration=dict(period_s=2), sessions=[dict(session_id='a', start_time_s=.173, duration_s=6),
                                                 dict(session_id='b', start_time_s=.173, duration_s=6)])))
    client = dict(kind='open_loop_replay', total=2, start_ns=10**12, err=0, sessions=[
        dict(id='a', sid=1, admitted=True, source_start_ns=10**12+173000000, period_ns=2*10**9,
             first_release_ns=10**12+2173000000, phase_policy='natural', sends=[], completed=False),
        dict(id='b', sid=2, rejected=True)])
    gateway, worker = [], []
    for seq, latency in ((1, .2), (2, 2.5)):
        release = client['sessions'][0]['first_release_ns']+(seq-1)*2*10**9
        identity = dict(session=1, epoch=1, frame=seq)
        gateway.extend([dict(identity, event='input_ready', time_ns=release+1000000),
                        dict(identity, event='input_release', time_ns=release+1000000,
                             release_ns=release, deadline_ns=release+2*10**9)])
        worker.extend([dict(identity, event=name, time_ns=release+round(latency*1e9))
                       for name in ('input_received', 'engine_input')])
        worker.append(dict(identity, event='compute_complete', time_ns=release+round(latency*1e9),
                           tokens=8, finish_reason='length', context_tokens=100*seq))
    return config, client, gateway, worker


def test_rejected_and_unfinished_work_never_disappear():
    result = evaluate(*example())
    assert not result['invalid_reasons']
    assert (result['offered_frames'], result['admitted_frames']) == (6, 3)
    assert (result['on_time'], result['late'], result['unfinished']) == (1, 1, 1)
    assert result['on_time_offered_fraction'] == 1/6
    assert result['on_time_admitted_fraction'] == 1/3
    assert result['completion_from_release_ms']['maximum'] == 2500


@pytest.mark.parametrize('change', ['deadline', 'phase', 'duplicate', 'work'])
def test_invalid_measurements_cannot_claim_success(change):
    config, client, gateway, worker = deepcopy(example())
    if change == 'deadline':
        gateway[1]['deadline_ns'] += 2*10**9
    elif change == 'phase':
        client['sessions'][0]['first_release_ns'] += 10**9
    elif change == 'duplicate':
        worker.append(worker[-1])
    elif change == 'work':
        worker[-1]['tokens'] = 1
    assert evaluate(config, client, gateway, worker)['invalid_reasons']


def test_measurement_warmup_does_not_drop_late_or_unfinished_work():
    config, client, gateway, worker = example()
    config['admission']['cohort']['configuration']['measurement_start_s'] = 3
    result = evaluate(config, client, gateway, worker)
    assert (result['offered_frames'], result['admitted_frames'], result['late'], result['unfinished']) == (4, 2, 1, 1)
