"""
Jalekon Prototype Compiler
==========================
Jalekon bytes → Tokens → AST → LLVM IR

Travis Edward Holley — April 9, 2026
First working prototype of the Jalekon compilation pipeline.

Usage:
    python jalekon_compiler.py input.jkn              # emit LLVM IR to stdout
    python jalekon_compiler.py input.jkn -o output.ll # emit LLVM IR to file
    python jalekon_compiler.py --test                 # run built-in tests
"""

import sys
import struct

# =============================================================================
# JALEKON BYTE TABLE
# =============================================================================
# These are the byte values from the v0 Jalekon table.
# When the model emits these bytes after a JALEKON toggle (0x07),
# they carry programming semantics.

# Control (inherited from Jalek)
SPACE           = 0x00
BOUNDARY        = 0x01
JALEKON_TOGGLE  = 0x07

# Structural
ST_NEWLINE      = 0x10
ST_INDENT       = 0x11
ST_DEDENT       = 0x12
ST_LPAREN       = 0x13
ST_RPAREN       = 0x14
ST_LBRACKET     = 0x15
ST_RBRACKET     = 0x16
ST_LBRACE       = 0x17
ST_RBRACE       = 0x18
ST_COMMA        = 0x19
ST_COLON        = 0x1A
ST_SEMI         = 0x1B
ST_DOT          = 0x1C

# Operators
OP_ASSIGN       = 0x20
OP_EQ           = 0x21
OP_NEQ          = 0x22
OP_LT           = 0x23
OP_GT           = 0x24
OP_LTE          = 0x25
OP_GTE          = 0x26
OP_ADD          = 0x27
OP_SUB          = 0x28
OP_MUL          = 0x29
OP_DIV          = 0x2A
OP_IDIV         = 0x2B
OP_MOD          = 0x2C
OP_POW          = 0x2D

# Keywords — Control Flow
KW_IF           = 0x40
KW_ELSE         = 0x41
KW_ELIF         = 0x42
KW_FOR          = 0x43
KW_WHILE        = 0x44
KW_BREAK        = 0x46
KW_CONTINUE     = 0x47
KW_RETURN       = 0x48
KW_PASS         = 0x4B

# Keywords — Declarations
KW_FUNC         = 0x60
KW_CLASS        = 0x61
KW_VAR          = 0x6F
KW_CONST        = 0x70

# Logic + Values
KW_AND          = 0x80
KW_OR           = 0x81
KW_NOT          = 0x82
KW_TRUE         = 0x89
KW_FALSE        = 0x8A
KW_NULL         = 0x8B

# Types
TY_INT          = 0x90
TY_FLOAT        = 0x91
TY_STR          = 0x92
TY_BOOL         = 0x93
TY_VOID         = 0x9A

# Builtins
BI_PRINT        = 0xA0

# Literals + Encoding
LIT_0           = 0xF0
LIT_1           = 0xF1
LIT_2           = 0xF2
LIT_NEG1        = 0xF3
LIT_INT_FOLLOWS = 0xF8
LIT_STR_FOLLOWS = 0xFA
LIT_IDENT       = 0xFB
ESCAPE          = 0xFF


# =============================================================================
# STAGE 1: LEXER
# =============================================================================
# Reads raw bytes, produces a stream of Token objects.
# For Jalekon this is almost trivial — each byte IS a token.

class Token:
    def __init__(self, kind, value=None, pos=0):
        self.kind = kind      # e.g. "KW_FUNC", "IDENTIFIER", "OP_ADD"
        self.value = value    # e.g. "add", 42, None
        self.pos = pos        # byte position in the input (for error messages)

    def __repr__(self):
        if self.value is not None:
            return f"Token({self.kind}, {self.value!r})"
        return f"Token({self.kind})"


