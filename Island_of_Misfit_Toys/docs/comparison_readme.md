# Model Comparison Study — The Ludwik Zamenhof Method

## Overview

Seven models trained to compare three encoding methods across three data configurations. All models use the same base Transformer architecture with matched parameter counts (~7.18M). Only the encoding method and training data differ.

## Models

| # | Model | Encoding | Vocab | Data | Params | Status |
|---|-------|----------|-------|------|--------|--------|
| 1 | LLZ | Word bytes | 256 | English 144MB | 7,178,880 | Complete |
| 2 | LidiaZ 7M | Concept bytes | 256 | Parallel Esp-Eng 61.8MB | 7,178,880 | Complete |
| 3 | LidiaZ 10M | Concept bytes | 256 | Parallel Esp-Eng 61.8MB | 10,346,000 | Complete |
| 4 | BPE-A | BPE tokens | 2000 | English 104.9MB | 7,185,024 | Training |
| 5 | BPE-B | BPE tokens | 2000 | Parallel Esp-Eng 141.7MB | 7,185,024 | Training |
| 6 | Esperanto-only | Concept bytes | 256 | Esperanto 36.2MB | 7,178,880 | Training |
| 7 | BPE-C | BPE tokens | 2000 | Esperanto 26.7MB | 7,185,024 | Queued |

## Results (Completed Models)

| Model | Best Eval Loss | Best Eval Perplexity | Epochs |
|-------|---------------|---------------------|--------|
| LLZ (word bytes, English) | 1.997 | 7.37 | 3 |
| LidiaZ 7M (concept bytes, parallel) | 1.332 | 3.79 | 5 |
| LidiaZ 10M (concept bytes, parallel) | 1.330 | 3.79 | 5 |

## Key Finding

At matched parameter count (7.18M), concept byte encoding with parallel data achieves perplexity 3.79 vs word byte encoding at 7.37 — a 1.94x improvement with 57% less training data.

## Architecture

All models share:
- RoPE positional encoding
- RMSNorm (pre-norm)
- SwiGLU feedforward
- Tied embeddings (where vocab allows)
- Causal attention mask
- AdamW optimizer (lr=3e-4, betas=(0.9, 0.95), weight_decay=0.01)
- Linear warmup (1000 steps) + cosine LR decay
- Gradient clipping at 1.0
- Batch size 64, sequence length 512

## Known Defects and Honest Limitations

### Vocabulary Bug
The English vocabulary table was missing "I" (first-person pronoun) and "a" (indefinite article). These single-character words were excluded by an automated 2-source validation filter that rejected entries shorter than 2 characters. This is visible in translation output: "mi amas vin" (I love you) generated "want you to love you" because the model had no byte code for "I." The defect has been corrected in the vocabulary table but NOT in the trained model weights released here. These results are as-is.

### Unaudited Training Data
The 1.39M parallel training pairs were encoded and verified structurally (correct format, Q/A separator, END byte, deduplication) but NOT verified at the concept level. We did not confirm that every Esperanto word mapped to the correct morpheme byte sequence or that every English word mapped to the correct word byte code. This likely degrades translation precision. A full line-by-line audit of all 1.39M pairs is required before the next training run.

### Translation Precision
Translation testing showed that the model correctly maps core concepts (hundo→dog, kato→cat, suno→sun, bona→good) but fails on specificity within categories. When tested with candidate ranking:
- Pronouns: "li" (he) → ranked "he" #1 at 52.75% confidence. Correct.
- Verbs: "havas" (has) → ranked "has" #5 out of 5 candidates. The model identifies the CATEGORY (verb should go here) but not the specific verb.
- Numbers: "dek" (ten) → ranked "ten" #4 out of 5 candidates. Same issue — correct category, wrong specific value.

This is consistent with training on sentence-level parallel pairs without concept-level verification.

### Structural Byte Advantage
Approximately 35% of bytes in concept-encoded sequences are structural (SPACE between words, BOUNDARY between morphemes, END at termination). These are highly predictable and lower measured perplexity. The LLZ English-only baseline has a similar structural byte ratio (36.6%). Both measured and adjusted perplexity numbers are reported:

| Model | Measured Perplexity | Adjusted (content-only) Perplexity |
|-------|-------------------|-----------------------------------|
| LLZ (word bytes) | 7.37 | 23.36 |
| LidiaZ 7M (concept bytes) | 3.79 | 7.73 |

All encoding methods — including BPE tokenization — have built-in structural predictability. BPE embeds it invisibly in token co-occurrence statistics. Concept byte encoding makes it explicit and measurable. Neither number is more "true" than the other.

### Assumptions We Made
1. We assumed Esperanto morphology is a good intermediate representation for machine translation. The perplexity results support this but translation quality needs more work.
2. We assumed that concept-level byte encoding would be more parameter-efficient than subword tokenization. The perplexity comparison supports this but the fair cross-vocabulary comparison (bits per source byte) requires careful normalization.
3. We assumed that the OPUS parallel corpus data was clean enough to train on without per-pair verification. This assumption was wrong and affected translation precision.
4. We assumed that a 2-source minimum filter for English vocabulary validation would catch all garbage without losing real words. This assumption was wrong — it killed "I" and "a."

## Reproduction

Training logs in `../training_logs/`. Model definitions and training scripts in `../models/`. All training data sourced from public corpora (OPUS, Tatoeba, C4, Gutenberg) under CC-BY or equivalent licenses.

## Hardware

- Concept byte models: NVIDIA RTX PRO 6000 Blackwell Server Edition (98GB) on RunPod
- LLZ baseline: NVIDIA GeForce RTX 4070 Ti SUPER (16GB) local
- BPE baselines: NVIDIA RTX PRO 6000 Blackwell Server Edition on RunPod

## License

CC-BY-NC-SA 4.0 for non-commercial use.
Commercial licensing: see Licensing_Royalty_Rate_Cap.pdf in repository root.
