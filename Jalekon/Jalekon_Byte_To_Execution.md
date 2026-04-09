# Jalekon: From Byte to Execution

## The Complete Trail — How a Jalekon Byte Becomes a Running Program
## Travis Edward Holley — April 9, 2026

---

## The Big Picture

A Jalekon program is a stream of bytes. Each byte is a programming concept. The compiler's job is to turn that stream of concepts into instructions a CPU can execute. Here's every step, with nothing skipped.

```
Jalekon Bytes (your program)
       |
  [1. LEXER] ............. Read bytes, identify what each one means
       |
  [2. PARSER] ............ Group them into a tree structure (like a sentence diagram)
       |
  [3. TYPE CHECKER] ...... Make sure the types make sense (no adding strings to integers)
       |
  [4. IR GENERATOR] ...... Translate the tree into LLVM's language
       |
  [5. LLVM] .............. Optimize and generate machine code
       |
  [6. LINKER] ............ Attach OS functions (print, file I/O, etc.)
       |
  Native Executable (runs on the CPU)
```

---

## The Example Program

We'll trace this simple program all the way through:

```python
def add(a, b):
    return a + b

print(add(3, 4))
```

In Jalekon bytes (after the JALEKON toggle):

```
Byte  Hex   Meaning
─────────────────────────────────────────────
0x60  KW_FUNC           "function definition"
0xFB  LIT_IDENT_FOLLOWS  "identifier coming..."
      a d d              ...the letters "add"
0x00  SPACE              end of identifier
0x13  ST_LPAREN          "("
0xFB  LIT_IDENT_FOLLOWS  "identifier coming..."
      a                  ...the letter "a"
0x00  SPACE              end of identifier
0x19  ST_COMMA           ","
0xFB  LIT_IDENT_FOLLOWS  "identifier coming..."
      b                  ...the letter "b"
0x00  SPACE              end of identifier
0x14  ST_RPAREN          ")"
0x1A  ST_COLON           ":"
0x10  ST_NEWLINE         new line
0x11  ST_INDENT          enter function body
0x48  KW_RETURN          "return"
0xFB  LIT_IDENT_FOLLOWS  "a"
0x00  SPACE
0x27  OP_ADD             "+"
0xFB  LIT_IDENT_FOLLOWS  "b"
0x00  SPACE
0x10  ST_NEWLINE         new line
0x12  ST_DEDENT          leave function body
0xA0  BI_PRINT           "print"
0x13  ST_LPAREN          "("
0xFB  LIT_IDENT_FOLLOWS  "add"
0x00  SPACE
0x13  ST_LPAREN          "("
0xF1  LIT_1... wait      nope — we need 3 and 4
```

Actually, let's simplify. The literal bytes for 3 and 4 would use LIT_INT_FOLLOWS (0xF8) because only 0, 1, 2, and -1 have dedicated single bytes. Let me use a simpler example that sticks to the single-byte literals:

```python
def add(a, b):
    return a + b
```

**Just the function definition. 21 Jalekon bytes total:**

```
Position  Hex   Token             What the compiler sees
────────────────────────────────────────────────────────────
0         0x60  KW_FUNC           Start of function definition
1         0xFB  LIT_IDENT_FOLLOWS Identifier name coming next
2-4       a,d,d (letters)         Function name: "add"
5         0x00  SPACE             End of identifier
6         0x13  ST_LPAREN         Open parameter list
7         0xFB  LIT_IDENT_FOLLOWS Parameter name coming
8         a     (letter)          Parameter name: "a"
9         0x00  SPACE             End of identifier
10        0x19  ST_COMMA          Separator
11        0xFB  LIT_IDENT_FOLLOWS Parameter name coming
12        b     (letter)          Parameter name: "b"
13        0x00  SPACE             End of identifier
14        0x14  ST_RPAREN         Close parameter list
15        0x1A  ST_COLON          Block start
16        0x10  ST_NEWLINE        Line break
17        0x11  ST_INDENT         Enter function body
18        0x48  KW_RETURN         Return statement
19        0xFB  LIT_IDENT_FOLLOWS Variable reference
20        a     (letter)          "a"
21        0x00  SPACE             End of identifier
22        0x27  OP_ADD            Addition operator
23        0xFB  LIT_IDENT_FOLLOWS Variable reference
24        b     (letter)          "b"
25        0x00  SPACE             End of identifier
26        0x10  ST_NEWLINE        Line break
27        0x12  ST_DEDENT         Leave function body
```

