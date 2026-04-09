# Jalekon Open Questions — What Changed Since March 29

## Discussion Starters, Not Decisions
## Travis Edward Holley — April 9, 2026

---

## Context

The Jalekon specification was written March 29, 2026. Between then and April 9, several major discoveries changed the foundation:

| Date | Discovery | Impact on Jalekon |
|------|-----------|------------------|
| April 6 | Byte adjacency noise | Multi-byte codes create false patterns |
| April 6 | Single-byte-only decision | 256 entries max, everything else spelled |
| April 6 | COIN as universal root marker | Concept boundaries explicitly marked |
| April 7 | Concept bytes are ideograms | Bytes represent concepts, not encodings |
| April 7 | 3D encoding idea → 4D evolution | Positional bytes encode spatial/temporal relationships |
| April 9 | SuperZ 4D positional system | 24 positional bytes replace all grammar AND derivation |
| April 9 | The collapse: 59 base + 24 positional = everything | System dramatically smaller than expected |

The v0 Jalekon byte table was designed before these discoveries. The questions below flag where the new understanding might require changes. **These are for discussion, not implementation.**

---

## Question 1: Does the JALEKON Toggle Change What the Positional Bytes Mean?

The JALEKON byte (0x07) toggles the table from natural language to programming mode. The same 256 values switch context.

In natural language mode, POS_FRONT means "forward, acts, causes." In programming mode, what does it mean?

**Possible mapping:**

| Positional Byte | Language Meaning | Programming Meaning? |
|----------------|-----------------|---------------------|
| POS_CENTER | occupies space, noun | variable declaration (thing in memory) |
| POS_TOP | above, modifies | type annotation (modifies a value) |
| POS_BESIDE | alongside, manner | comment (alongside code) |
| POS_FRONT | forward, acts | function call (action) |
| POS_BEHIND | behind, receives | return value (result of action) |
| POS_INSIDE | contained within | scope / block body |
| POS_OUTSIDE | surrounds, contains | module / namespace |
| POS_OVERLAP | shared space, group | array / collection |
| POS_BETWEEN | in the middle | operator (between operands) |
| T_BEFORE | past | previous state (before assignment) |
| T_AFTER | future | next state (after assignment) |
| T_DURING | present, ongoing | loop body (while executing) |
| T_GROW | increasing, becoming | increment / append |
| T_DECAY | diminishing, ending | decrement / delete |
| POS_MIRROR | opposite, reversal | negation / NOT |
| POS_VOID | absence, negation | null / undefined |

If this mapping works, then the same 24 positional bytes handle BOTH natural language grammar AND programming structure. The model learns the toggle — same geometry, different domain.

---

## Question 2: Does COIN Apply Inside Jalekon Mode?

In natural language mode, COIN marks "concept incoming" before every root. In programming mode:

- Should COIN precede every identifier? `COIN [fibonacci]`
- Should COIN precede every keyword? Or are keywords already unambiguous single bytes?
- If identifiers are COIN-spelled (letter by letter), the model learns identifier patterns the same way it learns root patterns in language mode.

**Argument for COIN in code:** Identifier boundaries are explicitly marked. The model knows "this is a name" vs "this is a keyword." Same tent-pole architecture as language mode.

**Argument against:** Keywords are single bytes — no ambiguity. COIN might only be needed for identifiers that switch back to the Jalek table for semantic decomposition.

---

## Question 3: Does the Adjacency Noise Finding Affect the Two-Byte Tier?

The v0 table allocates 61,504 two-byte codes for stdlib modules, dunder methods, framework patterns, etc. But the adjacency noise discovery on April 6 found that multi-byte codes create false patterns.

**Options:**
1. **Eliminate the two-byte tier entirely.** Everything beyond 248 single-byte codes gets COIN-spelled. Consistent with the language-mode decision.
2. **Keep the two-byte tier but only in Jalekon mode.** Programming concepts might be different enough from natural language that the noise is tolerable.
3. **The toggle itself might solve the problem.** The JALEKON byte acts as a context boundary. Multi-byte codes within a toggled region don't create cross-context adjacency noise because the model knows it's in a different mode.

This needs testing, not a design decision.

---

## Question 4: Does Prefix Notation (from Mathlete) Replace Infix Operators?

Mathlete uses prefix notation: `add 2 3` instead of `2 + 3`. Prefix tells the model the arity (how many operands) at the first byte, narrowing prediction space.

The v0 Jalekon table uses infix operators (OP_ADD between operands). Should Jalekon adopt prefix notation for consistency with Mathlete?

**Prefix version of `x = a + b * c`:**
```
OP_ASSIGN x OP_ADD a OP_MUL b c
```

**Infix version (current v0):**
```
x OP_ASSIGN a OP_ADD b OP_MUL c
```

**Argument for prefix:** Consistent with Mathlete. Arity-first narrows prediction space. No operator precedence ambiguity. The model uses the same pattern for math and code.

**Argument for infix:** Programmers think in infix. Decompilation views are more natural. The AI might learn either way.

**Argument for: let the model decide.** Train on both encodings, measure which produces lower loss. Empirical question.

---

## Question 5: How Does SKIP Routing Work with Jalekon?

SKIP (0x06) creates attention-masked regions. The model can't see SKIP content — only the orchestrator (KlaraZ) reads it.

When the model is in Jalekon mode and encounters a math expression, does it:

1. Stay in Jalekon mode and use Jalekon's math operators directly?
2. Emit a SKIP region that routes to Mathlete for computation?
3. Both — simple math inline, complex math routed?