# Map bytes to token kinds
BYTE_TO_TOKEN = {
    # Structural
    ST_NEWLINE:  "NEWLINE",
    ST_INDENT:   "INDENT",
    ST_DEDENT:   "DEDENT",
    ST_LPAREN:   "LPAREN",
    ST_RPAREN:   "RPAREN",
    ST_LBRACKET: "LBRACKET",
    ST_RBRACKET: "RBRACKET",
    ST_LBRACE:   "LBRACE",
    ST_RBRACE:   "RBRACE",
    ST_COMMA:    "COMMA",
    ST_COLON:    "COLON",
    ST_SEMI:     "SEMI",
    ST_DOT:      "DOT",

    # Operators
    OP_ASSIGN:   "ASSIGN",
    OP_EQ:       "EQ",
    OP_NEQ:      "NEQ",
    OP_LT:       "LT",
    OP_GT:       "GT",
    OP_LTE:      "LTE",
    OP_GTE:      "GTE",
    OP_ADD:      "ADD",
    OP_SUB:      "SUB",
    OP_MUL:      "MUL",
    OP_DIV:      "DIV",
    OP_IDIV:     "IDIV",
    OP_MOD:      "MOD",
    OP_POW:      "POW",

    # Keywords — Control Flow
    KW_IF:       "IF",
    KW_ELSE:     "ELSE",
    KW_ELIF:     "ELIF",
    KW_FOR:      "FOR",
    KW_WHILE:    "WHILE",
    KW_BREAK:    "BREAK",
    KW_CONTINUE: "CONTINUE",
    KW_RETURN:   "RETURN",
    KW_PASS:     "PASS",

    # Keywords — Declarations
    KW_FUNC:     "FUNC",
    KW_CLASS:    "CLASS",
    KW_VAR:      "VAR",
    KW_CONST:    "CONST",

    # Logic + Values
    KW_AND:      "AND",
    KW_OR:       "OR",
    KW_NOT:      "NOT",
    KW_TRUE:     "TRUE",
    KW_FALSE:    "FALSE",
    KW_NULL:     "NULL",

    # Types
    TY_INT:      "TYPE_INT",
    TY_FLOAT:    "TYPE_FLOAT",
    TY_STR:      "TYPE_STR",
    TY_BOOL:     "TYPE_BOOL",
    TY_VOID:     "TYPE_VOID",

    # Builtins
    BI_PRINT:    "PRINT",

    # Literals
    LIT_0:       "INT_LIT",
    LIT_1:       "INT_LIT",
    LIT_2:       "INT_LIT",
    LIT_NEG1:    "INT_LIT",
}

# Map literal bytes to their values
LIT_VALUES = {
    LIT_0: 0,
    LIT_1: 1,
    LIT_2: 2,
    LIT_NEG1: -1,
}


def lex(data: bytes) -> list[Token]:
    """
    Lex a stream of Jalekon bytes into tokens.

    This is the simplest stage of the compiler. Each byte maps directly
    to a token via table lookup. The only complexity is multi-byte sequences
    for identifiers (LIT_IDENT) and integer literals (LIT_INT_FOLLOWS).
    """
    tokens = []
    i = 0

    while i < len(data):
        byte = data[i]

        # Skip SPACE (token boundary) and JALEKON toggle
        if byte == SPACE or byte == JALEKON_TOGGLE:
            i += 1
            continue

        # Identifier: read bytes until SPACE
        if byte == LIT_IDENT:
            i += 1
            name_bytes = []
            while i < len(data) and data[i] != SPACE:
                name_bytes.append(data[i])
                i += 1
            name = bytes(name_bytes).decode("ascii")
            tokens.append(Token("IDENT", name, i))
            if i < len(data):
                i += 1  # skip trailing SPACE
            continue

        # Integer literal follows: read a variable-length signed integer
        if byte == LIT_INT_FOLLOWS:
            i += 1
            # Read 8 bytes as a signed 64-bit integer (little-endian)
            int_bytes = data[i:i+8]
            value = struct.unpack("<q", int_bytes)[0]
            tokens.append(Token("INT_LIT", value, i))
            i += 8
            continue

        # String literal follows: read length-prefixed string
        if byte == LIT_STR_FOLLOWS:
            i += 1
            # First two bytes = length (little-endian uint16)
            length = struct.unpack("<H", data[i:i+2])[0]
            i += 2
            string = data[i:i+length].decode("utf-8")
            tokens.append(Token("STR_LIT", string, i))
            i += length
            continue

        # Single-byte literal (0, 1, 2, -1)
        if byte in LIT_VALUES:
            tokens.append(Token("INT_LIT", LIT_VALUES[byte], i))
            i += 1
            continue

        # Standard single-byte token
        if byte in BYTE_TO_TOKEN:
            tokens.append(Token(BYTE_TO_TOKEN[byte], None, i))
            i += 1
            continue

        raise ValueError(f"Unknown Jalekon byte 0x{byte:02X} at position {i}")

    return tokens


# =============================================================================
# STAGE 2: PARSER
# =============================================================================
# Reads the token stream, builds an Abstract Syntax Tree (AST).
# Uses recursive descent — each grammar rule is a function.

# --- AST Node Types ---