28 bytes. The Python source is 33 characters (`def add(a, b):\n    return a + b\n`). Small savings here because the function is simple — the compression wins get bigger with boilerplate-heavy code.

Now let's trace these 28 bytes through every compiler stage.

---

## Stage 1: LEXER — Bytes to Tokens

The lexer reads the raw bytes and produces a stream of **tokens**. A token is a byte (or group of bytes for identifiers/literals) tagged with its type.

### What the lexer does

```
Read byte 0x60 → look up in table → Token(type=KEYWORD, value="func_def")
Read byte 0xFB → this means "identifier follows"
  Read bytes until SPACE → Token(type=IDENTIFIER, value="add")
Read byte 0x13 → Token(type=STRUCTURE, value="lparen")
Read byte 0xFB → identifier follows
  Read bytes until SPACE → Token(type=IDENTIFIER, value="a")
Read byte 0x19 → Token(type=STRUCTURE, value="comma")
...and so on
```

### The token stream (output of lexer)

```
Token(KEYWORD,    "func_def")
Token(IDENTIFIER, "add")
Token(LPAREN)
Token(IDENTIFIER, "a")
Token(COMMA)
Token(IDENTIFIER, "b")
Token(RPAREN)
Token(COLON)
Token(NEWLINE)
Token(INDENT)
Token(KEYWORD,    "return")
Token(IDENTIFIER, "a")
Token(OPERATOR,   "add")
Token(IDENTIFIER, "b")
Token(NEWLINE)
Token(DEDENT)
```

### Why this is trivial for Jalekon

