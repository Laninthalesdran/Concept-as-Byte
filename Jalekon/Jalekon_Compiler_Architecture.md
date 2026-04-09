# Jalekon Compiler Architecture

## How to Build a Compiler for an AI-Native Programming Language
## Travis Edward Holley — April 9, 2026

---

## Why Jalekon Needs a Compiler

Jalekon is not an encoding layer. It is a programming language. Programs written in Jalekon must compile to native executables that run on real hardware. The AI writes Jalekon bytecodes. The compiler turns them into machine code. No Python interpreter, no JVM, no runtime dependency on any other language.

---

## The Classic Compiler Pipeline

Every compiler follows the same basic architecture, separated into frontend and backend:

```
Source Code (Jalekon bytes)
       |
  [1. LEXER] .......... Bytes → Tokens
       |
  [2. PARSER] ......... Tokens → AST (Abstract Syntax Tree)
       |
  [3. SEMANTIC ANALYSIS] ... Type checking, scope resolution, validation
       |
  [4. IR GENERATION] .. AST → Intermediate Representation
       |
  [5. OPTIMIZER] ...... Transform IR for efficiency
       |
  [6. CODE GENERATOR] . IR → Target machine code
       |
  Native Executable
```

### What Each Stage Does

| Stage | Input | Output | Job |
|-------|-------|--------|-----|
| Lexer | Raw bytes | Token stream | Identify boundaries between meaningful units |
| Parser | Token stream | AST | Validate structure, build tree representation |
| Semantic Analysis | AST | Annotated AST | Check types, resolve scopes, catch errors |
| IR Generation | Annotated AST | LLVM IR | Translate to platform-independent form |
| Optimizer | LLVM IR | Optimized IR | Constant folding, dead code elimination, inlining |
| Code Generator | Optimized IR | Machine code | Target-specific instruction selection |

### Jalekon's Advantage: Lexing Is Trivial

In most compilers, the lexer is complex — it must handle whitespace, comments, string escaping, number parsing, keyword identification, and Unicode. Jalekon's source is already byte-level. Every byte IS a token. The lexer is essentially a table lookup:

```
Read byte → Look up in Jalekon table → Emit token
```

No whitespace parsing. No string escaping. No ambiguity. The most complex part of a traditional compiler frontend is nearly free for Jalekon.

---

## LLVM as Backend

LLVM (Low Level Virtual Machine) is the proven backend for multi-platform compilation. Rust, Swift, Clang (C/C++), and Kotlin/Native all use LLVM. One frontend emitting LLVM IR gets access to:

- Decades of optimization research (constant folding, loop unrolling, vectorization, register allocation)
- Every major target architecture (x86-64, ARM64, RISC-V, WebAssembly)
- Every major OS (Windows PE, macOS Mach-O, Linux ELF)
- Production-quality code generation

### LLVM IR

LLVM's Intermediate Representation is a typed, low-level language in Static Single Assignment (SSA) form:

```llvm
define i32 @add(i32 %a, i32 %b) {
  %result = add i32 %a, %b
  ret i32 %result
}
```

Key properties:
- Every variable assigned exactly once (SSA form enables powerful optimizations)
- Explicitly typed (i32, i64, float, double, pointers)
- Structured as Module → Functions → Basic Blocks → Instructions
- Can be in-memory, on-disk bitcode, or human-readable text

### The Jalekon → LLVM Pipeline

```
Jalekon Bytecodes
       |
  [Jalekon Frontend]
       |
  LLVM IR (.ll / .bc)
       |
  [LLVM Optimizer] — opt
       |
  [LLVM Backend] — llc
  /    |    |    \     \
x86  ARM64 WASM  RISCV  ...
 |     |     |     |
PE  Mach-O  .wasm  ELF
 |     |     |      |
Win  macOS  Browser  Linux
```

### How Other Languages Use LLVM