class FunctionDef:
    """Function definition: name, parameters, return type, body statements."""
    def __init__(self, name, params, body, return_type="i64"):
        self.name = name
        self.params = params        # list of (name, type) tuples
        self.body = body            # list of statement nodes
        self.return_type = return_type

class ReturnStmt:
    """Return statement with a value expression."""
    def __init__(self, value):
        self.value = value

class IfStmt:
    """If/else statement: condition, then body, optional else body."""
    def __init__(self, condition, then_body, else_body=None):
        self.condition = condition
        self.then_body = then_body
        self.else_body = else_body

class WhileStmt:
    """While loop: condition, body."""
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body

class AssignStmt:
    """Variable assignment: name = expression."""
    def __init__(self, name, value):
        self.name = name
        self.value = value

class VarDeclStmt:
    """Variable declaration with optional initial value."""
    def __init__(self, name, value=None, var_type="i64"):
        self.name = name
        self.value = value
        self.var_type = var_type

class ExprStmt:
    """Expression used as a statement (e.g., a function call on its own line)."""
    def __init__(self, expr):
        self.expr = expr

class BinaryOp:
    """Binary operation: left op right."""
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right

class UnaryOp:
    """Unary operation: op operand."""
    def __init__(self, op, operand):
        self.op = op
        self.operand = operand

class IntLiteral:
    """Integer constant."""
    def __init__(self, value):
        self.value = value

class BoolLiteral:
    """Boolean constant."""
    def __init__(self, value):
        self.value = value

class VarRef:
    """Reference to a variable by name."""
    def __init__(self, name):
        self.name = name

class CallExpr:
    """Function call: name(args)."""
    def __init__(self, name, args):
        self.name = name
        self.args = args

class PrintCall:
    """Built-in print call."""
    def __init__(self, args):
        self.args = args


