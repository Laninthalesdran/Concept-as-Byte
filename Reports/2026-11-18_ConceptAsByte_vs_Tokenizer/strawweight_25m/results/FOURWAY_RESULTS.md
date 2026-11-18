# Four-way number-layout test — Strawweight 25M, one mixed pass, full runs

| | v1 as Lightweight | v2 ones-first | v3 BOUNDARY digits | v4 place bytes | reference |
|---|---|---|---|---|---|
| Single families, right kind | 79.1 | 80.0 | 79.7 | 79.6 | wording guesser 50.1 |
| Single families, exact | 52.1 | 52.1 | 52.0 | 52.0 |  |
| Pairs, exact | 100.0 | 100.0 | 100.0 | 100.0 |  |
| Out-of-range, right kind | 50.2 | 60.6 | 48.6 | 51.8 | wording guesser 49.3 |
| Out-of-range, exact | 0.0000 | 0.2000 | 0.0000 | 0.0000 |  |
| Benchmark: hellaswag | 28.7 | 28.9 | 28.6 | 28.4 | chance 25 |
| Benchmark: arc | 28.9 | 28.6 | 29.0 | 29.1 | chance 25 |
| Benchmark: piqa | 52.9 | 52.8 | 53.8 | 53.8 | chance 50 |
| Benchmark: mmlu_cloze | 26.1 | 26.1 | 26.2 | 25.9 | chance 25 |
| Benchmark: commonsense_qa | 24.2 | 23.3 | 24.1 | 24.2 | chance 20 |
| Benchmark: winogrande | 48.5 | 48.9 | 48.1 | 48.8 | chance 50 |
| Benchmark: openbookqa | 25.2 | 24.8 | 23.4 | 23.6 | chance 25 |
| Benchmark: trivia_qa | 0.0400 | 0.0400 | 0.0300 | 0.0200 | chance 0 |
| Benchmark: gsm8k | 0.0000 | 0.0000 | 0.0000 | 0.0000 | chance 0 |
| Final held-out loss: web (per layout byte) | 1.3708 | 1.3459 | 1.2817 | 1.2262 |  |
| Final held-out loss: logic (per layout byte) | 0.1302 | 0.1308 | 0.1285 | 0.1266 |  |
| Final held-out loss: unseen_singles (per layout byte) | 0.1419 | 0.1418 | 0.1411 | 0.1384 |  |
| Final held-out loss: unseen_pairs (per layout byte) | 0.1160 | 0.1164 | 0.1144 | 0.1122 |  |
| Final held-out loss: oor (per layout byte) | 0.4551 | 0.3987 | 0.4992 | 0.4309 |  |
| Web bits per original character | 1.0970 | 1.0140 | 0.9970 | 0.9410 |  |

Per family (right kind / exact):

| family | v1 | v2 | v3 | v4 | wording |
|---|---|---|---|---|---|
| f1 | 65.8 / 17.5 | 67.2 / 18.8 | 64.0 / 16.0 | 65.5 / 15.5 | 41.5 |
| f2 | 89.2 / 81.5 | 91.0 / 81.0 | 92.0 / 83.8 | 92.8 / 82.2 | 56.0 |
| f3 | 85.8 / 80.3 | 88.2 / 81.9 | 87.9 / 82.7 | 87.9 / 82.7 | 43.8 |
| f4 | 99.5 / 46.9 | 100.0 / 45.3 | 99.5 / 46.6 | 99.5 / 46.6 | 50.9 |
| f5 | 69.8 / 49.1 | 73.2 / 48.0 | 72.7 / 48.3 | 70.1 / 46.2 | 49.9 |
| f6 | 54.0 / 3.8 | 51.8 / 4.2 | 56.0 / 3.8 | 52.5 / 2.8 | 51.2 |
| f7 | 92.1 / 91.0 | 94.2 / 93.4 | 94.0 / 92.9 | 94.5 / 92.6 | 59.2 |
| f8 | 76.0 / 52.5 | 73.5 / 51.8 | 72.2 / 45.0 | 74.5 / 51.0 | 43.8 |
| f9 | 76.3 / 54.4 | 76.3 / 52.5 | 77.6 / 56.7 | 73.4 / 52.2 | 54.6 |
| f10 | 75.8 / 51.1 | 78.0 / 51.4 | 75.5 / 51.9 | 79.7 / 54.7 | 48.6 |
| f11 | 89.0 / 50.8 | 89.8 / 50.0 | 88.4 / 50.0 | 88.4 / 51.1 | 52.2 |
| pairs | 100.0 / 100.0 | 100.0 / 100.0 | 100.0 / 100.0 | 100.0 / 100.0 | 49.1 |
