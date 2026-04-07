# Possible Solution: Universal COIN Byte Before Every Root

**Proposed:** April 6, 2026
**Proposed by:** Travis Holley
**Status:** Pending test — three table variants after Experiment Beta completes

---

## The Two Problems

1. **Multi-byte adjacency noise:** When two bytes form one code, the model finds patterns in their numerical adjacency that are artifacts of the encoding, not real semantics. This can cause hallucination.

2. **Spelling blinds the instrument:** Switching to single-byte-only with all roots spelled letter by letter fixes the noise — but the Layer 2 neural recorder snapshots become letter soup instead of concept-level attention maps. We lose the diagnostic tool that caught overfitting in real time on the 18.8M model.

These two problems appear to be in direct conflict. Fix one, break the other.

## The Solution: COIN Before Every Root

Use the COIN byte (0x09) as a universal root marker. Every root — whether it has a single-byte code or is spelled letter by letter — is preceded by COIN.

**Single-byte root:** COIN [root_byte] SPACE
**Spelled root:** COIN [letters] SPACE
**Root with suffix:** COIN [root_byte] [suffix_byte] [ending_byte] SPACE
**Spelled root with suffix:** COIN [letters] [suffix_byte] [ending_byte] SPACE

### What this solves

**For the model:**
- COIN = "concept incoming." The model learns that what follows COIN is a root concept, whether it's one byte or many letters.
- No multi-byte noise: single-byte roots are one byte. No internal adjacency to misinterpret.
- Spelled roots are real letter patterns. The adjacency between letters IS the signal — "h-u-n-d" is how you spell the concept.
- Every root boundary is explicitly marked. No guessing where concepts start and end.

**For the instrument:**
- Layer 2 snapshots read COIN as a concept boundary marker.
- For single-byte roots: the snapshot labels the concept by its table entry. Full concept-level readability.
- For spelled roots: the snapshot labels the concept by its letter sequence. Still readable — "hund" is clear even spelled.
- Concept-level attention tracking is preserved because COIN marks where every concept begins.
- The frequent roots (which dominate the data) get single-byte codes, so most of the attention map is concept-level. Rare spelled roots are rare — they don't cloud the picture.

**For diagnosing overfitting:**
- The 18.8M model showed overfitting via three correlated signals: eval loss rising, Layer 2 accuracy rising on fixed sentence (memorization), Layer 3 Spearman correlation pulling back toward zero (shifting from relevance to frequency).
- This diagnostic capability is preserved with COIN inclusion because concept-level attention is still readable.
- Nobody has ever watched overfitting happen at the concept level before. This solution keeps that ability intact.

## COIN's New Role

COIN was originally defined as "novel term prefix — spell letter by letter." Under this solution, its role expands:

**Old:** COIN = "unknown word follows, spelled out"
**New:** COIN = "root concept follows" — whether single-byte or spelled

This is not a contradiction. Every root IS a concept. COIN announces it. The model learns COIN as the universal concept marker. The instrument uses COIN as the universal concept boundary.

## What Needs Testing

Five table variants, same 8 model sizes, same data:

1. **COIN + spelled root** — all roots spelled letter by letter, COIN before each. No single-byte root codes at all.
2. **COIN + single-byte root** — frequent roots get single-byte codes, COIN before each. Rare roots spelled.
3. **Spelled root, no COIN** — all roots spelled, no marker. Control for whether COIN itself matters.
4. **Multi-byte, no COIN** — current Experiment Beta encoding. Baseline.
5. **COIN + multi-byte** — current multi-byte codes but COIN before every root. Tests whether COIN alone fixes the noise problem without eliminating multi-byte codes.

**What each comparison tells us:**
- 1 vs 2: Does giving frequent roots single-byte codes help or hurt when COIN is present?
- 1 vs 3: Does COIN itself matter for spelled roots?
- 2 vs 4: Does COIN + single-byte beat raw multi-byte?
- 4 vs 5: Does adding COIN to multi-byte codes fix the adjacency noise, or is eliminating multi-byte codes necessary?
- 1 vs 5: Full range — spelled with COIN vs multi-byte with COIN. Isolates the effect of code length.

## Byte Budget With COIN Inclusion

Every root costs 1 extra byte (the COIN prefix). For a sentence with 5 roots, that's 5 extra bytes. On a 20-byte sentence, that's a 25% increase. On a 40-byte sentence, 12.5%. Manageable — especially since the frequent roots are single-byte (root itself is 1 byte + COIN = 2 bytes total, versus multi-byte codes that were 2-3 bytes without COIN).

## Connection to the Cipher

The model cracks the cipher by learning byte relationship patterns. COIN marks where every root begins. The letters or single-byte code after COIN are the cipher to crack. The endings and suffixes after the root are the grammatical context. COIN gives the model an anchor point — "concept starts here, decode what follows."

LidiaZ 10M cracked the cipher without COIN markers and with dirty data. With clean data and COIN announcing every concept boundary, the model has a cleaner signal to learn from.

---

*Travis Edward Holley*
*April 6, 2026*