| Language | Frontend Written In | LLVM Usage | Notes |
|----------|-------------------|------------|-------|
| Rust | Rust (self-hosted) | Primary backend | Gold standard for LLVM multi-platform |
| Swift | C++ | Primary backend | Apple-focused but expanding |
| Clang | C++ | C/C++/ObjC frontend | Reference LLVM frontend |
| Zig | Zig (self-hosted) | Optional backend | Also has custom backend for debug builds |
| Kotlin/Native | Kotlin | One of three backends | Also targets JVM and WASM separately |

---

## Platform Targets

| Platform | LLVM Target Triple | Output | Distribution |
|----------|-------------------|--------|-------------|
| Windows | `x86_64-pc-windows-msvc` | PE .exe / .dll | Optional Authenticode signing |
| macOS Intel | `x86_64-apple-macosx` | Mach-O | Notarization required |
| macOS Apple Silicon | `arm64-apple-macosx` | Mach-O | Universal Binaries via `lipo` |
| Linux x86 | `x86_64-unknown-linux-gnu` | ELF | No signing required |
| Linux ARM | `aarch64-unknown-linux-gnu` | ELF | Raspberry Pi, ARM servers |
| Android | `aarch64-linux-android` | ELF .so | JNI wrapper + APK signing |
| iOS | `arm64-apple-ios` | Mach-O | AOT only — NO JIT allowed |
| HarmonyOS NEXT | `aarch64-unknown-linux-*` | ELF .so | N-API/ArkTS wrapper — NOT Android |
| WebAssembly | `wasm32-unknown-unknown` | .wasm | JS glue for DOM; WASI for server |

### Critical Platform Constraints

- **iOS prohibits JIT.** All code must be ahead-of-time compiled. If the Jalekon runtime includes any JIT, it must be disabled for iOS.
- **HarmonyOS NEXT is NOT Android.** Huawei stripped AOSP compatibility. Separate integration target.
- **WASM has no direct DOM access.** Requires JS glue or Component Model for browser interaction.
- **macOS/iOS builds require a Mac.** Apple's SDK and code signing tools are macOS-only.
- **Fire OS IS Android.** Amazon's AOSP fork runs Android APKs unchanged. No separate work needed.

---

## Bootstrapping Strategy

### The Bootstrap Problem

You need a compiler to compile the compiler. Solution: write the first Jalekon compiler in another language, then self-host later.

### Recommended Path

**Phase 0: Prototype compiler in Python**
- Python has AST manipulation libraries, is fast to iterate in
- Emit LLVM IR text format directly (no LLVM C API needed initially)
- Target: compile a subset of Jalekon (arithmetic, variables, functions, control flow)
- Goal: prove the pipeline works end to end

**Phase 1: Production compiler in Rust**
- Rust has first-class LLVM bindings (`inkwell` or `llvm-sys` crates)
- Memory-safe, no GC, produces small binaries
- The compiler itself is a native executable
- Target: full Jalekon language support

**Phase 2: Self-hosting (optional, long-term)**
- Write the Jalekon compiler in Jalekon
- Compile it with the Rust-based compiler
- Validate: self-compiled compiler produces identical output
- The language compiles itself — proof of completeness

### Minimum Viable Compiler

The smallest useful Jalekon compiler supports:
1. Integer and float arithmetic
2. Variables (mutable and immutable)
3. Functions with parameters and return values
4. Control flow (if/else, for, while)
5. Basic I/O (print)
6. One target (Linux x86_64 ELF)

Everything else (classes, generics, concurrency, stdlib, cross-platform) is incremental.

---

## Runtime Design

The Jalekon runtime provides services that LLVM IR cannot express alone:

### Memory Management Options

| Strategy | Pros | Cons | Used By |
|----------|------|------|---------|
| Manual (malloc/free) | Smallest binaries, maximum control | Error-prone, use-after-free | C |
| Reference Counting (ARC) | Deterministic, no pauses | Cycle leaks without cycle collector | Swift, Objective-C |
| Tracing GC | Simple for programmers | Stop-the-world pauses, large runtime | Go, Java, Python |
| Ownership + Borrow Checker | No GC, no leaks, no pauses | Steep learning curve | Rust |