In a normal compiler (for Python, C, Java), the lexer has to:
- Handle whitespace (spaces, tabs, newlines — which matter? which don't?)
- Parse string literals (escaping quotes, multiline strings, Unicode)
- Distinguish keywords from identifiers (is `class` a keyword or a variable name?)
- Parse numbers (integers, floats, hex, binary, underscores in numbers)
- Handle comments (single-line, multi-line, nested?)

For Jalekon: **every byte IS already a token.** The lexer is a table lookup. The only complexity is LIT_IDENT_FOLLOWS and LIT_STR_FOLLOWS, which read ahead until SPACE. That's it.

### Lexer implementation (Python prototype)

```python
JALEKON_TABLE = {
    0x60: ("KEYWORD", "func_def"),
    0x48: ("KEYWORD", "return"),
    0x40: ("KEYWORD", "if"),
    0x41: ("KEYWORD", "else"),
    0x43: ("KEYWORD", "for"),
    0x27: ("OPERATOR", "add"),
    0x28: ("OPERATOR", "sub"),
    0x29: ("OPERATOR", "mul"),
    0x20: ("OPERATOR", "assign"),
    0x21: ("OPERATOR", "eq"),
    0x13: ("LPAREN", None),
    0x14: ("RPAREN", None),
    0x19: ("COMMA", None),
    0x1A: ("COLON", None),
    0x10: ("NEWLINE", None),
    0x11: ("INDENT", None),
    0x12: ("DEDENT", None),
    0xA0: ("BUILTIN", "print"),
    0xF0: ("LITERAL_INT", 0),
    0xF1: ("LITERAL_INT", 1),
    0xF2: ("LITERAL_INT", 2),
    # ... rest of table
}

def lex(byte_stream):
    tokens = []
    i = 0
    while i < len(byte_stream):
        byte = byte_stream[i]

        if byte == 0xFB:  # LIT_IDENT_FOLLOWS
            # Read identifier bytes until SPACE (0x00)
            i += 1
            name = []
            while i < len(byte_stream) and byte_stream[i] != 0x00:
                name.append(chr(byte_stream[i]))
                i += 1
            tokens.append(("IDENTIFIER", "".join(name)))
            i += 1  # skip the SPACE

        elif byte == 0xF8:  # LIT_INT_FOLLOWS
            # Read variable-length integer
            i += 1
            # (integer decoding logic here)
            pass

        elif byte in JALEKON_TABLE:
            tokens.append(JALEKON_TABLE[byte])
            i += 1

        elif byte == 0x00:  # SPACE — token boundary
            i += 1

        else:
            raise ValueError(f"Unknown byte: 0x{byte:02X} at position {i}")

    return tokens
```

**That's the entire lexer.** ~30 lines of Python. A C or Java lexer is typically 500-2000 lines.

---

## Stage 2: PARSER — Tokens to AST

The parser reads the token stream and builds an **Abstract Syntax Tree (AST)**. The AST represents the program's structure as a tree, the same way a sentence diagram shows which words modify which.

### What is an AST?

The program `def add(a, b): return a + b` becomes:

```
FunctionDef
├── name: "add"
├── params: ["a", "b"]
└── body:
    └── ReturnStatement
        └── BinaryOp
            ├── op: "add"
            ├── left: VariableRef("a")
            └── right: VariableRef("b")
```

Each box is a **node**. Each node has a type (FunctionDef, ReturnStatement, BinaryOp, VariableRef) and children. The tree structure captures what contains what and what operates on what.

### How the parser builds the tree

The parser uses a technique called **recursive descent**. It reads tokens left to right and calls functions that match grammar rules:

```
See KW_FUNC → call parse_function()
  parse_function() reads:
    - IDENTIFIER → that's the function name
    - LPAREN → start of parameter list
    - loop: IDENTIFIER, COMMA → parameters
    - RPAREN → end of parameters
    - COLON → block starts
    - INDENT → enter body
    - call parse_statement() for each line in the body
    - DEDENT → exit body
    - return FunctionDef node

parse_statement() sees KW_RETURN → call parse_return()
  parse_return() reads:
    - call parse_expression() → gets the value to return
    - return ReturnStatement node

parse_expression() sees IDENTIFIER "a" → then OP_ADD → then IDENTIFIER "b"
  → return BinaryOp(op="add", left=VarRef("a"), right=VarRef("b"))
```

### Parser implementation (Python prototype)

```python
class ASTNode:
    pass

class FunctionDef(ASTNode):
    def __init__(self, name, params, body):
        self.name = name
        self.params = params
        self.body = body

class ReturnStmt(ASTNode):
    def __init__(self, value):
        self.value = value

class BinaryOp(ASTNode):
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right

class VarRef(ASTNode):
    def __init__(self, name):
        self.name = name

class IntLiteral(ASTNode):
    def __init__(self, value):
        self.value = value

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def consume(self, expected_type=None):
        token = self.tokens[self.pos]
        if expected_type and token[0] != expected_type:
            raise SyntaxError(
                f"Expected {expected_type}, got {token[0]} at position {self.pos}"
            )
        self.pos += 1
        return token

    def parse_program(self):
        """Entry point. Parse top-level statements."""
        statements = []
        while self.pos < len(self.tokens):
            tok = self.peek()
            if tok is None:
                break
            if tok == ("KEYWORD", "func_def"):
                statements.append(self.parse_function())
            elif tok[0] == "NEWLINE":
                self.consume()  # skip blank lines
            else:
                statements.append(self.parse_statement())
        return statements

    def parse_function(self):
        """Parse: KW_FUNC name LPAREN params RPAREN COLON NEWLINE INDENT body DEDENT"""
        self.consume()  # KW_FUNC
        name = self.consume("IDENTIFIER")[1]
        self.consume("LPAREN")

        params = []
        while self.peek()[0] != "RPAREN":
            params.append(self.consume("IDENTIFIER")[1])
            if self.peek()[0] == "COMMA":
                self.consume()  # skip comma

        self.consume("RPAREN")
        self.consume("COLON")
        self.consume("NEWLINE")
        self.consume("INDENT")

        body = []
        while self.peek() and self.peek()[0] != "DEDENT":
            body.append(self.parse_statement())

        self.consume("DEDENT")
        return FunctionDef(name, params, body)

    def parse_statement(self):
        """Parse a single statement."""
        tok = self.peek()
        if tok == ("KEYWORD", "return"):
            return self.parse_return()
        elif tok == ("KEYWORD", "if"):
            return self.parse_if()
        # ... other statement types
        else:
            return self.parse_expression()

    def parse_return(self):
        """Parse: KW_RETURN expression NEWLINE"""
        self.consume()  # KW_RETURN
        value = self.parse_expression()
        if self.peek() and self.peek()[0] == "NEWLINE":
            self.consume()
        return ReturnStmt(value)

    def parse_expression(self):
        """Parse an expression (handles binary operators)."""
        left = self.parse_primary()

        # Check for binary operator
        while self.peek() and self.peek()[0] == "OPERATOR":
            op = self.consume()[1]
            right = self.parse_primary()
            left = BinaryOp(op, left, right)

        return left

    def parse_primary(self):
        """Parse a single value: identifier, literal, or parenthesized expression."""
        tok = self.peek()

        if tok[0] == "IDENTIFIER":
            name = self.consume()[1]
            # Check if it's a function call
            if self.peek() and self.peek()[0] == "LPAREN":
                return self.parse_call(name)
            return VarRef(name)

        elif tok[0] == "LITERAL_INT":
            return IntLiteral(self.consume()[1])

        elif tok[0] == "LPAREN":
            self.consume()
            expr = self.parse_expression()
            self.consume("RPAREN")
            return expr

        else:
            raise SyntaxError(f"Unexpected token: {tok}")
```

### The AST for our example

After parsing, the tree looks like this in memory:

```
FunctionDef(
    name = "add",
    params = ["a", "b"],
    body = [
        ReturnStmt(
            value = BinaryOp(
                op = "add",
                left = VarRef("a"),
                right = VarRef("b")
            )
        )
    ]
)
```

This tree IS the program's meaning, stripped of all syntax. No colons, no indentation, no parentheses — just the structure of what the program does.

---

## Stage 3: TYPE CHECKER — Does This Program Make Sense?

Before generating machine code, the compiler checks that the program is valid:

- Are all variables defined before use? ("a" and "b" are function parameters — yes)
- Do the types match? (adding two numbers — yes. Adding a number to a string — error)
- Does every code path return a value? (our function always returns — yes)

For a first prototype, the type checker can be minimal or skipped entirely (like Python does — it checks at runtime instead). A production Jalekon compiler would do full static type checking.

---

## Stage 4: IR GENERATOR — AST to LLVM IR

This is the critical stage. The compiler walks the AST tree and emits **LLVM IR** — a low-level, platform-independent language that LLVM understands.

### What LLVM IR looks like

LLVM IR is somewhere between a programming language and assembly. Here's what our `add` function becomes:

```llvm
; Function: add(a, b) -> a + b
define i64 @add(i64 %a, i64 %b) {
entry:
  %result = add i64 %a, %b
  ret i64 %result
}
```

Line by line:

| LLVM IR | What it means |
|---------|--------------|
| `define i64 @add(i64 %a, i64 %b) {` | Define a function named "add" that takes two 64-bit integers and returns one |
| `entry:` | Label for the first block of code (every function starts with "entry") |
| `%result = add i64 %a, %b` | Add the two parameters, store in a temporary named %result |
| `ret i64 %result` | Return the result |
| `}` | End of function |

### How the IR generator walks the AST

```
Visit FunctionDef("add", ["a", "b"], body):
  → emit: "define i64 @add(i64 %a, i64 %b) {"
  → emit: "entry:"
  → visit each statement in body:
    Visit ReturnStmt(value):
      → visit the value expression:
        Visit BinaryOp("add", VarRef("a"), VarRef("b")):
          → visit left: VarRef("a") → returns "%a"
          → visit right: VarRef("b") → returns "%b"
          → emit: "%result = add i64 %a, %b"
          → returns "%result"
      → emit: "ret i64 %result"
  → emit: "}"
```

### IR generator implementation (Python prototype)

```python
class IRGenerator:
    def __init__(self):
        self.output = []
        self.temp_counter = 0

    def new_temp(self):
        """Generate a unique temporary variable name."""
        self.temp_counter += 1
        return f"%t{self.temp_counter}"

    def generate(self, node):
        """Dispatch to the right generator method based on node type."""
        if isinstance(node, FunctionDef):
            return self.gen_function(node)
        elif isinstance(node, ReturnStmt):
            return self.gen_return(node)
        elif isinstance(node, BinaryOp):
            return self.gen_binary_op(node)
        elif isinstance(node, VarRef):
            return self.gen_var_ref(node)
        elif isinstance(node, IntLiteral):
            return self.gen_int_literal(node)

    def gen_function(self, node):
        # Build parameter list
        params = ", ".join(f"i64 %{p}" for p in node.params)
        self.output.append(f"define i64 @{node.name}({params}) {{")
        self.output.append("entry:")

        # Generate body
        for stmt in node.body:
            self.generate(stmt)

        self.output.append("}")
        self.output.append("")

    def gen_return(self, node):
        # Generate the return value expression
        val = self.generate(node.value)
        self.output.append(f"  ret i64 {val}")

    def gen_binary_op(self, node):
        # Generate left and right sides
        left = self.generate(node.left)
        right = self.generate(node.right)

        # Map Jalekon operators to LLVM IR instructions
        llvm_ops = {
            "add": "add",
            "sub": "sub",
            "mul": "mul",
            "div": "sdiv",   # signed division
            "mod": "srem",   # signed remainder
        }

        result = self.new_temp()
        llvm_op = llvm_ops[node.op]
        self.output.append(f"  {result} = {llvm_op} i64 {left}, {right}")
        return result

    def gen_var_ref(self, node):
        return f"%{node.name}"

    def gen_int_literal(self, node):
        return str(node.value)

    def emit(self):
        return "\n".join(self.output)
```

### The complete LLVM IR output for our example

```llvm
define i64 @add(i64 %a, i64 %b) {
entry:
  %t1 = add i64 %a, %b
  ret i64 %t1
}
```

That's it. The entire function, in a form LLVM can compile to any platform.

---

## Stage 5: LLVM — IR to Machine Code

This is where LLVM takes over. We don't write this part — we call LLVM's tools.

### Step 5a: Save the IR to a file

```bash
# The compiler writes this file
cat > add.ll << 'EOF'
define i64 @add(i64 %a, i64 %b) {
entry:
  %t1 = add i64 %a, %b
  ret i64 %t1
}
EOF
```

### Step 5b: LLVM optimizes the IR

```bash
opt -O2 add.ll -o add_optimized.bc
```

LLVM runs optimization passes:
- **Constant folding:** If both inputs are known constants, compute at compile time
- **Dead code elimination:** Remove code that can never execute
- **Inlining:** Replace function calls with the function body (if small enough)
- **Register allocation:** Map virtual registers to physical CPU registers

### Step 5c: LLVM generates assembly for the target

```bash
llc add_optimized.bc -o add.s
```

For x86-64 Linux, this produces assembly like:

```asm
add:
    lea rax, [rdi + rsi]    ; rax = first_param + second_param
    ret                      ; return rax
```

Two instructions. The CPU adds two registers and returns. That's what `a + b` compiles down to.

For ARM64 (phones, Apple Silicon):

```asm
add:
    add x0, x0, x1          ; x0 = first_param + second_param
    ret                      ; return x0
```

Also two instructions. Different CPU, different registers, same result. LLVM handled the translation.

### Step 5d: Assemble to object file

```bash
llc add_optimized.bc -filetype=obj -o add.o
```

This produces a `.o` file — raw machine code bytes plus metadata (symbol names, relocation entries).

---

## Stage 6: LINKER — Object File to Executable

The object file contains our function's machine code, but it's not a program yet. It needs:

- An entry point (`main` function or equivalent)
- OS startup code (sets up the stack, calls `main`, handles exit)
- Any library functions we called (like `printf` for BI_PRINT)

```bash
clang add.o -o add        # Linux
clang add.o -o add.exe    # Windows
```

The linker:
1. Finds the entry point
2. Resolves all function references (connects our `@add` to its machine code)
3. Links system libraries (libc for printf, malloc, etc.)
4. Writes the executable in the OS's format (ELF for Linux, PE for Windows, Mach-O for macOS)

---

## The Complete Trail — Summary

```
JALEKON BYTE                   WHAT HAPPENS
──────────────────────────────────────────────────────────────

0x60 (KW_FUNC)                 Lexer: Token(KEYWORD, "func_def")
                                Parser: Start building FunctionDef node
                                IR Gen: emit "define i64 @..."
                                LLVM:   Create function entry in object file
                                Linker: Register symbol @add

0xFB 'a' 'd' 'd' 0x00          Lexer: Token(IDENTIFIER, "add")
                                Parser: Set function name = "add"
                                IR Gen: Use "add" in function name
                                LLVM:   Name the symbol @add
                                Linker: Export symbol @add

0x13 (ST_LPAREN)               Lexer: Token(LPAREN)
                                Parser: Start parameter list

0xFB 'a' 0x00                  Lexer: Token(IDENTIFIER, "a")
                                Parser: Add "a" to parameter list
                                IR Gen: emit "i64 %a" in function signature
                                LLVM:   Map %a to register rdi (x86) or x0 (ARM)

0x19 (ST_COMMA)                Lexer: Token(COMMA)
                                Parser: Expect next parameter

0xFB 'b' 0x00                  Lexer: Token(IDENTIFIER, "b")
                                Parser: Add "b" to parameter list
                                IR Gen: emit "i64 %b" in function signature
                                LLVM:   Map %b to register rsi (x86) or x1 (ARM)

0x14 (ST_RPAREN)               Lexer: Token(RPAREN)
                                Parser: Close parameter list

0x1A (ST_COLON)                Lexer: Token(COLON)
                                Parser: Function body follows

0x11 (ST_INDENT)               Lexer: Token(INDENT)
                                Parser: Enter function body scope

0x48 (KW_RETURN)               Lexer: Token(KEYWORD, "return")
                                Parser: Start ReturnStmt node
                                IR Gen: Will emit "ret" instruction

0xFB 'a' 0x00                  Lexer: Token(IDENTIFIER, "a")
                                Parser: VarRef("a") — left side of expression
                                IR Gen: Reference %a

0x27 (OP_ADD)                  Lexer: Token(OPERATOR, "add")
                                Parser: BinaryOp node, operator = add
                                IR Gen: emit "add i64 %a, %b"
                                LLVM:   Emit ADD instruction (lea rdi+rsi on x86)
                                CPU:    One clock cycle. Two numbers become one.

0xFB 'b' 0x00                  Lexer: Token(IDENTIFIER, "b")
                                Parser: VarRef("b") — right side of expression
                                IR Gen: Reference %b

0x12 (ST_DEDENT)               Lexer: Token(DEDENT)
                                Parser: Exit function body, close FunctionDef
                                IR Gen: emit "}"
```

**One Jalekon byte (0x27, OP_ADD) → one LLVM instruction → one CPU instruction → one clock cycle.**

The entire path from concept to computation.

---

## A More Complex Example: If/Else

```python
def max(a, b):
    if a > b:
        return a
    else:
        return b
```

### Jalekon bytes

```
KW_FUNC IDENT"max" LPAREN IDENT"a" COMMA IDENT"b" RPAREN COLON NEWLINE
INDENT
  KW_IF IDENT"a" OP_GT IDENT"b" COLON NEWLINE
  INDENT
    KW_RETURN IDENT"a" NEWLINE
  DEDENT
  KW_ELSE COLON NEWLINE
  INDENT
    KW_RETURN IDENT"b" NEWLINE
  DEDENT
DEDENT
```

### AST

```
FunctionDef(
    name = "max",
    params = ["a", "b"],
    body = [
        IfStatement(
            condition = BinaryOp("gt", VarRef("a"), VarRef("b")),
            then_body = [ReturnStmt(VarRef("a"))],
            else_body = [ReturnStmt(VarRef("b"))]
        )
    ]
)
```

### LLVM IR

```llvm
define i64 @max(i64 %a, i64 %b) {
entry:
  %cmp = icmp sgt i64 %a, %b       ; compare: is a > b? (signed greater than)
  br i1 %cmp, label %then, label %else  ; branch based on comparison

then:
  ret i64 %a                        ; return a

else:
  ret i64 %b                        ; return b
}
```

### x86-64 Assembly (what the CPU actually runs)

```asm
max:
    cmp  rdi, rsi       ; compare a and b
    mov  rax, rdi       ; assume a (will be overwritten if wrong)
    cmovl rax, rsi      ; if a < b, overwrite with b (conditional move)
    ret                  ; return winner
```

Three instructions. The CPU compares two numbers and returns the larger one. No branch, no jump — LLVM optimized the if/else into a conditional move because it's faster.

---

## What Each Stage Needs to Handle (Minimum Viable Compiler)

| Language Feature | Lexer | Parser | IR Generator |
|-----------------|-------|--------|--------------|
| Function definition | KW_FUNC token | FunctionDef node | LLVM `define` |
| Parameters | IDENTIFIER tokens | param list | LLVM function args |
| Return | KW_RETURN token | ReturnStmt node | LLVM `ret` |
| Integer arithmetic | OP_ADD/SUB/MUL/DIV | BinaryOp node | LLVM `add`/`sub`/`mul`/`sdiv` |
| Integer literals | LIT_0/1/2, LIT_INT_FOLLOWS | IntLiteral node | LLVM integer constants |
| Variables | IDENTIFIER token | VarRef node | LLVM `alloca` + `load`/`store` |
| Assignment | OP_ASSIGN token | AssignStmt node | LLVM `store` |
| If/else | KW_IF/ELSE tokens | IfStatement node | LLVM `icmp` + `br` + labels |
| While loop | KW_WHILE token | WhileStmt node | LLVM labels + `br` loop |
| Print | BI_PRINT token | CallExpr node | LLVM `call @printf` |

That's the minimum. ~10 language features. Each one needs handling in three places (lexer, parser, IR generator). The lexer part is trivial (table lookup). The parser part is a function per feature. The IR generator part is string emission following LLVM patterns.

---

## Next Step: Building the Prototype

The first working Jalekon compiler is a Python script (~500-1000 lines) that:

1. Reads a file of Jalekon bytes
2. Lexes → parses → generates LLVM IR (all in Python)
3. Writes the IR to a `.ll` file
4. Calls `llc` and `clang` (already installed via LLVM) to compile to native

The result: a Jalekon byte file goes in, a native executable comes out. The executable runs on the CPU with no interpreter, no VM, no Python.

This prototype proves the pipeline works. Everything after is refinement — more language features, better error messages, optimization, more targets.

---

*Travis Edward Holley*
*April 9, 2026*
