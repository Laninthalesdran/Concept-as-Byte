# Jalekon Byte Table — v0 Reference

## Programming Concept Assignments for the Jalekon Toggle Mode
## Travis Edward Holley — April 9, 2026

---

## The Toggle Principle

The JALEKON byte (0x07) acts as a toggle. When the model encounters it in the byte stream, the same 256 byte values switch from natural language concepts to programming concepts. Same table structure, same byte ranges, different interpretation.

The model learns this from training data. It sees the JALEKON toggle, and everything that follows is code. The model doesn't need explicit instructions — the patterns in the training data teach it that post-toggle bytes carry programming semantics.

```
[natural language bytes] JALEKON [programming bytes] JALEKON [natural language bytes]
```

No separate encoder. No separate table. Same 256 values, two contexts. The model learns the difference.

---

## Single-Byte Tier (0x08-0xFF = 248 slots)

### 0x08-0x0F — Decompilation Views (8 slots)

Human inspection hints. No effect on compilation.

| Hex | Code | Target |
|-----|------|--------|
| 0x08 | LANG_PYTHON | Python |
| 0x09 | LANG_JS | JavaScript |
| 0x0A | LANG_TS | TypeScript |
| 0x0B | LANG_JAVA | Java |
| 0x0C | LANG_RUST | Rust |
| 0x0D | LANG_GO | Go |
| 0x0E | LANG_CPP | C/C++ |
| 0x0F | LANG_GENERIC | Language-agnostic |

### 0x10-0x1F — Structural Tokens (16 slots)

| Hex | Code | Symbol | Concept |
|-----|------|--------|---------|
| 0x10 | ST_NEWLINE | `\n` | Line break |
| 0x11 | ST_INDENT | (4 spaces) | Increase indentation |
| 0x12 | ST_DEDENT | (unindent) | Decrease indentation |
| 0x13 | ST_LPAREN | `(` | Open parenthesis |
| 0x14 | ST_RPAREN | `)` | Close parenthesis |
| 0x15 | ST_LBRACKET | `[` | Open bracket |
| 0x16 | ST_RBRACKET | `]` | Close bracket |
| 0x17 | ST_LBRACE | `{` | Open brace |
| 0x18 | ST_RBRACE | `}` | Close brace |
| 0x19 | ST_COMMA | `,` | Separator |
| 0x1A | ST_COLON | `:` | Block start / key separator |
| 0x1B | ST_SEMI | `;` | Statement end |
| 0x1C | ST_DOT | `.` | Member access |
| 0x1D | ST_SPREAD | `...` | Spread / rest |
| 0x1E | ST_AT | `@` | Decorator / annotation |
| 0x1F | ST_HASH | `#` / `//` | Line comment |

### 0x20-0x3F — Operators (32 slots)

| Hex | Code | Symbol(s) | Concept |
|-----|------|-----------|---------|
| 0x20 | OP_ASSIGN | `=` | Assignment |
| 0x21 | OP_EQ | `==` / `===` | Equality |
| 0x22 | OP_NEQ | `!=` / `!==` | Inequality |
| 0x23 | OP_LT | `<` | Less than |
| 0x24 | OP_GT | `>` | Greater than |
| 0x25 | OP_LTE | `<=` | Less or equal |
| 0x26 | OP_GTE | `>=` | Greater or equal |
| 0x27 | OP_ADD | `+` | Addition / concatenation |
| 0x28 | OP_SUB | `-` | Subtraction |
| 0x29 | OP_MUL | `*` | Multiplication |
| 0x2A | OP_DIV | `/` | Division |
| 0x2B | OP_IDIV | `//` | Integer division |
| 0x2C | OP_MOD | `%` | Modulo |
| 0x2D | OP_POW | `**` | Exponentiation |
| 0x2E | OP_ADDEQ | `+=` | Add-assign |
| 0x2F | OP_SUBEQ | `-=` | Subtract-assign |
| 0x30 | OP_MULEQ | `*=` | Multiply-assign |
| 0x31 | OP_DIVEQ | `/=` | Divide-assign |
| 0x32 | OP_MODEQ | `%=` | Modulo-assign |
| 0x33 | OP_POWEQ | `**=` | Power-assign |
| 0x34 | OP_BAND | `&` | Bitwise AND |
| 0x35 | OP_BOR | `\|` | Bitwise OR |
| 0x36 | OP_BXOR | `^` | Bitwise XOR |
| 0x37 | OP_BNOT | `~` | Bitwise NOT |
| 0x38 | OP_LSHIFT | `<<` | Left shift |
| 0x39 | OP_RSHIFT | `>>` | Right shift |
| 0x3A | OP_BANDEQ | `&=` | Bitwise AND assign |
| 0x3B | OP_BOREQ | `\|=` | Bitwise OR assign |
| 0x3C | OP_BXOREQ | `^=` | Bitwise XOR assign |
| 0x3D | OP_LSHIFTEQ | `<<=` | Left shift assign |
| 0x3E | OP_RSHIFTEQ | `>>=` | Right shift assign |
| 0x3F | OP_WALRUS | `:=` | Assignment expression |