**Recommendation for Jalekon:** Reference counting (ARC) with a cycle collector. Rationale:
- The AI writes the code, so "steep learning curve" doesn't apply
- Deterministic cleanup is better for resource management
- Smaller runtime than tracing GC (matters for WASM and embedded)
- Swift proved ARC works at production scale

### Threading

- POSIX threads on Linux/macOS
- Win32 threads on Windows
- Web Workers for WASM (threading support maturing)
- Platform abstraction layer in the runtime

### I/O Abstraction

Standard library wraps platform-specific I/O:
- File I/O: POSIX `open`/`read`/`write` on Unix, `CreateFile`/`ReadFile` on Windows, WASI on WASM
- Network: BSD sockets on Unix, Winsock on Windows
- Console: `stdout`/`stderr` everywhere

---

## Foreign Function Interface (FFI)

Jalekon must call C functions for OS interaction. FFI handles:

- **Calling convention translation** — match C's ABI (cdecl, System V, Win64)
- **Type marshaling** — map Jalekon types to C types (int → int32_t, str → char*)
- **Symbol resolution** — find functions in shared libraries at link time or runtime

### Implementation

```
# Jalekon FFI declaration (conceptual)
KW_FUNC AM_NATIVE "write" ST_LPAREN TY_INT "fd" ST_COMMA TY_STR "buf" ST_COMMA TY_INT "len" ST_RPAREN TY_INT
```

The `AM_NATIVE` modifier marks functions as external C symbols. The compiler emits LLVM `declare` statements and the linker resolves them against system libraries.

---

## Phased Development Roadmap

### Phase 1: Proof of Concept
- Python prototype compiler
- Jalekon bytecodes → LLVM IR → Linux x86_64 ELF
- Subset: arithmetic, variables, functions, control flow, print
- Goal: "Hello World" and Fibonacci compile and run

### Phase 2: Production Compiler
- Rewrite in Rust with `inkwell` LLVM bindings
- Full Jalekon language support (types, classes, generics, error handling)
- Runtime with ARC memory management
- Targets: Linux, Windows, macOS

### Phase 3: Standard Library
- I/O, collections, math, string manipulation
- Networking, concurrency, JSON
- Platform abstraction layer

### Phase 4: Cross-Platform
- WASM target with JS glue
- Android (JNI wrapper)
- iOS (Swift wrapper, AOT only)
- HarmonyOS NEXT (N-API wrapper)

### Phase 5: Self-Hosting
- Write Jalekon compiler in Jalekon
- Prove language completeness
- AI generates its own compiler improvements

---

## Alternative Backends (If Not LLVM)

| Backend | Pros | Cons | When to Use |
|---------|------|------|-------------|
| Cranelift | Lighter, modern, Rust-native | Fewer targets, newer ecosystem | Fast JIT, WASM focus |
| QBE | Tiny, simple, educational | Limited targets, fewer optimizations | Toy/prototype compiler |
| Custom bytecode VM | Total control, minimal deps | Must write everything yourself | If native compilation not needed |
| Direct WASM emit | No LLVM dependency for web | WASM-only target | Web-only deployment |

---

## What Makes Jalekon's Compiler Unique

1. **Lexing is trivial.** Source is already bytes. No whitespace, no escaping, no Unicode normalization.
2. **Parsing is simplified.** Fixed-width opcodes with known arities. No operator precedence ambiguity (especially if prefix notation is adopted from Mathlete).
3. **Semantic analysis operates on concepts.** Type checking happens at the concept level — `TY_INT` is unambiguous across all source languages.
4. **Cross-language compilation is decoding.** The same Jalekon IR can emit Python, JavaScript, Java, or Rust through different decompilation backends.
5. **The AI optimizes its own code.** A Jalekon-trained model can reason about Jalekon programs at the concept level — suggesting optimizations that work across all target platforms.

---

*Travis Edward Holley*
*April 9, 2026*
