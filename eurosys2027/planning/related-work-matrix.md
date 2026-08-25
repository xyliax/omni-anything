# Closest-Work Matrix

完成此表后再冻结 New Problem/Setting 与 Technique 的定位。每一行必须指向可核验的论文版本和日期。

| Work | Long-lived session | Growing KV | Predictable next use | Partial GPU residency | Restore prefetch | Real-time or periodic SLO | Difference from this paper |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `<interactive/streaming serving work>` | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| `<KV offload/tiering work>` | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| `<real-time scheduling work>` | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| `<closest evaluated system>` | TBD | TBD | TBD | TBD | TBD | TBD | TBD |

## Search Buckets

- Interactive and streaming model serving.
- Full-duplex or continuous multimodal serving.
- KV cache allocation, prefix caching and long-context serving.
- GPU/CPU KV offload, tiering and prefetch.
- Periodic, deadline-aware and next-use-aware resource scheduling.
- GPU memory oversubscription and working-set management.

## Novelty Gate

- [ ] The single closest work is named.
- [ ] The difference is expressible in one sentence without marketing language.
- [ ] The comparison covers assumptions, mechanism and evidence, not only features.
- [ ] Any “first” claim has been checked against current literature immediately before submission.
