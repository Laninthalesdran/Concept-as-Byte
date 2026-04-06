# Failed Experiment Alpha

## Concept-as-Byte: Dense Morphological Byte Encoding for Translation
## First Attempt — April 4-5, 2026

**Author:** Travis Edward Holley, TNT Holley, Inc.
**Architecture & Implementation:** Claude (Anthropic)

---

## What We Tried

We built a translation system based on the hypothesis that encoding language at the concept level — using Esperanto morphemes as byte codes — would be more efficient than subword tokenization (BPE) for training translation models.

The system has three components:
1. **AdamZ** (13.2M params) — a reasoning engine that thinks in Esperanto concept bytes
2. **LidiaZ** (7.18M-10.35M params) — a translator trained on parallel Esperanto-English data
3. **Lookup tables** — mapping between Esperanto morpheme byte codes and English word byte codes

We trained seven models to compare concept byte encoding against BPE tokenization across different data configurations.

---

## What Worked

### The encoding architecture works
- Esperanto morphemes map cleanly to byte codes
- The shared control layer (control bytes, digits, letters, punctuation) is identical across both language tables
- The encoder/decoder achieves 100% passthrough on 10,000 test sentences
- Morpheme composition with BOUNDARY bytes produces readable, decomposable byte sequences

### The models train and converge
- All seven models trained successfully and produced declining loss curves
- Concept byte models consistently converged faster than word byte models at matched parameter counts

### Basic concept translation works
- LidiaZ correctly maps core concepts: hundo→dog, kato→cat, suno→sun, bona→good, amas→love
- The model correctly identifies "li" (he) as the first word of a translation with 52.75% confidence

### Training numbers

| Model | Encoding | Vocab | Data | Best Eval Loss | Best Eval Perplexity |
|-------|----------|-------|------|---------------|---------------------|
| LLZ | Word bytes | 256 | English 144MB | 1.997 | 7.37 |
| LidiaZ 7M | Concept bytes | 256 | Parallel 61.8MB | 1.332 | 3.79 |
| LidiaZ 10M | Concept bytes | 256 | Parallel 61.8MB | 1.330 | 3.79 |
| BPE-A | BPE tokens | 2000 | English 104.9MB | Pending | Pending |
| BPE-B | BPE tokens | 2000 | Parallel 141.7MB | Pending | Pending |
| Esperanto-only | Concept bytes | 256 | Esperanto 36.2MB | Pending | Pending |
| BPE-C | BPE tokens | 2000 | Esperanto 26.7MB | **Cancelled** | **Cancelled** |

---

## What Failed

### 1. The English vocabulary table was catastrophically incomplete

The automated cleaning pipeline that built the English word table stripped out core vocabulary. "Winter", "mother", "father", "friend", "million", "thousand", "mountain", "church", "office" — basic English words were missing. We added 8.5 million words back from the raw source, but the damage was systemic.

Worse: our 2-source validation filter killed single-character words. **"I" and "a"** — the most common pronoun and the most common article in English — were missing from the vocabulary. The model literally could not say "I."

### 2. The training data was not audited at the concept level

We encoded 1.39 million parallel Esperanto-English pairs from the OPUS corpus. We verified the FORMAT was correct (Q/A separator present, END byte termination, duplicates removed). We did NOT verify the CONTENT — whether each Esperanto word mapped to the correct morpheme byte sequence, or whether each English word mapped to the correct word byte code.

This is the primary reason translation precision was poor. The model learned category-level mappings (a verb should go here, a number should go here) but not specific mappings (THIS verb, THIS number). Garbage in, garbage out.

### 3. The comparison was not fair

BPE-B trained on 2.83 million pairs (141.7MB). LidiaZ 7M trained on 1.39 million pairs (61.8MB). The difference is because our concept byte encoder rejected pairs it couldn't encode — words not in our tables got dropped. BPE tokenized everything and kept it all.

A fair comparison requires both models to train on the EXACT same sentence pairs, just encoded differently. We did not do this.

BPE-C (Esperanto-only, BPE tokenized) was planned but cancelled. The experiment was already corrupted by the varying sizes of training data across models, even though model size was held constant. Adding another model trained on yet another data size would not produce a meaningful comparison. A clean experiment requires identical data across all encoding methods. This was not achieved in Experiment Alpha.

### 3a. Compression makes data size comparison misleading

Concept byte encoding compresses text more aggressively than BPE tokenization. The same OPUS parallel sentences encode to 61.8MB in concept bytes vs 141.7MB in BPE tokens. Comparing "trained on 61.8MB vs 141.7MB" makes it look like BPE had 2.3x more data. It didn't. It had the same sentences encoded less efficiently.

The fair comparison metric is SENTENCES, not megabytes. But even sentence count is complicated: our concept byte encoder dropped sentences it couldn't encode (words missing from the table), while BPE tokenized everything and kept it all. So BPE trained on 2.83M pairs while concept bytes trained on 1.39M pairs — not because BPE had more data, but because our encoder was incomplete.

Any comparison between encoding methods must control for both the number of training examples AND the information content per example. We controlled for neither.