This connects to the three-model architecture (translator → descriptor → reasoning engine). If math is a separate specialist, SKIP routing makes sense. If the programming model handles its own math, inlining makes sense.

---

## Question 6: What Happens at the Toggle Boundary?

When the byte stream contains mixed prose and code:

```
[natural language] JALEKON [code] JALEKON [natural language]
```

How does the model handle the transition? Specifically:

- Do identifiers in code mode decompose through the Jalek language table (LIT_IDENT_FOLLOWS switches context momentarily)?
- Do string literals in code mode use language-mode encoding (LIT_STR_FOLLOWS)?
- Can code comments toggle back to language mode, or do they stay in code mode?
- Can Jalekon regions nest (code that generates code)?

The March 29 spec used JALEKON_START/JALEKON_END as paired delimiters. The toggle approach (single JALEKON byte flips state) is simpler but requires the model to track which mode it's in. The model should learn this from patterns — but it's worth verifying.

---

## Question 7: Does the SuperZ Positional System Subsume Jalekon's Keyword Bytes?

The most radical question. Consider:

| Programming Concept | Current v0 | SuperZ Alternative |
|-------------------|------------|-------------------|
| `if` (conditional) | KW_IF (0x40) | [condition] POS_FRONT [consequence] |
| `for` (iteration) | KW_FOR (0x43) | [collection] T_DURING [body] |
| `return` (function return) | KW_RETURN (0x48) | [value] POS_BEHIND [function] |
| `class` (type definition) | KW_CLASS (0x61) | [concept] POS_OUTSIDE [methods] |
| `import` (module) | KW_IMPORT (0x65) | [module] POS_INSIDE [current_scope] |

If programming constructs can be expressed as root + positional bytes, then Jalekon doesn't need 218 dedicated keyword bytes. It needs roots for programming concepts and the same 24 positional bytes that handle everything else.

**This would mean:** The same 59 base + 24 positional byte system handles natural language, programming, math, vision, AND audio. One encoding for everything.

**Counter-argument:** Dedicated keyword bytes might give the model cleaner signal. A single byte `KW_IF` is unambiguous. A positional expression `[test] POS_FRONT [then]` requires the model to infer the conditional pattern from position.

**The answer is empirical.** Train models on both encodings, measure loss. The data will tell us which the model finds easier to learn.

---

## Question 8: Sequence Order as a Fifth Dimension

**Discovered April 9, 2026 — Travis Edward Holley**

The 4D positional system (composition, hierarchy, causation, time) encodes WHAT the relationship between concepts is. But the ORDER of bytes in the sequence — which comes before and which comes after — carries additional information that the positional bytes themselves don't encode.

A positional byte BEFORE a root has a different meaning than the same byte AFTER a root:

| Encoding | Meaning | Zamenhof Equivalent |
|----------|---------|-------------------|
| `POS_MIRROR [root]` | Opposite of what's coming (prefix) | mal- (prefix) |
| `[root] POS_MIRROR` | Reversal of that root (suffix) | Different operation |
| `POS_FAR [root]` | In the context of largeness | Prefix modifier |
| `[root] POS_FAR` | Made large (augmentative) | -eg- (suffix) |
| `POS_VOID [root]` | Without what follows | sen- (prefix) |
| `[root] POS_VOID` | Absence of that root | Different operation |

**This doubles the positional vocabulary without adding bytes:**

24 positional bytes × 2 sequence positions = **48 distinct grammatical operations from 24 bytes.**

No stacking needed. No doubling up. The sequence IS the grammar. The model already captures this natively — RoPE encodes position, attention tracks what came before vs after. The 1D stream isn't just carrying 4D structure. The ordering itself is a fifth channel that was always there.

**Two conditions must hold for this to work:**

1. **Clean pattern.** The before/after distinction must map to consistently distinct, learnable meanings for every positional byte. Not arbitrary — the semantic logic must be generalizable. If `POS_X [root]` and `[root] POS_X` don't carry a clean, consistent distinction across all roots, the model can't learn the pattern.

2. **Decodable.** The decoder must unambiguously reconstruct the original language from the byte stream. If the same byte means different things based on position, the decoder needs to read the sequence order to pick the correct output word. This is solvable — the decoder reads left to right just like the model — but the mapping table needs to encode both directions.

**Implication:** The SuperZ table may need revision. Every prefix/suffix pair that was mapped to stacked positional bytes (like POS_TOP + POS_TOP = leader) might collapse to a single byte in the correct sequence position. The table gets simpler, the byte budget gets cheaper, and the model gets a cleaner pattern to learn.

**Status:** Insight documented. Requires design work to map all 24 positional bytes to their before/after meanings, then validation that the mappings are clean and decodable. No implementation until the mappings are agreed on.

---

## Summary

| Question | Core Issue | Resolution Method |
|----------|-----------|-------------------|
| 1. Positional bytes in code mode | Same geometry, different semantics? | Design discussion |
| 2. COIN in code mode | Identifier boundaries | Design discussion |
| 3. Two-byte tier and adjacency noise | Consistency with language-mode decision | Testing required |
| 4. Prefix vs infix operators | Consistency with Mathlete | Testing required |
| 5. SKIP routing for math | Architecture decision | Design discussion |
| 6. Toggle boundary behavior | Mixed prose/code handling | Design discussion |
| 7. SuperZ subsumes keywords | One encoding for everything? | Testing required |
| 8. Sequence order as 5th dimension | Before/after root doubles positional vocabulary | Design + testing |

**None of these should be resolved by argument alone. Where testing is indicated, test. Where discussion is indicated, discuss. No unilateral changes.**

---

*Travis Edward Holley*
*April 9, 2026*