### 0x40-0x5F — Control Flow Keywords (32 slots, 5 reserved)

| Hex | Code | Python | JS | Java | Concept |
|-----|------|--------|----|------|---------|
| 0x40 | KW_IF | `if` | `if` | `if` | Conditional branch |
| 0x41 | KW_ELSE | `else` | `else` | `else` | Alternative branch |
| 0x42 | KW_ELIF | `elif` | `else if` | `else if` | Chained conditional |
| 0x43 | KW_FOR | `for` | `for` | `for` | Loop |
| 0x44 | KW_WHILE | `while` | `while` | `while` | Conditional loop |
| 0x45 | KW_DO | — | `do` | `do` | Do-while |
| 0x46 | KW_BREAK | `break` | `break` | `break` | Loop exit |
| 0x47 | KW_CONTINUE | `continue` | `continue` | `continue` | Skip iteration |
| 0x48 | KW_RETURN | `return` | `return` | `return` | Function return |
| 0x49 | KW_YIELD | `yield` | `yield` | — | Generator yield |
| 0x4A | KW_YIELD_FROM | `yield from` | `yield*` | — | Delegated yield |
| 0x4B | KW_PASS | `pass` | — | — | No-op |
| 0x4C | KW_SWITCH | `match` | `switch` | `switch` | Pattern match |
| 0x4D | KW_CASE | `case` | `case` | `case` | Match arm |
| 0x4E | KW_DEFAULT | — | `default` | `default` | Default arm |
| 0x4F | KW_TRY | `try` | `try` | `try` | Exception block |
| 0x50 | KW_CATCH | `except` | `catch` | `catch` | Exception handler |
| 0x51 | KW_FINALLY | `finally` | `finally` | `finally` | Cleanup block |
| 0x52 | KW_THROW | `raise` | `throw` | `throw` | Raise exception |
| 0x53 | KW_WITH | `with` | — | try-with-resources | Context manager |
| 0x54 | KW_AS | `as` | `as` | — | Alias / cast |
| 0x55 | KW_ASSERT | `assert` | — | `assert` | Assertion |
| 0x56 | KW_DELETE | `del` | `delete` | — | Deletion |
| 0x57 | KW_ASYNC | `async` | `async` | — | Async declaration |
| 0x58 | KW_AWAIT | `await` | `await` | — | Await expression |
| 0x59 | KW_GOTO | — | — | — | Goto (C/C++) |
| 0x5A | KW_LABEL | — | — | — | Label target |
| 0x5B-0x5F | _RESERVED | — | — | — | 5 reserved slots |

### 0x60-0x7F — Declarations + Access Modifiers (32 slots, 2 reserved)