# --- Comparison operators (for the parser) ---
COMPARISON_OPS = {"EQ", "NEQ", "LT", "GT", "LTE", "GTE"}
ADDITIVE_OPS = {"ADD", "SUB"}
MULTIPLICATIVE_OPS = {"MUL", "DIV", "IDIV", "MOD"}


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return Token("EOF")

    def at(self, kind):
        return self.peek().kind == kind

    def consume(self, kind=None):
        tok = self.tokens[self.pos]
        if kind is not None and tok.kind != kind:
            raise SyntaxError(
                f"Expected {kind}, got {tok.kind} (value={tok.value!r}) "
                f"at token position {self.pos}"
            )
        self.pos += 1
        return tok

    def skip_newlines(self):
        while self.pos < len(self.tokens) and self.at("NEWLINE"):
            self.consume()

    # --- Grammar Rules ---

    def parse_program(self):
        """Program = list of top-level statements (functions, etc.)."""
        statements = []
        self.skip_newlines()
        while self.pos < len(self.tokens) and not self.at("EOF"):
            if self.at("FUNC"):
                statements.append(self.parse_function())
            else:
                statements.append(self.parse_statement())
            self.skip_newlines()
        return statements

    def parse_function(self):
        """
        Function = FUNC IDENT LPAREN params RPAREN COLON NEWLINE
                   INDENT body DEDENT
        """
        self.consume("FUNC")
        name = self.consume("IDENT").value

        # Parameters
        self.consume("LPAREN")
        params = []
        while not self.at("RPAREN"):
            param_name = self.consume("IDENT").value
            params.append((param_name, "i64"))  # default type for now
            if self.at("COMMA"):
                self.consume()
        self.consume("RPAREN")

        # Optional return type annotation (skipped for now — default i64)
        self.consume("COLON")
        self.skip_newlines()

        # Body
        self.consume("INDENT")
        body = self.parse_block()
        self.consume("DEDENT")

        return FunctionDef(name, params, body)

    def parse_block(self):
        """Block = list of statements until DEDENT."""
        stmts = []
        self.skip_newlines()
        while not self.at("DEDENT") and not self.at("EOF"):
            stmts.append(self.parse_statement())
            self.skip_newlines()
        return stmts

    def parse_statement(self):
        """Statement = return | if | while | var | assignment | expression."""
        self.skip_newlines()
        tok = self.peek()

        if tok.kind == "RETURN":
            return self.parse_return()
        elif tok.kind == "IF":
            return self.parse_if()
        elif tok.kind == "WHILE":
            return self.parse_while()
        elif tok.kind == "VAR" or tok.kind == "CONST":
            return self.parse_var_decl()
        elif tok.kind == "PRINT":
            return self.parse_print()
        elif tok.kind == "IDENT":
            # Could be assignment (x = ...) or expression (func_call())
            return self.parse_assign_or_expr()
        elif tok.kind == "PASS":
            self.consume()
            return ExprStmt(IntLiteral(0))  # no-op
        else:
            return ExprStmt(self.parse_expression())

    def parse_return(self):
        self.consume("RETURN")
        if self.at("NEWLINE") or self.at("DEDENT") or self.at("EOF"):
            return ReturnStmt(IntLiteral(0))  # bare return
        value = self.parse_expression()
        return ReturnStmt(value)

    def parse_if(self):
        self.consume("IF")
        condition = self.parse_expression()
        self.consume("COLON")
        self.skip_newlines()
        self.consume("INDENT")
        then_body = self.parse_block()
        self.consume("DEDENT")

        else_body = None
        self.skip_newlines()
        if self.at("ELSE"):
            self.consume("ELSE")
            self.consume("COLON")
            self.skip_newlines()
            self.consume("INDENT")
            else_body = self.parse_block()
            self.consume("DEDENT")
        elif self.at("ELIF"):
            # elif chains as nested if in else
            else_body = [self.parse_if()]

        return IfStmt(condition, then_body, else_body)

    def parse_while(self):
        self.consume("WHILE")
        condition = self.parse_expression()
        self.consume("COLON")
        self.skip_newlines()
        self.consume("INDENT")
        body = self.parse_block()
        self.consume("DEDENT")
        return WhileStmt(condition, body)

    def parse_var_decl(self):
        self.consume()  # VAR or CONST
        name = self.consume("IDENT").value
        value = None
        if self.at("ASSIGN"):
            self.consume()
            value = self.parse_expression()
        return VarDeclStmt(name, value)

    def parse_print(self):
        self.consume("PRINT")
        self.consume("LPAREN")
        args = []
        if not self.at("RPAREN"):
            args.append(self.parse_expression())
            while self.at("COMMA"):
                self.consume()
                args.append(self.parse_expression())
        self.consume("RPAREN")
        return ExprStmt(PrintCall(args))

    def parse_assign_or_expr(self):
        name_tok = self.consume("IDENT")
        if self.at("ASSIGN"):
            self.consume()
            value = self.parse_expression()
            return AssignStmt(name_tok.value, value)
        elif self.at("LPAREN"):
            # Function call
            call = self.parse_call(name_tok.value)
            return ExprStmt(call)
        else:
            # Just a variable reference as a statement (unusual but valid)
            return ExprStmt(VarRef(name_tok.value))

    def parse_call(self, name):
        self.consume("LPAREN")
        args = []
        if not self.at("RPAREN"):
            args.append(self.parse_expression())
            while self.at("COMMA"):
                self.consume()
                args.append(self.parse_expression())
        self.consume("RPAREN")
        return CallExpr(name, args)

    # --- Expression parsing (precedence climbing) ---

    def parse_expression(self):
        """Expression with operator precedence: comparison > additive > multiplicative."""
        return self.parse_logical()

    def parse_logical(self):
        left = self.parse_comparison()
        while self.peek().kind in ("AND", "OR"):
            op = self.consume().kind.lower()
            right = self.parse_comparison()
            left = BinaryOp(op, left, right)
        return left

    def parse_comparison(self):
        left = self.parse_additive()
        while self.peek().kind in COMPARISON_OPS:
            op = self.consume().kind.lower()
            right = self.parse_additive()
            left = BinaryOp(op, left, right)
        return left

    def parse_additive(self):
        left = self.parse_multiplicative()
        while self.peek().kind in ADDITIVE_OPS:
            op = self.consume().kind.lower()
            right = self.parse_multiplicative()
            left = BinaryOp(op, left, right)
        return left

    def parse_multiplicative(self):
        left = self.parse_unary()
        while self.peek().kind in MULTIPLICATIVE_OPS:
            op = self.consume().kind.lower()
            right = self.parse_unary()
            left = BinaryOp(op, left, right)
        return left

    def parse_unary(self):
        if self.at("SUB"):
            self.consume()
            operand = self.parse_primary()
            return UnaryOp("neg", operand)
        if self.at("NOT"):
            self.consume()
            operand = self.parse_primary()
            return UnaryOp("not", operand)
        return self.parse_primary()

    def parse_primary(self):
        tok = self.peek()

        if tok.kind == "INT_LIT":
            self.consume()
            return IntLiteral(tok.value)

        if tok.kind == "TRUE":
            self.consume()
            return BoolLiteral(True)

        if tok.kind == "FALSE":
            self.consume()
            return BoolLiteral(False)

        if tok.kind == "IDENT":
            name = self.consume().value
            if self.at("LPAREN"):
                return self.parse_call(name)
            return VarRef(name)

        if tok.kind == "LPAREN":
            self.consume()
            expr = self.parse_expression()
            self.consume("RPAREN")
            return expr

        raise SyntaxError(
            f"Unexpected token {tok.kind} (value={tok.value!r}) "
            f"at position {self.pos}"
        )


