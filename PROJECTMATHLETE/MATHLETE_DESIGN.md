# Project Mathlete — Design Document

## A Model Trained Only on Math

**Author:** Travis Edward Holley
**Architecture:** Claude (Anthropic)
**Date:** April 6, 2026
**Status:** Design phase — table structure under discussion

---

## Concept

A model that takes equations with variables and produces answers. Trained exclusively on mathematics. No natural language. No reasoning about reasoning. Pure math.

---

## The Core Question: How Do You Write Every Math Calculation as a Single Line?

### Prior Art — This Has Been Solved

1. **Polish Notation** (Jan Lukasiewicz, 1924) — Prefix notation. Every expression is a single unambiguous sequence. No parentheses needed. `(2 + 3) * 4` becomes `mul add 2 3 4`. 101 years old.

2. **Reverse Polish Notation / RPN** (Hamblin, 1957) — Postfix. Same idea, reversed. `2 3 + 4 *`. HP calculators used this for decades. Forth programming language is built on it.

3. **Lambda Calculus** (Alonzo Church, 1930s) — Proves ALL computable mathematics can be expressed as single-line expressions. This is the theoretical proof that linearization works for everything computable.

4. **APL** (Kenneth Iverson, 1962) — The densest practical math notation ever built. Single characters for operations that take paragraphs in standard notation. Matrix inverse is one character. Won the Turing Award.

5. **Wolfram Language** (Stephen Wolfram, 1988) — Everything is M-expressions. `Integrate[x^2, {x, 0, 1}]` — single line, any math.

### What Nobody Has Done

Encode math operations as concept bytes for a predictive model. The prior art linearizes math for humans or for stack-based computers. Nobody has built a byte-level math vocabulary optimized for a transformer's left-to-right prediction.

---

## Why Prefix Notation Is Perfect for Predictive Modeling

Same reason Zamenhof's suffix-after-root structure works for JalekCore — the OPERATOR arrives first and tells the model what's coming.

```
add 2 3           -> model sees "add", knows: two operands follow, result is sum
mul add 2 3 4     -> model sees "mul", knows: two operands, first is itself an expression
sin pow x 2       -> model sees "sin", knows: one operand follows
deriv x pow x 3   -> model sees "deriv", knows: variable then expression
```

Each operator byte constrains the prediction space by telling the model the ARITY — how many operands follow. This is the same information flow advantage as morphemes: the first byte narrows what can come next.

**Contrast with infix (standard math notation):**
- `2 + 3 * 4` — model sees `2`, has no idea what's coming. Sees `+`, now knows addition but doesn't know operator precedence. Sees `3`, doesn't know if this is the full second operand. Sees `*`, now must retroactively reparse. The prediction space stays wide throughout.

**Prefix eliminates ambiguity at every position.** The model always knows how many operands remain. The prediction space narrows with every byte. Loss drops faster.

---

## Operator Categories — Known Coverage

| Category | Operations | Arity | Byte Count |
|----------|-----------|-------|------------|
| Arithmetic | add, sub, mul, div, mod, pow, neg, abs, floor, ceil, round | 2,2,2,2,2,2,1,1,1,1,1 | 11 |
| Comparison | eq, neq, gt, lt, gte, lte | 2 each | 6 |
| Algebra | solve, factor, expand, simplify, substitute | 1-2 | 5 |
| Calculus | deriv, integral, limit, sum, product, partial_deriv | 2-3 | 6 |
| Trigonometry | sin, cos, tan, asin, acos, atan, sinh, cosh, tanh | 1 each | 9 |
| Exponential/Log | exp, ln, log, log2, log10, sqrt, cbrt, root | 1-2 | 8 |
| Logic | and, or, not, xor, implies, iff | 1-2 | 6 |
| Set Theory | union, intersect, diff, member, subset, superset, card | 1-2 | 7 |
| Linear Algebra | dot, cross, transpose, det, inv, eigenval, eigenvec, trace, rank, norm | 1-2 | 10 |
| Statistics | mean, median, mode, stddev, var, cov, corr, prob, expect, permute, choose | 1-2 | 11 |
| Constants | pi, e, i, inf, neg_inf, nan | 0 (values) | 6 |
| **TOTAL KNOWN** | | | **~85 operators + 6 constants** |

### Gaps — What Needs Research

- Tensor operations (contraction, outer product, trace over specific indices)
- Number theory (gcd, lcm, prime, factorial, fibonacci, binomial)
- Combinatorics (permutations, combinations, partition, derangement)
- Topology / abstract algebra (group operations, ring operations, field operations)
- Complex number operations (conjugate, modulus, argument, real, imag)
- Differential equations (ode, pde, boundary conditions)
- Discrete math (graph operations, recurrence relations)
- Probability distributions (normal, binomial, poisson, uniform — as operators or as constants?)
- **Minimal complete operator set** — what is the SMALLEST set that covers all of mathematics? Has anyone formally defined this?

