# Metronome-Bench Leaderboard

MSCS = max sustainable concurrent sessions @ 0.1% deadline-miss SLO. Hardware: RTX PRO 6000 Blackwell.

| Model | Tick | B0 | B1 | B2 | **M** | M/B1 | $/sess-hr (M) | pred=meas (G5) | KV gain | class |
|---|---|---|---|---|---|---|---|---|---|---|
| moshi | 80 ms | 4 | 40 | 40 | **136** | 3.4× | $0.0147 | 136=160 | 10.7× | essential |
| minicpm-o | 1000 ms | 48 | 17 | 17 | **71** | 4.2× | $0.0282 | 71=71 | 8.4× | essential |
| qwen3-omni | 200 ms | 16 | 64 | 64 | **158** | 2.5× | $0.0127 | 158=160 | 2.8× | complementary |