| Hex | Code | Concept |
|-----|------|---------|
| 0x60 | KW_FUNC | Function / method definition |
| 0x61 | KW_CLASS | Class definition |
| 0x62 | KW_INTERFACE | Interface / protocol / ABC |
| 0x63 | KW_ENUM | Enumeration |
| 0x64 | KW_STRUCT | Struct (Rust/Go/C) |
| 0x65 | KW_IMPORT | Import |
| 0x66 | KW_FROM | Import source |
| 0x67 | KW_EXPORT | Export |
| 0x68 | KW_PACKAGE | Package (Java/Go) |
| 0x69 | KW_NEW | Instantiation |
| 0x6A | KW_THIS | self / this |
| 0x6B | KW_SUPER | super() |
| 0x6C | KW_EXTENDS | Inheritance |
| 0x6D | KW_IMPLEMENTS | Interface implementation |
| 0x6E | KW_LAMBDA | Anonymous function |
| 0x6F | KW_VAR | Mutable variable |
| 0x70 | KW_CONST | Immutable constant |
| 0x71 | KW_GLOBAL | Global / nonlocal |
| 0x72 | KW_TYPEDEF | Type alias |
| 0x73 | KW_DATACLASS | Data class / record |
| 0x74 | AM_PUBLIC | Public access |
| 0x75 | AM_PRIVATE | Private access |
| 0x76 | AM_PROTECTED | Protected access |
| 0x77 | AM_STATIC | Static member |
| 0x78 | AM_ABSTRACT | Abstract |
| 0x79 | AM_FINAL | Final / sealed |
| 0x7A | AM_OVERRIDE | Override |
| 0x7B | AM_VOLATILE | Volatile |
| 0x7C | AM_SYNCHRONIZED | Synchronized |
| 0x7D | AM_NATIVE | Native / extern |
| 0x7E-0x7F | _RESERVED | 2 reserved slots |

### 0x80-0x8F — Logic + Values (16 slots, 1 reserved)

| Hex | Code | Concept |
|-----|------|---------|
| 0x80 | KW_AND | Logical AND |
| 0x81 | KW_OR | Logical OR |
| 0x82 | KW_NOT | Logical NOT |
| 0x83 | KW_IN | Membership test |
| 0x84 | KW_NOT_IN | Negative membership |
| 0x85 | KW_IS | Identity |
| 0x86 | KW_IS_NOT | Negative identity |
| 0x87 | KW_INSTANCEOF | Type check |
| 0x88 | KW_TYPEOF | Type query |
| 0x89 | KW_TRUE | Boolean true |
| 0x8A | KW_FALSE | Boolean false |
| 0x8B | KW_NULL | Null / None |
| 0x8C | KW_TERNARY | Ternary expression |
| 0x8D | KW_NULLCOAL | Nullish coalescing (??) |
| 0x8E | KW_OPTCHAIN | Optional chaining (?.) |
| 0x8F | _RESERVED | Reserved |

### 0x90-0x9F — Type Primitives (16 slots)

| Hex | Code | Concept |
|-----|------|---------|
| 0x90 | TY_INT | Integer |
| 0x91 | TY_FLOAT | Floating point |
| 0x92 | TY_STR | String |
| 0x93 | TY_BOOL | Boolean |
| 0x94 | TY_BYTE | Byte / buffer |
| 0x95 | TY_CHAR | Character |
| 0x96 | TY_LIST | Ordered collection |
| 0x97 | TY_DICT | Key-value mapping |
| 0x98 | TY_SET | Unique collection |
| 0x99 | TY_TUPLE | Immutable sequence |
| 0x9A | TY_VOID | No return |
| 0x9B | TY_ANY | Any type |
| 0x9C | TY_OPTIONAL | Nullable |
| 0x9D | TY_GENERIC | Generic parameter `<T>` |
| 0x9E | TY_UNION | Type union |
| 0x9F | TY_CALLABLE | Function type |

### 0xA0-0xAF — Builtins: I/O (16 slots, 3 reserved)