# =============================================================================
# STAGE 3: IR GENERATOR
# =============================================================================
# Walks the AST and emits LLVM IR text.
# Each AST node type has a corresponding generation method.

class IRGenerator:
    def __init__(self):
        self.lines = []
        self.temp_count = 0
        self.label_count = 0
        self.local_vars = {}  # name -> LLVM alloca register
        self.has_printf = False

    def new_temp(self):
        self.temp_count += 1
        return f"%t{self.temp_count}"

    def new_label(self, prefix="L"):
        self.label_count += 1
        return f"{prefix}{self.label_count}"

    def emit(self, line):
        self.lines.append(line)

    # --- Top-level generation ---

    def generate_program(self, statements):
        """Generate a complete LLVM IR module."""
        # Collect function definitions and top-level statements
        functions = []
        main_stmts = []
        for stmt in statements:
            if isinstance(stmt, FunctionDef):
                functions.append(stmt)
            else:
                main_stmts.append(stmt)

        # Generate each function
        for func in functions:
            self.gen_function(func)

        # If there are top-level statements, wrap them in main()
        if main_stmts:
            main = FunctionDef("main", [], main_stmts, return_type="i32")
            main.is_main = True
            self.gen_function(main)

        # Add printf declaration if needed
        header = []
        header.append("; Jalekon Compiler Output")
        header.append("; Generated by jalekon_compiler.py")
        header.append("")
        if self.has_printf:
            header.append(
                '@.fmt_int = private unnamed_addr constant [4 x i8] '
                'c"%d\\0A\\00"'
            )
            header.append(
                "declare i32 @printf(ptr, ...)"
            )
            header.append("")

        return "\n".join(header + self.lines) + "\n"

    # --- Function generation ---

    def gen_function(self, node):
        self.temp_count = 0
        self.local_vars = {}

        is_main = getattr(node, "is_main", False)
        ret_type = "i32" if is_main else "i64"

        # Function signature
        if node.params:
            params_str = ", ".join(f"i64 %{p[0]}" for p in node.params)
        else:
            params_str = ""

        self.emit(f"define {ret_type} @{node.name}({params_str}) {{")
        self.emit("entry:")

        # Allocate space for parameters (so they can be reassigned)
        for pname, ptype in node.params:
            alloca = self.new_temp()
            self.emit(f"  {alloca} = alloca i64")
            self.emit(f"  store i64 %{pname}, ptr {alloca}")
            self.local_vars[pname] = alloca

        # Generate body
        for stmt in node.body:
            self.gen_statement(stmt)

        # If the last statement wasn't a return, add one
        if not node.body or not isinstance(node.body[-1], ReturnStmt):
            if is_main:
                self.emit("  ret i32 0")
            else:
                self.emit("  ret i64 0")

        self.emit("}")
        self.emit("")

    # --- Statement generation ---

    def gen_statement(self, node):
        if isinstance(node, ReturnStmt):
            self.gen_return(node)
        elif isinstance(node, IfStmt):
            self.gen_if(node)
        elif isinstance(node, WhileStmt):
            self.gen_while(node)
        elif isinstance(node, AssignStmt):
            self.gen_assign(node)
        elif isinstance(node, VarDeclStmt):
            self.gen_var_decl(node)
        elif isinstance(node, ExprStmt):
            self.gen_expr_stmt(node)

    def gen_return(self, node):
        val = self.gen_expression(node.value)
        self.emit(f"  ret i64 {val}")

    def gen_if(self, node):
        cond = self.gen_expression(node.condition)
        then_label = self.new_label("then")
        else_label = self.new_label("else")
        end_label = self.new_label("endif")

        # Branch
        self.emit(f"  br i1 {cond}, label %{then_label}, label %{else_label}")

        # Then block
        self.emit(f"{then_label}:")
        for stmt in node.then_body:
            self.gen_statement(stmt)
        if not node.then_body or not isinstance(node.then_body[-1], ReturnStmt):
            self.emit(f"  br label %{end_label}")

        # Else block
        self.emit(f"{else_label}:")
        if node.else_body:
            for stmt in node.else_body:
                self.gen_statement(stmt)
            if not isinstance(node.else_body[-1], ReturnStmt):
                self.emit(f"  br label %{end_label}")
        else:
            self.emit(f"  br label %{end_label}")

        # End
        self.emit(f"{end_label}:")

    def gen_while(self, node):
        cond_label = self.new_label("while_cond")
        body_label = self.new_label("while_body")
        end_label = self.new_label("while_end")

        self.emit(f"  br label %{cond_label}")

        # Condition check
        self.emit(f"{cond_label}:")
        cond = self.gen_expression(node.condition)
        self.emit(f"  br i1 {cond}, label %{body_label}, label %{end_label}")

        # Body
        self.emit(f"{body_label}:")
        for stmt in node.body:
            self.gen_statement(stmt)
        self.emit(f"  br label %{cond_label}")

        # End
        self.emit(f"{end_label}:")

    def gen_assign(self, node):
        val = self.gen_expression(node.value)
        if node.name not in self.local_vars:
            # First assignment — allocate
            alloca = self.new_temp()
            self.emit(f"  {alloca} = alloca i64")
            self.local_vars[node.name] = alloca
        self.emit(f"  store i64 {val}, ptr {self.local_vars[node.name]}")

    def gen_var_decl(self, node):
        alloca = self.new_temp()
        self.emit(f"  {alloca} = alloca i64")
        self.local_vars[node.name] = alloca
        if node.value is not None:
            val = self.gen_expression(node.value)
            self.emit(f"  store i64 {val}, ptr {alloca}")

    def gen_expr_stmt(self, node):
        if isinstance(node.expr, PrintCall):
            self.gen_print(node.expr)
        elif isinstance(node.expr, CallExpr):
            self.gen_expression(node.expr)
        # Other expression statements are just evaluated and discarded

    def gen_print(self, node):
        self.has_printf = True
        for arg in node.args:
            val = self.gen_expression(arg)
            result = self.new_temp()
            self.emit(
                f"  {result} = call i32 (ptr, ...) @printf("
                f"ptr @.fmt_int, i64 {val})"
            )

    # --- Expression generation ---

    def gen_expression(self, node):
        """Generate code for an expression, return the LLVM value (register or constant)."""
        if isinstance(node, IntLiteral):
            return str(node.value)

        if isinstance(node, BoolLiteral):
            return "1" if node.value else "0"

        if isinstance(node, VarRef):
            if node.name not in self.local_vars:
                raise NameError(f"Undefined variable: {node.name}")
            result = self.new_temp()
            self.emit(f"  {result} = load i64, ptr {self.local_vars[node.name]}")
            return result

        if isinstance(node, BinaryOp):
            return self.gen_binary_op(node)

        if isinstance(node, UnaryOp):
            return self.gen_unary_op(node)

        if isinstance(node, CallExpr):
            return self.gen_call(node)

        raise TypeError(f"Unknown expression type: {type(node).__name__}")

    def gen_binary_op(self, node):
        left = self.gen_expression(node.left)
        right = self.gen_expression(node.right)
        result = self.new_temp()

        # Arithmetic operators → LLVM instructions
        arith_ops = {
            "add": "add",
            "sub": "sub",
            "mul": "mul",
            "div": "sdiv",
            "idiv": "sdiv",
            "mod": "srem",
        }

        # Comparison operators → LLVM icmp
        cmp_ops = {
            "eq":  "eq",
            "neq": "ne",
            "lt":  "slt",
            "gt":  "sgt",
            "lte": "sle",
            "gte": "sge",
        }

        if node.op in arith_ops:
            self.emit(f"  {result} = {arith_ops[node.op]} i64 {left}, {right}")
            return result

        if node.op in cmp_ops:
            cmp_result = self.new_temp()
            self.emit(
                f"  {cmp_result} = icmp {cmp_ops[node.op]} i64 {left}, {right}"
            )
            # icmp returns i1 (1-bit boolean) — that's what we need for branches
            return cmp_result

        if node.op == "and":
            self.emit(f"  {result} = and i1 {left}, {right}")
            return result

        if node.op == "or":
            self.emit(f"  {result} = or i1 {left}, {right}")
            return result

        raise ValueError(f"Unknown operator: {node.op}")

    def gen_unary_op(self, node):
        operand = self.gen_expression(node.operand)
        result = self.new_temp()
        if node.op == "neg":
            self.emit(f"  {result} = sub i64 0, {operand}")
        elif node.op == "not":
            self.emit(f"  {result} = xor i1 {operand}, 1")
        return result

    def gen_call(self, node):
        args = [self.gen_expression(arg) for arg in node.args]
        args_str = ", ".join(f"i64 {a}" for a in args)
        result = self.new_temp()
        self.emit(f"  {result} = call i64 @{node.name}({args_str})")
        return result


