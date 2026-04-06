# Known Issue: Multi-Byte Code Adjacency Noise

**Discovered:** April 6, 2026
**Discovered by:** Travis Holley
**Status:** Architectural decision made — single-byte vocabulary only going forward

---

## The Problem

When two or more bytes form a single code (e.g., 0x8E 0x7F = one concept), the model sees two byte values adjacent with no separator. It has no way to distinguish this mechanical adjacency from meaningful adjacency. The model applies math to ALL adjacency patterns and finds relationships — real or not.

Byte codes in the JalekCore table were assigned alphabetically. "agrabl" (agreeable) got a byte code next to "agord" (tune) because they start with the same letters, not because they mean anything similar. The model may learn a false semantic relationship between them because their codes are numerically adjacent.

This is the same failure mode as large-model hallucination — the model found a pattern that isn't real and encoded it as knowledge — but from a different source. BPE models hallucinate from noisy text. Concept byte models could hallucinate from arbitrary byte numbering.

## Evidence

LidiaZ 10M (Experiment Alpha) demonstrated that concept byte models learn by cracking byte relationship patterns. The model decoded three relationship types from the raw byte stream:

1. **byte byte** — consecutive bytes with no separator = parts of one multi-byte code
2. **byte BOUNDARY byte** — separator = parts of one word (morpheme composition)
3. **byte SPACE byte** — separator = separate words in a sentence

The model used these patterns to reverse-engineer translations from dirty data — including figuring out "li" (he) with 52.75% confidence when "I" was missing from the vocabulary entirely. It also correctly mapped hundo→dog, kato→cat, suno→sun, amas→love.

The model applies the same math to ALL byte adjacency. It cannot distinguish real patterns (semantic relationships across BOUNDARY and SPACE) from spurious patterns (alphabetically adjacent byte assignments with no separator).

## The Solution

**Single-byte vocabulary only. 256 entries. No multi-byte codes.**

Every byte the model sees is one concept. If a word doesn't have a single-byte code, it gets spelled letter by letter. Every relationship between bytes is explicitly defined by a control byte (BOUNDARY, SPACE, etc.). No ambiguity. No spurious adjacency patterns. Every pattern the model finds is real.

## Impact on Existing Work

All models trained on multi-byte JalekCore encoding carry this noise in their weights:
- Experiment Alpha (LidiaZ 7M, LidiaZ 10M, LLZ 7M)
- Experiment Beta (8 models, currently training)
- 135M benchmark model

These results are still valid for measuring relative scaling behavior, but absolute performance may be degraded by false patterns from multi-byte adjacency.

## Future Test

Same 8 models, same data, single-byte encoding vs multi-byte encoding. Directly measures whether multi-byte codes help or hurt.

---

*Travis Edward Holley*
*TNT Holley, Inc.*
*April 6, 2026*
