# Jalekon — AI-Native Programming Language

**Author:** Travis Edward Holley
**Date:** April 9, 2026
**Patent:** U.S. Application No. 64/017,122

The first programming language designed for AI to write and compilers to execute.

---

## What This Is

Jalekon is a byte-level programming language where each byte represents a programming concept — `function definition`, `if`, `return`, `+`, `print` — not ASCII text. An AI model writes Jalekon bytecodes directly. The Jalekon compiler turns those bytes into native executables via LLVM.

This package contains the prototype compiler and design documentation.

## Quick Start

### Requirements

- **Python 3.10+** — https://python.org
- **LLVM/Clang** — https://github.com/llvm/llvm-project/releases
  - Download the installer for your platform (e.g., `LLVM-22.1.3-win64.exe`)
  - During install, check **"Add LLVM to the system PATH"**

### Run the Built-In Tests

```bash
python jalekon_compiler.py --test
```

This compiles four Jalekon programs to LLVM IR and prints the output:
1. `add(a, b)` — basic function
2. `max(a, b)` — if/else branching
3. `factorial(n)` — recursion
4. `print(add(3, 4))` — full program with main and printf

### Compile to Native Executable

```bash
# Generate LLVM IR from test (or from a .jkn file)
python jalekon_compiler.py --test > output.ll

# Compile to native executable
clang output.ll -o output.exe

# Run it
./output.exe
```

### Compile a Jalekon Byte File

```bash
python jalekon_compiler.py program.jkn -o program.ll
clang program.ll -o program.exe
./program.exe
```

## What's in This Package

| File | Description |
|------|-------------|
| `jalekon_compiler.py` | **The compiler.** Lexer + Parser + LLVM IR Generator. ~700 lines of Python. |
| `JALEKON_DESIGN.md` | Main design document — what Jalekon is and why it exists |
| `Jalekon_Byte_Table.md` | Complete v0 byte table — all 248 single-byte codes |
| `Jalekon_Byte_To_Execution.md` | Trail from byte to CPU instruction with working code at every stage |
| `Jalekon_Compiler_Architecture.md` | How compilers work, LLVM, bootstrapping strategy |
| `Jalekon_Prior_Art.md` | Historical context — APL, Forth, Lua, WebAssembly |
| `Jalekon_Open_Questions.md` | Design questions for future development |
| `test_add.ll` | Sample LLVM IR output (the `add(3,4)` program) |

## How It Works

```
Jalekon Bytes → [Lexer] → Tokens → [Parser] → AST → [IR Gen] → LLVM IR → [clang] → Native .exe
```

1. **Lexer:** Each byte is a token. Table lookup. ~40 lines.
2. **Parser:** Recursive descent. Builds an AST. ~250 lines.
3. **IR Generator:** Walks the AST, emits LLVM IR text. ~250 lines.
4. **LLVM/Clang:** Optimizes and compiles to native machine code for any platform.

## Supported Language Features (Prototype)

- Function definitions with parameters
- Integer arithmetic (`+`, `-`, `*`, `/`, `%`)
- Comparison operators (`==`, `!=`, `<`, `>`, `<=`, `>=`)
- Variables and assignment
- If/elif/else
- While loops
- Recursion
- Built-in print (via C printf)
- Integer and boolean literals

## License

CC-BY-NC-SA 4.0 for non-commercial use.
Commercial licensing: contact travis@tntholley.com

## Links

- **Patent:** U.S. Application No. 64/017,122 (filed March 25, 2026)
- **Parent Project:** [Concept-as-Byte](https://github.com/Laninthalesdran/Concept-as-Byte)
- **Preprint:** DOI 10.5281/zenodo.19390531

---

*Travis Edward Holley — April 9, 2026*