# =============================================================================
# HELPER: Build Jalekon byte sequences programmatically
# =============================================================================

def jalekon_ident(name):
    """Encode an identifier: LIT_IDENT + ascii bytes + SPACE."""
    return bytes([LIT_IDENT]) + name.encode("ascii") + bytes([SPACE])


def jalekon_int(value):
    """Encode an integer literal."""
    if value == 0:
        return bytes([LIT_0])
    elif value == 1:
        return bytes([LIT_1])
    elif value == 2:
        return bytes([LIT_2])
    elif value == -1:
        return bytes([LIT_NEG1])
    else:
        return bytes([LIT_INT_FOLLOWS]) + struct.pack("<q", value)


# =============================================================================
# BUILT-IN TESTS
# =============================================================================

def test_add_function():
    """
    Test: def add(a, b): return a + b

    This is the simplest possible Jalekon program — a function that
    adds two numbers and returns the result.
    """
    print("=" * 60)
    print("TEST: add(a, b) -> a + b")
    print("=" * 60)

    # Build the Jalekon byte sequence
    program = bytes([
        KW_FUNC,                    # def
    ]) + jalekon_ident("add") + bytes([
        ST_LPAREN,                  # (
    ]) + jalekon_ident("a") + bytes([
        ST_COMMA,                   # ,
    ]) + jalekon_ident("b") + bytes([
        ST_RPAREN,                  # )
        ST_COLON,                   # :
        ST_NEWLINE,                 # \n
        ST_INDENT,                  # enter body
        KW_RETURN,                  # return
    ]) + jalekon_ident("a") + bytes([
        OP_ADD,                     # +
    ]) + jalekon_ident("b") + bytes([
        ST_NEWLINE,                 # \n
        ST_DEDENT,                  # exit body
    ])

    print(f"\nJalekon bytes ({len(program)} bytes):")
    print(" ".join(f"{b:02X}" for b in program))

    # Stage 1: Lex
    tokens = lex(program)
    print(f"\nTokens ({len(tokens)}):")
    for t in tokens:
        print(f"  {t}")

    # Stage 2: Parse
    parser = Parser(tokens)
    ast = parser.parse_program()
    print(f"\nAST:")
    for node in ast:
        print(f"  FunctionDef(name={node.name!r}, params={node.params})")

    # Stage 3: Generate LLVM IR
    gen = IRGenerator()
    ir = gen.generate_program(ast)
    print(f"\nLLVM IR:")
    print(ir)

    return ir