| Hex | Code | Python | JS | Concept |
|-----|------|--------|----|---------|
| 0xA0 | BI_PRINT | `print()` | `console.log()` | Standard output |
| 0xA1 | BI_INPUT | `input()` | `readline()` | Standard input |
| 0xA2 | BI_OPEN | `open()` | `fs.readFile()` | File open |
| 0xA3 | BI_READ | `.read()` | `fs.readFileSync` | File read |
| 0xA4 | BI_WRITE | `.write()` | `fs.writeFileSync` | File write |
| 0xA5 | BI_CLOSE | `.close()` | — | File close |
| 0xA6 | BI_FLUSH | `.flush()` | — | Buffer flush |
| 0xA7 | BI_FORMAT | `f"..."` | `` `${}` `` | String interpolation |
| 0xA8 | BI_REPR | `repr()` | `JSON.stringify` | Debug representation |
| 0xA9 | BI_LOG_DEBUG | `logging.debug` | `console.debug` | Debug log |
| 0xAA | BI_LOG_INFO | `logging.info` | `console.info` | Info log |
| 0xAB | BI_LOG_WARN | `logging.warning` | `console.warn` | Warning log |
| 0xAC | BI_LOG_ERROR | `logging.error` | `console.error` | Error log |
| 0xAD-0xAF | _RESERVED | — | — | 3 reserved |

### 0xB0-0xBF — Builtins: Collections (16 slots)

| Hex | Code | Concept |
|-----|------|---------|
| 0xB0 | BI_LEN | Collection size |
| 0xB1 | BI_APPEND | Add to end |
| 0xB2 | BI_EXTEND | Concatenate collections |
| 0xB3 | BI_INSERT | Add at index |
| 0xB4 | BI_REMOVE | Remove element |
| 0xB5 | BI_POP | Remove and return last |
| 0xB6 | BI_GET | Access by key |
| 0xB7 | BI_SET | Set by key |
| 0xB8 | BI_KEYS | Get all keys |
| 0xB9 | BI_VALUES | Get all values |
| 0xBA | BI_ITEMS | Get key-value pairs |
| 0xBB | BI_CONTAINS | Membership check |
| 0xBC | BI_INDEX | Find position |
| 0xBD | BI_SORT | Sort elements |
| 0xBE | BI_REVERSE | Reverse order |
| 0xBF | BI_COPY | Shallow copy |

### 0xC0-0xCF — Builtins: Functional + Math (16 slots)

| Hex | Code | Concept |
|-----|------|---------|
| 0xC0 | BI_MAP | Transform elements |
| 0xC1 | BI_FILTER | Filter elements |
| 0xC2 | BI_REDUCE | Aggregate elements |
| 0xC3 | BI_ZIP | Parallel iteration |
| 0xC4 | BI_ENUMERATE | Index + value iteration |
| 0xC5 | BI_RANGE | Integer range |
| 0xC6 | BI_ALL | All match predicate |
| 0xC7 | BI_ANY | Any match predicate |
| 0xC8 | BI_MIN | Minimum |
| 0xC9 | BI_MAX | Maximum |
| 0xCA | BI_SUM | Sum |
| 0xCB | BI_ABS | Absolute value |
| 0xCC | BI_ROUND | Round |
| 0xCD | BI_FLOOR | Floor |
| 0xCE | BI_CEIL | Ceiling |
| 0xCF | BI_POWER | Power |

### 0xD0-0xDF — Builtins: Strings (16 slots)

| Hex | Code | Concept |
|-----|------|---------|
| 0xD0 | BI_SPLIT | Split string |
| 0xD1 | BI_JOIN | Join strings |
| 0xD2 | BI_STRIP | Trim whitespace |
| 0xD3 | BI_LSTRIP | Trim left |
| 0xD4 | BI_RSTRIP | Trim right |
| 0xD5 | BI_REPLACE | Replace substring |
| 0xD6 | BI_FIND | Find substring |
| 0xD7 | BI_UPPER | Uppercase |
| 0xD8 | BI_LOWER | Lowercase |
| 0xD9 | BI_STARTSWITH | Starts with |
| 0xDA | BI_ENDSWITH | Ends with |
| 0xDB | BI_TOSTR | Convert to string |
| 0xDC | BI_TOINT | Convert to integer |
| 0xDD | BI_TOFLOAT | Convert to float |
| 0xDE | BI_REGEX | Regex match |
| 0xDF | BI_REGEX_SUB | Regex replace |

