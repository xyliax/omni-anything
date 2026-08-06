"""Shared helpers for the experiment scripts."""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from metronome import models
from metronome.cost_model import CostModel

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CM_DIR = os.path.join(ROOT, "results", "cost_model")

# HBM available for KV on this accelerator (96 GiB card; reserve weights+workspace).
# Reported per the 97 887 MiB total seen on the RTX PRO 6000 Blackwell.
HBM_TOTAL_GIB = 96.0
WEIGHTS_RESERVE_GIB = 16.0   # 7-9B weights + activation workspace
HBM_KV_GIB = HBM_TOTAL_GIB - WEIGHTS_RESERVE_GIB


def load_cost(name) -> CostModel:
    return CostModel.from_json(os.path.join(CM_DIR, f"{name}.json"))


def hbm_kv_bytes(gib=HBM_KV_GIB) -> float:
    return gib * 2**30


def all_models():
    return [m for m in ("moshi", "minicpm-o", "qwen3-omni")
            if os.path.exists(os.path.join(CM_DIR, f"{m}.json"))]
