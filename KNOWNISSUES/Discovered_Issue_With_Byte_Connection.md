# Discovered Issue: Byte Connection Patterns

**Discovered:** April 6, 2026
**Discovered by:** Travis Holley
**Origin:** Re-examination of LidiaZ 10M results from Experiment Alpha

---

## What the Model Actually Sees

A concept byte model does not see words, morphemes, or language. It sees numbers in sequence. It uses math to find patterns in how those numbers relate to each other.

The model learns three connection patterns:

1. **byte byte** — two bytes with nothing between them. The model learns these are part of the same thing.
2. **byte BOUNDARY byte** — two bytes separated by 0x01. The model learns these compose into one word.
3. **byte SPACE byte** — two bytes separated by 0x02. The model learns these are separate words that relate in context.

These three patterns are the entire grammar of the byte stream. The control bytes define what kind of relationship exists between the bytes on either side. The model decoded this grammar on its own — nobody taught it what BOUNDARY or SPACE means. It figured out the structure from the data.

## What LidiaZ 10M Proved

In Experiment Alpha, the LidiaZ 10M model was trained on parallel Esperanto-English data encoded as concept bytes. The data was dirty. The English vocabulary was missing basic words including "I" and "a". The byte codes were assigned alphabetically with no semantic logic.

The model cracked it anyway.

- "la hundo estas bona" → produced "dog"
- "mi amas vin" → produced "love"
- "la kato dormas sur la lito" → produced "cat", "on", "bed"
- "la suno brilas" → produced "sun"
- "li" (he) → ranked #1 prediction with 52.75% confidence

It did this by learning the byte connection patterns. Which bytes appear together across BOUNDARY. Which bytes appear in the same positions across SPACE. Which bytes on the Esperanto side of the Q/A separator co-occur with which bytes on the English side. The model used math to reverse-engineer the cipher of byte relationships.

We called this experiment a failure because the translations were imprecise. We were wrong about what we were looking at. The model was not failing to translate — it was succeeding at decoding the pattern structure of the byte stream. It figured out the relationship types, identified the concept mappings, and produced the correct core concepts despite catastrophically bad input data.

## The Discovery

The model applies the same pattern-finding math to ALL byte adjacency — including adjacency that is an artifact of the encoding, not a real relationship.

Multi-byte codes (two or three bytes forming one concept) create byte-to-byte adjacency with no separator. The model treats this the same way it treats any other adjacency: it looks for a pattern. If two byte values happen to appear next to each other frequently because they form a common multi-byte code, the model may learn a relationship between those byte VALUES that has nothing to do with the CONCEPTS they encode.

The byte assignment order (alphabetical) compounds this. Concepts that are alphabetically similar get numerically similar byte codes. The model finds numerical proximity patterns that look like semantic relationships but are actually just alphabetical coincidence.

This is an uncontrolled variable in every model trained on concept byte data.

## The Connection to Hallucination

Large language models hallucinate because they learned patterns from training data that aren't true in the real world. The patterns were in the data, so the model learned them, but they don't reflect reality.

Concept byte models face the same risk from a different source. The patterns from arbitrary byte assignment are in the encoded data. The model will learn them. They don't reflect semantic reality. The model has no way to tell the difference.

## The Solution

Eliminate multi-byte codes. Single-byte vocabulary only. 256 entries.

Every byte is one concept. Every relationship between bytes is defined by a control byte. The model never sees unexplained adjacency. Every pattern it finds is real because every connection is labeled.

Everything beyond the 256 single-byte concepts gets spelled letter by letter.

---

*Travis Edward Holley*
*April 6, 2026*
