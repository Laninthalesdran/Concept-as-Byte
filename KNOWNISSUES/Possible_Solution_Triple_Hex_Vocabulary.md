# Possible Solution: Triple Hex Vocabulary (4096 Tokens)

**Proposed:** April 6, 2026
**Proposed by:** Travis Holley
**Status:** REJECTED — see addendum below

---

## The Problem Being Solved

Multi-byte codes create adjacency noise. When two bytes form one code, the model sees two numbers next to each other and finds patterns in their numerical relationship — patterns that are artifacts of the encoding, not real semantics. This is an uncontrolled variable that may cause hallucination.

The single-byte-only solution (256 entries, everything else spelled) solves the noise but creates a context window problem — common words get spelled letter by letter, consuming 5-10x more sequence length.

## The Proposed Solution

Expand the model's vocabulary from 256 (single hex byte, 0x00-0xFF) to 4096 (triple hex, 0x000-0xFFF).

4096 atomic tokens. Each one is a single embedding lookup. No multi-byte codes. No adjacency noise. No spelling overhead.

## What Fits in 4096

- ~10 control bytes
- ~10 digits
- ~32 letters
- ~4 punctuation
- ~12 grammatical endings
- ~41 affixes (suffixes + prefixes)
- ~80 function words
- ~917 Zamenhof roots (ALL of them)
- ~67 symbols (if needed)
- **~2,800+ remaining slots** for common compounds, proper nouns, domain terms, or future expansion

Every Esperanto morpheme gets its own atomic token. No spelling needed. No context window inflation. Every token is one concept, every relationship between tokens is defined by control tokens.

## How It Works in Practice

Each token is stored as a fixed-width code in the training data. The model's embedding layer has 4096 entries instead of 256. Each position in the sequence is one token — one concept — regardless of how many bytes it takes to store the code on disk.

The model never sees "bytes." It sees token IDs from a vocabulary of 4096. Token boundaries are fixed — no ambiguity about where one token ends and another begins. No multi-byte interpretation needed.

## Tradeoffs

**Embedding cost:** At d_model=320 (AdamZ size), embedding goes from 256 × 320 = 81,920 params to 4096 × 320 = 1,310,720 params. About 1.2M more parameters in the embedding layer. On a 13.2M model, that's ~10% of total params going to vocabulary representation instead of reasoning depth.

**Comparison to BPE:** BPE models use 32,000-50,000 token vocabularies. 4096 is still 8-12x smaller. The embedding cost is a fraction of what BPE models pay.

**Sequence length:** Dramatically shorter than single-byte-only with spelling. A sentence that would be 80 bytes with COIN-spelled roots becomes ~20 tokens with 4096 vocab.

**Adjacency noise:** Eliminated. Every token is atomic. The model sees token IDs, not byte values. No internal byte-to-byte adjacency to create false patterns.

## Open Questions

1. What is the optimal vocabulary size? 4096 is triple hex. But 2048 or 8192 might be better. The right number depends on how many concepts need atomic representation.

2. How does the embedding cost trade off against context window efficiency? At what point does the embedding overhead exceed the compute savings from shorter sequences?

3. Does the model need to see individual letters at all? If every root has its own token, letter-level tokens might only be needed for COIN (truly novel words).

4. How does this interact with the SKIP routing to Mathlete? SKIP regions contain tokens from the math vocabulary — do those share the same 4096 space or are they a separate vocabulary?

5. Is this testable as a Project Theta variable? Same 8 models, same data, 256 vocab vs 4096 vocab. The difference measures the impact of vocabulary size on the scaling curve.

---

---

## ADDENDUM: Rejected (Travis Holley, April 6, 2026)

This approach solves the wrong problem. Giving roots their own token IDs lets the model memorize numbers. Spelling roots letter by letter forces the model to LEARN what the letter patterns mean from context. The spelling is the cipher. The model cracking the cipher is the learning.

LidiaZ 10M proved this in Experiment Alpha — it decoded "hundo" into "dog" by cracking the byte patterns across thousands of contexts. It didn't memorize a mapping. It figured out the relationship. That's the mechanism we want. Giving it a shortcut token would skip the learning that makes the model actually understand.

All roots get spelled. That's the architecture. The 256 single-byte table contains control bytes, digits, letters, punctuation, endings, affixes, and function words — the structural pieces. Every root is spelled with COIN + letters. The model earns its understanding by decoding letter patterns in context.

---

*Travis Edward Holley*
*TNT Holley, Inc.*
*April 6, 2026*
