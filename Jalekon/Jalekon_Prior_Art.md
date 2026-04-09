# Jalekon Prior Art — Historical Context and Related Work

## Languages, Systems, and Ideas That Got Here First (Partially)
## Travis Edward Holley — April 9, 2026

---

## APL — The Densest Practical Notation Ever Built

**Kenneth Iverson, 1962. Turing Award 1979.**

APL uses 80+ special graphic symbols as operators. Each symbol is a complete operation — matrix inverse is one character, transpose is one character, reduction (fold) is one character. A program that takes 50 lines in C fits in 5 characters of APL.

APL is symbolic rather than lexical — its primitives are denoted by symbols, not words. Many symbols have dual meaning depending on whether they're used monadically (one argument) or dyadically (two arguments), determined by context.

### What APL Got Right

- **Single-symbol operators.** Each character IS an operation. No multi-character keywords. This is the closest historical parallel to Jalekon's single-byte concept codes.
- **Extreme density.** More meaning per character than any other programming language.
- **Array-oriented thinking.** Operations apply to entire arrays by default — no loops needed for element-wise computation.

### What APL Got Wrong for This Purpose

- **Designed for human mathematicians.** The symbols require a special keyboard and years of training. Jalekon doesn't need to be human-writable.
- **Custom character set.** APL couldn't use standard ASCII, creating adoption barriers. Jalekon uses standard bytes.
- **No compilation path.** APL is interpreted. Jalekon compiles to native code via LLVM.

### Relevance to Jalekon

APL proved that single-symbol operators work for practical programming. It demonstrated that a dense symbolic encoding can express complex computation concisely. Jalekon takes the same principle — one symbol = one operation — but designs for machine consumption rather than human mathematicians, and uses bytes rather than special characters.

---

## Forth — Zero Syntax, Pure Stack

**Charles Moore, 1970.**

Forth is a stack-based, concatenative language using Reverse Polish Notation (RPN). It has effectively zero syntax — all expressions are sequences of "words" that push values onto or manipulate a stack. No parentheses, no operator precedence, no parsing ambiguity.

```forth
: FIBONACCI ( n -- n )
  DUP 1 <= IF DROP 1 ELSE
    DUP 1- RECURSE SWAP 2- RECURSE +
  THEN ;
```

### What Forth Got Right

- **Minimal implementation.** Forth can be implemented in a few hundred lines of assembly. It runs on 8-bit microcontrollers.
- **Stack execution matches byte-level processing.** Push a value, push an operation, execute. No parsing required.
- **Extensible by composition.** New words are defined in terms of existing words. The language grows by composition, not by new syntax.
- **Real-time capable.** Used in embedded systems, boot loaders, spacecraft (Philae lander).

### What Forth Got Wrong for This Purpose