def test_max_function():
    """
    Test: def max(a, b):
              if a > b: return a
              else: return b
    """
    print("=" * 60)
    print("TEST: max(a, b) with if/else")
    print("=" * 60)

    program = bytes([
        KW_FUNC,
    ]) + jalekon_ident("max") + bytes([
        ST_LPAREN,
    ]) + jalekon_ident("a") + bytes([
        ST_COMMA,
    ]) + jalekon_ident("b") + bytes([
        ST_RPAREN,
        ST_COLON,
        ST_NEWLINE,
        ST_INDENT,
        # if a > b:
        KW_IF,
    ]) + jalekon_ident("a") + bytes([
        OP_GT,
    ]) + jalekon_ident("b") + bytes([
        ST_COLON,
        ST_NEWLINE,
        ST_INDENT,
        KW_RETURN,
    ]) + jalekon_ident("a") + bytes([
        ST_NEWLINE,
        ST_DEDENT,
        # else:
        KW_ELSE,
        ST_COLON,
        ST_NEWLINE,
        ST_INDENT,
        KW_RETURN,
    ]) + jalekon_ident("b") + bytes([
        ST_NEWLINE,
        ST_DEDENT,
        ST_DEDENT,
    ])

    print(f"\nJalekon bytes ({len(program)} bytes):")
    print(" ".join(f"{b:02X}" for b in program))

    tokens = lex(program)
    parser = Parser(tokens)
    ast = parser.parse_program()

    gen = IRGenerator()
    ir = gen.generate_program(ast)
    print(f"\nLLVM IR:")
    print(ir)

    return ir


