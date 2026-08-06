"""Mock backend — CPU, no GPU. Reproduces a backend's per-tick latency from a cost
model so the Realtime server / scheduler can be exercised anywhere (tests, CI,
protocol development). Drop-in for the ``Backend`` protocol."""
from __future__ import annotations

import time
from typing import Sequence

from ..cost_model import CostModel
from ..models import ModelFacts


class MockBackend:
    _WORDS = ("hello there how are you doing today I think that sounds good "
              "let me check the weather is nice yes of course absolutely right").split()

    def __init__(self, facts: ModelFacts, cost: CostModel | None = None,
                 hbm_kv_gib: float = 80.0, real_sleep: bool = False):
        self.facts = facts
        self.cost = cost or CostModel(
            model=facts.name, device="cpu", c_fixed=8.0, alpha=0.0005,
            batch_base=8.0, batch_per_session=0.05, batch_alpha=0.0005,
            tail_factor=1.0, kv_bytes_per_token=facts.kv_bytes_per_token)
        self._hbm = hbm_kv_gib * 2**30
        self.real_sleep = real_sleep
        self.lengths: dict[int, int] = {}
        self.last_outputs: dict[int, list] = {}   # {sid: [token_ids] generated this step}
        import random
        self._rng = random.Random(0)

    @property
    def kv_bytes_per_token(self) -> int: return self.facts.kv_bytes_per_token
    @property
    def num_layers(self) -> int: return self.facts.num_layers
    @property
    def hbm_kv_bytes(self) -> float: return self._hbm
    @property
    def model(self) -> str: return self.facts.name

    def add_session(self, sid: int, kv_budget_tokens: int) -> None:
        self.lengths[sid] = 0
        self._budget = kv_budget_tokens

    def remove_session(self, sid: int) -> None:
        self.lengths.pop(sid, None)

    def context_len(self, sid: int) -> int:
        return self.lengths.get(sid, 0)

    def step(self, due_sids: Sequence[int], n_new: int) -> float:
        if not due_sids:
            self.last_outputs = {}
            return 0.0
        lat = self.cost.predict_batch([self.lengths.get(s, 0) for s in due_sids])
        self.last_outputs = {}
        for s in due_sids:
            self.lengths[s] = min(self.lengths.get(s, 0) + n_new,
                                  getattr(self, "_budget", 1 << 30))
            self.last_outputs[s] = [self._rng.randrange(0, len(self._WORDS))
                                    for _ in range(max(1, n_new))]
        if self.real_sleep:
            time.sleep(lat / 1000.0)
        return lat

    def detokenize(self, token_ids) -> str:
        return " ".join(self._WORDS[t % len(self._WORDS)] for t in token_ids)

    def abort(self, sid: int) -> None:
        pass