- **Designed for human tinkerers.** The stack-manipulation thinking style is notoriously difficult for humans. Irrelevant for AI-written code.
- **No type system.** Everything is a cell on the stack. Jalekon needs types for compilation to native code.
- **Postfix notation.** RPN puts the operator after the operands. Prefix notation (Mathlete's approach) is better for predictive models because the operator arrives first, telling the model how many operands to expect.

### Relevance to Jalekon

Forth proved that a programming language can have essentially no syntax and still be Turing-complete and practical. A Forth compiler is tiny — orders of magnitude smaller than GCC or LLVM. If Jalekon ever needs a minimal bootstrap compiler, Forth's architecture is the template for "how small can a language implementation be?"

---

## Lua — The Minimum Viable VM

**Roberto Ierusalimschy, PUC-Rio, 1993.**

Lua's bytecode VM is less than 6,000 lines of C with zero external dependencies. The entire VM binary is ~200KB. It compiles source to bytecode in a single pass, then interprets the bytecode.

### What Lua Got Right

- **Designed for embedding.** Lua was built to be embedded inside other programs (game engines, network equipment, IoT devices). Its C API is simple and clean.
- **Minimal size, no dependencies.** 200KB VM, no libc extensions, no external libraries. Runs anywhere C compiles.
- **Bytecode compilation.** Single-pass source → bytecode → interpretation. Separates parsing from execution.
- **Hybrid stack/register VM.** Modern Lua uses a register-based VM for efficiency — fewer instructions than pure stack machines.

### Relevance to Jalekon

Lua is the proof that a complete, practical programming language can have a sub-10,000-line implementation. If Jalekon's first runtime target is a custom bytecode VM (before LLVM integration), Lua's architecture is the reference for "how to build a minimal VM right."

---

## Factor — Modern Concatenative Programming

**Slava Pestov, 2003.**

Factor is a modern stack-based language inspired by Forth and Joy. It adds quotations (anonymous functions), combinators (higher-order stack operators), and a proper type system while keeping the concatenative paradigm.

### Relevance to Jalekon

Factor demonstrates that stack-based languages can be both minimal and modern — garbage collection, dynamic typing, macros, and a rich standard library on top of a concatenative core. If Jalekon's execution model is stack-based, Factor shows how to add modern features without abandoning the simplicity.

---

## WebAssembly — Portable Bytecode for the Modern Web

**W3C, 2017. Major updates through 2025.**

WebAssembly (WASM) is a portable binary instruction format designed for near-native performance. It's a stack-based virtual machine with a compact binary encoding.

### Current State (2025-2026)

- **WasmGC** (baseline support Dec 2024): Garbage collection primitives enabling efficient compilation of Java, C#, Kotlin, Dart, Go, Python
- **WASM 3.0** (released Sept 2025): 64-bit address space, exception handling, GC types
- **WASI 0.3** (expected H1 2025): Native async + Component Model integration
- **~40 programming languages** can target WASM
- Supported in all major browsers + server runtimes (Wasmtime, Wasmer)

### Relevance to Jalekon

WASM is one of Jalekon's compilation targets. The LLVM backend handles WASM emission via `wasm32-unknown-unknown`. WASM's Component Model may also provide a mechanism for Jalekon modules to interoperate with code written in other languages in the browser.

The more interesting parallel: WASM itself is a bytecode-level language designed for machine consumption, not human authoring. Jalekon and WASM share the design philosophy of "humans don't write this — tools do." The difference is that Jalekon operates at the concept level (programming semantics) while WASM operates at the instruction level (machine operations).

---

## Blissymbolics — Ideographic Programming's Ancestor

**Charles K. Bliss, 1949.**

Bliss built a universal concept-encoding system with ~100 base symbols composing into ~900 characters composing into 5,000+ words. No phonetic layer. Language-independent. Each symbol represents a concept directly.

### Relevance to Jalekon

Jalekon's byte codes are programming ideograms — each byte represents a programming concept independent of any language's syntax. `KW_FUNC` IS "function definition" the way a Bliss symbol IS "house" or "water." The parallel is exact. Bliss designed for human eyes (2D spatial composition). Jalekon designs for machine processing (1D byte stream). Same principle, different audience.

---

## Emerging AI-First Languages

### Synapse (2025)

AI-first language using Abstract Syntax Graph (ASG) as the canonical representation instead of text. Focuses on formal code generation and AI-assisted transformations. The ASG is the source of truth — text rendering is a view.

### Klar (2025)

Designed specifically for AI code generation. Emphasizes machine-writable, human-inspectable source.

### Relevance to Jalekon

These represent the same insight arriving from different directions: traditional programming languages were designed for humans, and AI needs something different. Jalekon predates both in concept (March 20, 2026) and goes further — not just "AI-friendly" syntax but a complete byte-level encoding where each byte IS a concept, embedded in a unified encoding system that also handles natural language, math, vision, and audio.

---

## Summary: What Each System Contributed

| System | Key Insight for Jalekon |
|--------|------------------------|
| APL | Single-symbol operators work for practical programming |
| Forth | A language can have zero syntax and still be complete |
| Lua | A complete VM can be <6,000 lines of C |
| Factor | Stack-based + modern features is possible |
| WebAssembly | Bytecode-level languages designed for tools, not humans |
| Blissymbolics | Concept-level ideographic encoding independent of language |
| Synapse/Klar | The industry is starting to see that AI needs its own languages |

---

*Travis Edward Holley*
*April 9, 2026*
