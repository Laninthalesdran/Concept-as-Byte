# Concept bytes vs. a tokenizer: report, results and logs (November 18, 2026)

**Author:** Travis Edward Holley · TNT Holley, Inc.

This folder holds the report `ConceptAsByte_vs_Tokenizer_Strawweight.pdf` together with the score files and training
logs behind every number in it. Nothing here was hand-edited: each file is copied unchanged from the run that
produced it. Open the PDF first; this page says which file backs which part of it.

## What was tested

- **Strawweight 25M, five byte models and one tokenizer twin, trained on identical documents in one mixed pass**
  (web text + reasoning curriculum, shuffled together):
  - four number layouts (`v1`–`v4`);
  - the ones-first layout with the word separators removed (`v2ns`);
  - a concept-patch transformer (`cp_v2`);
  - the same 25M transformer body behind a 49,152-entry BPE tokenizer (`tok`, 62.9M parameters in total).
- **Lightweight 132.5M**, the larger concept-byte model, scored on the same reasoning probe plus public benchmarks,
  never-seen web text and the nanochat CORE suite.

These 25M models are new experiments on the November competition table. They are **not** the released ZophiaE
Strawweight checkpoint.

## Headline numbers (all in the PDF, all in the files below)

| Same documents, same 25M body | Concept bytes V2 | V2 without separators | Concept-patch V2 | Tokenizer (63M) |
|---|---|---|---|---|
| Never-trained single reasoning families, right kind / exact | 80.0 / 52.1 | 78.7 / 48.6 | 80.0 / 52.8 | 76.9 / 47.0 |
| All probe questions, exact | 67.6 | 65.2 | 68.0 | 64.1 |
| Numbers outside the trained range, right kind | 60.6 | 67.2 | 51.2 | 52.2 |
| 843 shared never-seen web documents, bits per character (lower is better) | 1.132 | 1.160 | 1.185 | 1.270 |

The Lightweight 132.5M scores **0.1439 on nanochat CORE** (GPT-2 124M: 0.1139).

**Running cost.** Energy was measured, not estimated. Per character of text, the tokenizer model is cheaper to run,
because a byte model takes more steps for the same text. Every energy run is listed separately; nothing is
averaged. PDF sections 9–11 explain this.

## Files

### `strawweight_25m/results/`
| File | What it is |
|---|---|
| `probe_<model>.txt` / `.json` | Reasoning probe per family: right kind, exact, and the two baselines (a wording-only guesser, a constant answer) |
| `oor_<model>.txt` / `.json` | Numbers outside the trained range |
| `bench_<model>.json` / `.log` | Public benchmarks (HellaSwag, ARC, PIQA, MMLU cloze, CommonsenseQA, Winogrande, OpenBookQA, TriviaQA, GSM8K) |
| `web_shared.json` / `.txt`, `web_shared_v2ns.txt`, `web_shared_cp.txt` | Bits per original character on the 843 shared never-seen web documents (1,165,941 characters) |
| `FOURWAY_RESULTS.md` | The four number-layout comparison in one table |
| `energy.json` | First energy test, one run per model (byte V2 vs. tokenizer) |
| `energy_three_way.txt`, `energy_v2_v2ns_tok.json` | Session 1: READ and WRITE, two runs per model (V2, no separators, tokenizer) |
| `energy_read4.json` | Session 2: READ, two runs per model (adds the concept-patch model) |

Model tags: `v1`–`v4` are the number layouts (`v2` = ones-first), `v2ns` is V2 without separators, `cp_v2` is the
concept-patch V2, and `tok` is the tokenizer twin.

### `strawweight_25m/training_logs/`
Full training logs, one per model: `runs2_v1` to `runs2_v4`, `runs2_v2ns`, `runs_tok_v2`, `runs_cp_v2`. Each log
records the data plan, the parameter count, every logged step, the held-out evaluations, and the final checkpoint.

### `lightweight_132m/`
- `results/`: the probe, out-of-range, public benchmarks, bits per character on never-seen climbmix text, and
  nanochat CORE (`core_lw`).
- `training_logs/`:
  - `log.jsonl`: per-step loss, learning rate and throughput;
  - `train2_until_0446.log` and `train2.log`: the run before and after its resume;
  - `run_lw_tests.log`: the test pass.

## What is not here, and why

- **Per-question answers and the reasoning curriculum.** The curriculum's questions are private, so the files of
  individual answers stay out. The family-level scores are all here.
- **Per-item benchmark dumps.** They are large and add nothing to the summary files.
- **Experiments still running.** On November 18 a second set of concept-patch runs was in progress (separators
  given to the large model as markers instead of bytes). Those results will be added when they finish.

## Hardware

- The Strawweight runs and all energy measurements used one RTX 4070 Ti SUPER (16 GB).
- The Lightweight 132.5M trained on rented 8-GPU nodes.

License: CC-BY-NC-SA 4.0 on GitHub (see the repository's scope map). On Hugging Face these files sit beside the
model under the repository's license.