---

## Control Codes — Mapping to Existing JalekCore Infrastructure

### Existing Control Codes That Apply Directly

| Byte | Name | Math Usage |
|------|------|-----------|
| 0x00 | END | End of problem/answer |
| 0x01 | BOUNDARY | Separate components within an expression (e.g., variable name boundary) |
| 0x02 | SPACE | Separate tokens (operator from operands) |
| 0x05 | Q/A | Equation -> Answer transition. The model sees the equation, Q/A byte, then generates the answer. Perfect. |
| 0x0A-0x13 | Digits 0-9 | Numeric values |
| 0x14 | Decimal point | Decimal numbers |
| 0x15-0x34 | Letters a-z + extras | Variable names |

### Potential New Control Codes

| Proposed | Purpose | Rationale |
|----------|---------|-----------|
| VAR | "Variable follows" | Like NAME for proper nouns. Tells the model the next letter(s) are a variable, not a spelled word. Model learns to treat VAR-tagged bytes as unknowns to solve for. |
| VEC_START | Begin vector/matrix | Brackets the start of a multi-element structure in the flat byte stream. |
| VEC_END | End vector/matrix | Closes the structure. Model knows all elements between VEC_START and VEC_END form one object. |
| DIM | Dimension separator | Within a matrix, separates rows. `VEC_START 1 2 3 DIM 4 5 6 VEC_END` = 2x3 matrix. |

### Open Questions on Control Codes

1. Do we need VEC_START/VEC_END, or can vectors just be expressed as nested prefix operations? `vec 3 1 2 3` (vector of length 3 containing 1, 2, 3) — arity-first might eliminate the need for brackets entirely.

2. Does VAR need to be a control code, or can variables just be letters? If the model only ever sees math, every letter IS a variable — no ambiguity with words.

3. Should negative numbers use `neg` operator (`neg 5`) or a control code (`NEG_SIGN 5`)? Prefix `neg` is cleaner — treats negation as what it is, a unary operation.

4. How to handle subscripts/superscripts in variable names? `x_1`, `x_2`, `a_ij` — BOUNDARY between letter and subscript index?

---

## Training Data Format

Each training example is one line:

```
[equation in prefix bytes] Q/A [answer in prefix bytes] END
```

### Examples (conceptual, not byte-encoded yet)

**Arithmetic:**
```
add 2 3 Q/A 5 END
mul add 2 3 4 Q/A 20 END
div sub 10 4 2 Q/A 3 END
```

**Algebra with variables:**
```
solve eq add mul 2 VAR x 3 11 VAR x Q/A eq VAR x 4 END
```
(Solve: 2x + 3 = 11, x = ?)

**Calculus:**
```
deriv VAR x pow VAR x 3 Q/A mul 3 pow VAR x 2 END
```
(d/dx of x^3 = 3x^2)

**Linear algebra:**
```
det VEC_START 1 2 DIM 3 4 VEC_END Q/A neg 2 END
```
(determinant of [[1,2],[3,4]] = -2)

**Trigonometry:**
```
sin div pi 2 Q/A 1 END
```
(sin(pi/2) = 1)

---

## Architecture Questions

1. **Model size:** Mathlete is a specialist. How small can it be? If concept bytes make 13.2M viable for Esperanto reasoning, could Mathlete work at 3-5M?

2. **Relationship to JalekCore weight classes:** Is Mathlete a Jalekon package (domain table swap on the Lightweight), or is it a standalone model with its own table?

3. **Curriculum:** Does Mathlete need curriculum training (arithmetic -> algebra -> calculus), or can it learn all operations simultaneously because they're all prefix byte sequences?

4. **Composition:** Can Mathlete be chained with JalekCore? JalekCore extracts the math problem from natural language, Mathlete solves it, JalekCore formats the answer.

---

## Research Needed

1. **Minimal complete operator set** — formal enumeration of ALL mathematical operations, grouped by category, with arity. Goal: complete byte table with zero gaps.

2. **Existing math-as-linear-notation systems** — deep dive into APL, J, K, Wolfram, and any academic work on minimal math encoding.

3. **Training data sources** — where to get millions of equation/answer pairs across all math domains. Synthetic generation? Existing datasets?

4. **Representation of proofs** — can multi-step derivations be expressed as byte chains? Each step is a transformation. The chain is the proof.

---

*Travis Edward Holley*
*April 6, 2026*