### 0xE0-0xEF — Common Patterns (16 slots)

| Hex | Code | Replaces | Compression |
|-----|------|----------|-------------|
| 0xE0 | PT_MAIN | `if __name__=="__main__":` | 97% |
| 0xE1 | PT_INIT | `def __init__(self):` | 95% |
| 0xE2 | PT_SUPER_INIT | `super().__init__()` | 94% |
| 0xE3 | PT_SELF_ASSIGN | `self.x = x` pattern | 80% |
| 0xE4 | PT_FOR_RANGE | `for i in range(n):` | 74% |
| 0xE5 | PT_FOR_EACH | `for x in collection:` | 73% |
| 0xE6 | PT_WITH_OPEN | `with open(path) as f:` | 77% |
| 0xE7 | PT_TRY_BLOCK | `try: ... except E as e:` | 75% |
| 0xE8 | PT_LIST_COMP | `[expr for x in iter]` | 70% |
| 0xE9 | PT_DICT_COMP | `{k:v for k,v in iter}` | 72% |
| 0xEA | PT_SET_COMP | `{expr for x in iter}` | 70% |
| 0xEB | PT_GEN_EXPR | `(expr for x in iter)` | 70% |
| 0xEC | PT_IMPORT_FROM | `from x import y` | 75% |
| 0xED | PT_IMPORT_AS | `import x as y` | 72% |
| 0xEE | PT_DOCSTRING | `"""..."""` | 67% |
| 0xEF | PT_DUNDER | `__method__` marker | 80% |

### 0xF0-0xFF — Literals + Encoding Control (16 slots)

| Hex | Code | Meaning |
|-----|------|---------|
| 0xF0 | LIT_0 | Integer 0 |
| 0xF1 | LIT_1 | Integer 1 |
| 0xF2 | LIT_2 | Integer 2 |
| 0xF3 | LIT_NEG1 | Integer -1 |
| 0xF4 | LIT_EMPTY_STR | Empty string `""` |
| 0xF5 | LIT_EMPTY_LIST | Empty list `[]` |
| 0xF6 | LIT_EMPTY_DICT | Empty dict `{}` |
| 0xF7 | LIT_EMPTY_SET | Empty set |
| 0xF8 | LIT_INT_FOLLOWS | Variable-length integer follows |
| 0xF9 | LIT_FLOAT_FOLLOWS | IEEE 754 float follows |
| 0xFA | LIT_STR_FOLLOWS | String literal follows (Jalek-encoded) |
| 0xFB | LIT_IDENT_FOLLOWS | Identifier follows (via main Jalek table) |
| 0xFC | LIT_RAW_FOLLOWS | Raw bytes follow (length-prefixed) |
| 0xFD | SCOPE_BEGIN | Named scope begins |
| 0xFE | SCOPE_END | Named scope ends |
| 0xFF | ESCAPE | Next byte is literal, not a code |

---

## Two-Byte Tier (61,504 slots available)

| Category | Estimated Codes |
|----------|----------------|
| Standard library modules | ~50 |
| Python dunder methods | ~30 |
| Framework patterns (Flask, React, Django, Spring) | ~40 |
| Error/exception types | ~20 |
| Language-specific keywords | TBD |
| Domain-specific builtins | TBD |
| **Initial total** | **~140** |
| **Capacity** | **61,504** |

---

## Summary

| Metric | Count |
|--------|-------|
| Single-byte codes assigned | 218 |
| Single-byte codes reserved | 14 |
| Total single-byte slots | 248 |
| Two-byte capacity | 61,504 |
| Status | v0 DRAFT — all assignments provisional |

---

*Travis Edward Holley*
*April 9, 2026*