### 4. Translation specificity failed

When given Esperanto "havas" (has), the model ranked "has" #5 out of 5 verb candidates. When given "dek" (ten), it ranked "ten" #4 out of 5 number candidates. The model knows WHAT CATEGORY of word should appear but cannot determine WHICH SPECIFIC word.

This may be because:
- The training data contained encoding errors (see #2)
- The morpheme decomposition (hav + BOUNDARY + as) breaks the word into pieces the model hasn't learned to reassemble in the English direction
- 1.39M training pairs is insufficient for specific concept-to-word mapping

### 5. The structural byte advantage was not controlled for

~35% of bytes in concept-encoded sequences are structural (SPACE, BOUNDARY, END, Q/A). These are highly predictable and inflate the perplexity comparison in our favor. While the LLZ baseline had a similar ratio (36.6%), we should have reported adjusted perplexity from the start, not as an afterthought.

### 6. Composed word byte codes were assigned incorrectly

Early in development, composed Esperanto words were assigned their OWN byte codes instead of being represented as morpheme byte sequences with BOUNDARY. This violated the core architecture principle: the table decomposes, always. It was caught and fixed, but training data encoded before the fix may contain incorrect byte codes.

---

## What We Learned

1. **100% or nothing.** Every shortcut we took — the vocabulary filter, the unaudited training data, the unfair data split — produced a defect that degraded the final result. There is no "good enough" in encoding.

2. **The encoding matters more than the model.** At matched parameters, concept byte encoding converged faster than word byte encoding on the same architecture. This result held even with all the defects above. The core hypothesis appears sound. The execution was sloppy.

3. **Esperanto's regularity is a real computational advantage.** The model trained on structured Esperanto data learned faster than the model trained on chaotic English data, consistent with the 10-13x human learning speed advantage documented in the Esperanto pedagogy literature.

4. **You cannot trust automated pipelines to build clean data.** Every automated step — vocabulary cleaning, validation filtering, encoding, deduplication — introduced errors that were not caught until testing. The next attempt requires line-by-line human verification of training data.

5. **Publish failures.** The "I" bug, the unaudited data, the unfair comparison — documenting these is more valuable than hiding them. Anyone who builds on this work needs to know where the mines are.

---

## Unexpected Finding: Esperanto Training Effect on BPE

During the comparison study, BPE models trained on parallel Esperanto-English data (BPE-B) converged significantly faster than BPE models trained on English-only data (BPE-A), consistent with the propaedeutic effect observed in human language learning. Structured Esperanto data improves training regardless of encoding method.

However, a critical scaling difference exists between BPE tokenization and concept byte encoding:

**BPE vocabulary must scale with model size.** GPT-2 (124M params) uses 50,257 tokens. LLaMA (7B params) uses 32,000 tokens. As models grow, token vocabularies grow with them, and each token requires a row in the embedding table (vocab_size × d_model parameters). A significant fraction of parameters in large BPE models are consumed by the embedding layer — parameters that store vocabulary, not reasoning.

**Concept byte vocabulary is fixed at 256.** A 7M model uses 256 bytes. A 100M model uses 256 bytes. A 1B model uses 256 bytes. The vocabulary never scales because compositionality handles the complexity — you don't need more symbols, you compose longer sequences from the same 256 symbols.

This means: when a BPE model scales from 7M to 100M parameters, a growing fraction of new parameters goes to LARGER EMBEDDING TABLES. When a concept byte model scales from 7M to 100M parameters, ALL new parameters go to REASONING DEPTH. The concept byte architecture has a structural scaling advantage that compounds as models grow.

We have not tested this at scale. It remains a prediction, not a measurement.

---

## What Comes Next

1. **Full audit of all parallel training pairs.** Every pair decoded both sides, verified concept-for-concept. No sampling.
2. **Fair comparison.** Same sentences, same pairs, just encoded differently. BPE vs concept bytes on identical data.
3. **Corrected vocabulary.** "I" and "a" in the table. Every common English word verified present.
4. **Retrain from clean data.** New training run with audited data.
5. **AdamZ integration.** The reasoning engine has not been tested with the translation pipeline. That's the actual goal — reasoning in Esperanto bytes, translating to English.

---

## Repository Contents

This repository contains everything from the first attempt:

- **Model weights** — trained models, warts and all
- **Training logs** — every step, every eval, every checkpoint
- **Training scripts** — exactly what was run
- **Model definitions** — the architectures
- **Encoding tables** — Esperanto and English byte code tables
- **Encoder/decoder** — the pipeline code
- **This document** — what failed and why

Everything is released under CC-BY-NC-SA 4.0 so anyone can reproduce, verify, or improve on these results.

---

## Hardware

- NVIDIA RTX PRO 6000 Blackwell Server Edition (98GB) × 2 on RunPod
- NVIDIA GeForce RTX 4070 Ti SUPER (16GB) local desktop
- Total training cost: approximately $30 in RunPod credits

---

*Travis Edward Holley*
*TNT Holley, Inc.*
*April 5, 2026*

*"100% or nothing. We said it. And we missed 'I'."*
