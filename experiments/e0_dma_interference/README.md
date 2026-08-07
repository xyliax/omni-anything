# E0: DMA/decode interference

E0 measures whether pinned H2D traffic on a separate CUDA stream inflates decode latency. It is the
physical go/no-go check that precedes implementation of the KV conveyor.

```text
run.py                  benchmark and immutable output-directory creation
model.lock              model ID and immutable Hugging Face revision
reference_data/         previously measured PCIe/H2D calibration inputs
```

Run it from the repository root:

```bash
python3 -m experiments.e0_dma_interference.run --device 0
```

Each invocation creates a new directory under:

```text
results/e0_dma_interference/runs/<UTC-run-id>/
├── measurements.csv
└── summary.json
```

The committed initial result is indexed in
[`../../results/README.md`](../../results/README.md). The exact method and acceptance threshold are
defined in [`../../docs/PAPER-EXPERIMENTS.md`](../../docs/PAPER-EXPERIMENTS.md).