def test_factorial():
    """
    Test: def factorial(n):
              if n <= 1: return 1
              return n * factorial(n - 1)
    """
    print("=" * 60)
    print("TEST: factorial(n) — recursion")
    print("=" * 60)

    program = bytes([
        KW_FUNC,
    ]) + jalekon_ident("factorial") + bytes([
        ST_LPAREN,
    ]) + jalekon_ident("n") + bytes([
        ST_RPAREN,
        ST_COLON,
        ST_NEWLINE,
        ST_INDENT,
        # if n <= 1:
        KW_IF,
    ]) + jalekon_ident("n") + bytes([
        OP_LTE,
    ]) + bytes([LIT_1]) + bytes([
        ST_COLON,
        ST_NEWLINE,
        ST_INDENT,
        KW_RETURN,
        LIT_1,
        ST_NEWLINE,
        ST_DEDENT,
        # return n * factorial(n - 1)
        KW_RETURN,
    ]) + jalekon_ident("n") + bytes([
        OP_MUL,
    ]) + jalekon_ident("factorial") + bytes([
        ST_LPAREN,
    ]) + jalekon_ident("n") + bytes([
        OP_SUB,
        LIT_1,
        ST_RPAREN,
        ST_NEWLINE,
        ST_DEDENT,
    ])

    print(f"\nJalekon bytes ({len(program)} bytes):")
    print(" ".join(f"{b:02X}" for b in program))

    tokens = lex(program)
    parser = Parser(tokens)
    ast = parser.parse_program()

    gen = IRGenerator()
    ir = gen.generate_program(ast)
    print(f"\nLLVM IR:")
    print(ir)

    return ir


def test_with_main():
    """
    Test: Full program with main that calls functions and prints.

    def add(a, b): return a + b
    print(add(3, 4))
    """
    print("=" * 60)
    print("TEST: Full program with print(add(3, 4))")
    print("=" * 60)

    # def add(a, b): return a + b
    func_bytes = bytes([
        KW_FUNC,
    ]) + jalekon_ident("add") + bytes([
        ST_LPAREN,
    ]) + jalekon_ident("a") + bytes([
        ST_COMMA,
    ]) + jalekon_ident("b") + bytes([
        ST_RPAREN,
        ST_COLON,
        ST_NEWLINE,
        ST_INDENT,
        KW_RETURN,
    ]) + jalekon_ident("a") + bytes([
        OP_ADD,
    ]) + jalekon_ident("b") + bytes([
        ST_NEWLINE,
        ST_DEDENT,
    ])

    # print(add(3, 4))
    main_bytes = bytes([
        BI_PRINT,
        ST_LPAREN,
    ]) + jalekon_ident("add") + bytes([
        ST_LPAREN,
    ]) + jalekon_int(3) + bytes([
        ST_COMMA,
    ]) + jalekon_int(4) + bytes([
        ST_RPAREN,
        ST_RPAREN,
        ST_NEWLINE,
    ])

    program = func_bytes + main_bytes

    print(f"\nJalekon bytes ({len(program)} bytes):")
    print(" ".join(f"{b:02X}" for b in program))

    tokens = lex(program)
    print(f"\nTokens ({len(tokens)}):")
    for t in tokens:
        print(f"  {t}")

    parser = Parser(tokens)
    ast = parser.parse_program()

    gen = IRGenerator()
    ir = gen.generate_program(ast)
    print(f"\nLLVM IR:")
    print(ir)

    return ir


# =============================================================================
# MAIN
# =============================================================================

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python jalekon_compiler.py --test           Run built-in tests")
        print("  python jalekon_compiler.py input.jkn        Compile to LLVM IR")
        print("  python jalekon_compiler.py input.jkn -o out.ll")
        sys.exit(1)

    if sys.argv[1] == "--test":
        test_add_function()
        print()
        test_max_function()
        print()
        test_factorial()
        print()
        test_with_main()
        print()
        print("=" * 60)
        print("All tests completed.")
        print("=" * 60)
        return

    # Compile a .jkn file
    input_path = sys.argv[1]
    with open(input_path, "rb") as f:
        data = f.read()

    tokens = lex(data)
    parser = Parser(tokens)
    ast = parser.parse_program()
    gen = IRGenerator()
    ir = gen.generate_program(ast)

    if "-o" in sys.argv:
        out_idx = sys.argv.index("-o") + 1
        output_path = sys.argv[out_idx]
        with open(output_path, "w") as f:
            f.write(ir)
        print(f"LLVM IR written to {output_path}")
    else:
        print(ir)


if __name__ == "__main__":
    main()
