# Benchmark data (`data/`)

The full-duplex audio benchmark data is **not committed** to this repository.
It derives from third-party corpora (e.g. the CANDOR conversational corpus, via
[Full-Duplex-Bench](https://github.com/DanielLin94144/Full-Duplex-Bench)) that
carry their own licenses and redistribution terms. `data/` is git-ignored — stage
it locally before running the FD-Bench experiments.

## Expected layout

The experiment scripts (`experiments/run_fdbench*.sh`, `experiments/moshi_fdbench.py`)
expect each task under `data/fdbench/<task>/<task>/<id>/`:

```
data/fdbench/
  candor_turn_taking/candor_turn_taking/<id>/input.wav
  synthetic_pause_handling/synthetic_pause_handling/<id>/input.wav
  synthetic_user_interruption/synthetic_user_interruption/<id>/input.wav
  icc_backchannel/icc_backchannel/<id>/input.wav
```

Each `<id>/` holds the task's `input.wav`; the pipeline writes `output.wav`,
`output.json` (Whisper word timestamps), and the per-task evaluator JSON
(e.g. `turn_taking.json`) alongside it.

## How to obtain it

1. Clone the upstream benchmark into `external/` (also git-ignored):

   ```bash
   git clone https://github.com/DanielLin94144/Full-Duplex-Bench external/Full-Duplex-Bench
   ```

2. Download the task audio following that repo's instructions and unpack it into
   `data/fdbench/` using the layout above. (If you unzip on macOS, delete the
   stray `__MACOSX/` directories.)

3. Verify one task resolves, e.g.:

   ```bash
   ls data/fdbench/candor_turn_taking/candor_turn_taking/*/input.wav | head
   ```

The committed `results/` JSONs were produced from this data and remain in the
repository for inspection and reproducibility of the reported numbers.
