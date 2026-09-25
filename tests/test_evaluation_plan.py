import json
import wave
from pathlib import Path

import pytest

from experiments.conveyor.evaluate import prepare, execute_plan


def test_matrix_freezes_matched_inputs_policies_and_costs(tmp_path, monkeypatch):
    audio = tmp_path/'speech.wav'
    with wave.open(str(audio), 'wb') as stream:
        stream.setparams((1,2,16000,0,'NONE','not compressed'))
        stream.writeframes(b'\1\0' * 160000)
    costs = dict(compute_s=.1, backup_s=.01, max_evict_blocks=8, h2d_blocks_per_s=1000,
        transfer_overhead_s=.001, safety_s=.01, gpu_reserve_blocks=1, host_reserve_blocks=1, max_sessions=4)
    for system,mode in [('pilarius','maximum_context'),('on_demand','static_limit')]:
        (tmp_path/f'{system}.json').write_text(json.dumps(dict(costs,planning_mode=mode)))
    spec = dict(schema_version=1,evidence_role='diagnostic',audio=['speech.wav'],models=[dict(
        common=dict(model_preset='minicpm_o45', max_model_len=2048, slots=2), resident_limit=3,
        pilarius_profile='pilarius.json',on_demand_profile='on_demand.json',
        capacity=dict(concurrency=[2], seeds=[11,22,33], session_duration_s=4, measurement_start_s=2),
        ablation_concurrency=[2])])
    (tmp_path/'spec.json').write_text(json.dumps(spec))
    plan_path = prepare(tmp_path/'spec.json',tmp_path/'prepared')
    plan = json.loads(plan_path.read_text())
    assert len(plan['points']) == 15
    for seed in (11,22,33):
        points = [row for row in plan['points'] if row['seed']==seed]
        assert len({row['config']['cohort_manifest'] for row in points}) == 1
        configs = {row['system']:row['config'] for row in points}
        assert configs['resident']['phase_policy']=='natural'
        assert configs['natural_pre_tick']['phase_policy']=='natural'
        assert {configs[k]['phase_policy'] for k in ('pilarius','on_demand','after_submit')}=={'assigned'}
        assert {configs[k]['restore_policy'] for k in ('pilarius','natural_pre_tick')}=={'pre_tick'}
    with pytest.raises(FileExistsError):
        prepare(tmp_path/'spec.json',tmp_path/'prepared')
    # Tampering is detected before a worker can be launched.
    frozen = Path(next(iter(plan['files'])))
    frozen.write_text('{}')
    with pytest.raises(ValueError, match='frozen experiment input changed'):
        execute_plan(plan_path)
