# Mathlete — Complete Mathematical Operator Research

## Author: Travis Edward Holley
## Architecture: Claude (Anthropic)
## Date: April 6, 2026

---

## 1. Minimal Complete Operator Sets — What Exists

### Theoretical Minimum: 1-2 Combinators (Unusable)

- **Iota combinator** (Chris Barker): Single combinator, Turing-complete. Unusable — every operation is an enormous combinator tree.
- **SK calculus** (Schonfinkel 1920, Curry 1930s): Two combinators. S x y z = x z (y z), K x y = x. Turing-complete. Also unusable in practice.
- **NAND alone** is functionally complete for Boolean logic (Post's theorem).

### Practical Minimum: ~50 Primitives (K Language)

Arthur Whitney's K language achieves the most compressed practical set: ~50 primitives, each a single ASCII character, heavily overloaded. K unifies arrays as nested lists, reducing rank-related operations.

### APL: ~80 Glyphs (The Gold Standard)

Iverson's APL uses ~80 glyphs, each with monadic (arity 1) and dyadic (arity 2) meanings. This covers arithmetic, comparison, logic, array manipulation, sorting, set operations, and higher-order operators (reduce, scan, inner/outer product).

### J Language: ~100+ Primitives

Extends APL with number theory (prime counting, factorization, GCD, LCM), complex numbers, polynomial operations, and matrix operations — all as single ASCII digraphs.

### Wolfram Language: ~6,600 Built-in Symbols

The ceiling — every named mathematical function gets its own symbol. The mathematical subset runs into thousands.

### Assessment for Mathlete

| Level | Count | Coverage |
|-------|-------|----------|
| Theoretical minimum | 1-2 | Turing-complete, unusable |
| Practical minimum (K) | ~50 | Core computation |
| Working math system (APL/J) | ~80-100 | All common math |
| Full practical coverage | ~300-500 | All branches of mathematics |
| Exhaustive (Wolfram) | ~6,600 | Every named function |

**Target for Mathlete: 256 single-byte codes.** Between APL's 80 and full coverage at 500. One byte per operator. Fits in 8 bits. The sweet spot.

---

## 2. Complete Operator Enumeration by Category

### 2.1 Arithmetic & Elementary

| Operation | Arity | Primitive? | Notes |
|-----------|-------|-----------|-------|
| add | 2 | YES | Fundamental |
| negate | 1 | YES | Additive inverse |
| multiply | 2 | YES | Fundamental |
| reciprocal | 1 | YES | Multiplicative inverse |
| power | 2 | YES | Cannot reduce further |
| mod | 2 | YES | Fundamental |
| abs | 1 | YES | Fundamental |
| floor | 1 | YES | Fundamental |
| factorial | 1 | YES | n! |
| ln | 1 | YES | Inverse of exp |
| subtract | 2 | NO | add(x, negate(y)) |
| divide | 2 | NO | multiply(x, reciprocal(y)) |
| sqrt | 1 | NO | power(x, 0.5) |
| cbrt | 1 | NO | power(x, 1/3) |
| root | 2 | NO | power(x, reciprocal(n)) |
| exp | 1 | NO | power(e, x) |
| log | 2 | NO | divide(ln(x), ln(base)) |
| log2 | 1 | NO | divide(ln(x), ln(2)) |
| log10 | 1 | NO | divide(ln(x), ln(10)) |
| sign | 1 | NO | divide(x, abs(x)) |
| ceil | 1 | NO | negate(floor(negate(x))) |
| round | 1 | NO | floor(add(x, 0.5)) |
| max | 2 | NO | Derivable from comparison |
| min | 2 | NO | Derivable from comparison |
| binomial | 2 | NO | factorial compositions |

### 2.2 Comparison & Logic

| Operation | Arity | Primitive? |
|-----------|-------|-----------|
| equal | 2 | YES |
| less_than | 2 | YES |
| not | 1 | YES |
| and | 2 | YES |
| nand | 2 | YES (alone is complete) |
| forall | 2 | YES (predicate, domain) |
| not_equal | 2 | NO (not(equal)) |
| greater_than | 2 | NO (less_than swapped) |
| less_equal | 2 | NO |
| greater_equal | 2 | NO |
| or | 2 | NO (De Morgan) |
| xor | 2 | NO |
| implies | 2 | NO (or(not(a), b)) |
| biconditional | 2 | NO |
| exists | 2 | NO (not(forall(not(p)))) |

### 2.3 Trigonometric & Hyperbolic

| Operation | Arity | Primitive? |
|-----------|-------|-----------|
| sin | 1 | YES |
| arcsin | 1 | YES |
| arctan | 1 | YES |
| atan2 | 2 | YES (two-argument) |
| cos | 1 | NO (sin(pi/2 - x)) |
| tan | 1 | NO (sin/cos) |
| arccos | 1 | NO (pi/2 - arcsin) |
| sinh | 1 | NO ((exp(x)-exp(-x))/2) |
| cosh | 1 | NO |
| tanh | 1 | NO |
| arcsinh | 1 | NO |
| arccosh | 1 | NO |
| arctanh | 1 | NO |

### 2.4 Complex Numbers

| Operation | Arity | Primitive? |
|-----------|-------|-----------|
| complex | 2 | YES (constructor: re, im) |
| real_part | 1 | YES |
| imag_part | 1 | YES |
| argument | 1 | YES (angle) |
| conjugate | 1 | NO (complex(re, negate(im))) |
| modulus | 1 | NO (sqrt(re^2 + im^2)) |

### 2.5 Calculus

| Operation | Arity | Primitive? |
|-----------|-------|-----------|
| derivative | 2 | YES (function, variable) |
| integral_indefinite | 2 | YES (function, variable) |
| integral_definite | 4 | YES (function, var, lower, upper) |
| limit | 3 | YES (function, variable, point) |
| summation | 4 | YES (expr, var, lower, upper) |
| product_sum | 4 | YES (expr, var, lower, upper) |
| gradient | 1 | YES (vector of partials) |
| hessian | 1 | YES (matrix of 2nd partials) |
| jacobian | 1 | YES (matrix of 1st partials) |
| partial_derivative | 3 | NO (derivative with multi-var) |
| divergence | 1 | NO (trace of Jacobian) |
| curl | 1 | NO (specific cross-product) |
| laplacian | 1 | NO (divergence(gradient)) |
| series_taylor | 3 | NO (composed from derivatives) |

### 2.6 Linear Algebra / Matrix

| Operation | Arity | Primitive? |
|-----------|-------|-----------|
| matrix_multiply | 2 | YES |
| transpose | 1 | YES |
| determinant | 1 | YES |
| eigenvalues | 1 | YES |
| eigenvectors | 1 | YES |
| cross_product | 2 | YES (3D specific) |
| outer_product | 2 | YES |
| kronecker_product | 2 | YES |
| norm | 2 | YES (vector, p) |
| lu_decompose | 1 | YES |
| qr_decompose | 1 | YES |
| svd | 1 | YES |
| inverse | 1 | NO (adjugate/determinant) |
| trace | 1 | NO (sum of diagonal) |
| rank | 1 | NO (from row reduction) |
| dot_product | 2 | NO (sum of elementwise multiply) |
| solve_linear | 2 | NO (inverse(A)*b) |
| cholesky | 1 | NO (special decomposition) |
| pseudoinverse | 1 | NO (from SVD) |

### 2.7 Tensor / Multilinear Algebra

| Operation | Arity | Primitive? |
|-----------|-------|-----------|
| tensor_product | 2 | YES |
| tensor_contract | 3 | YES (tensor, index1, index2) |

### 2.8 Number Theory

| Operation | Arity | Primitive? |
|-----------|-------|-----------|
| gcd | 2 | YES |
| is_prime | 1 | YES |
| nth_prime | 1 | YES |
| factor | 1 | YES (prime factorization) |
| jacobi_symbol | 2 | YES |
| lcm | 2 | NO (multiply(a,b)/gcd(a,b)) |
| totient | 1 | NO (from factorization) |
| divisors | 1 | NO |
| moebius_mu | 1 | NO |
| mod_inverse | 2 | NO (extended GCD) |
| mod_power | 3 | NO (repeated squaring) |

### 2.9 Combinatorics

| Operation | Arity | Primitive? |
|-----------|-------|-----------|
| partition_count | 1 | YES (no closed form) |
| stirling_first | 2 | YES |
| stirling_second | 2 | YES |
| bell_number | 1 | NO (sum of Stirling 2nd) |
| catalan_number | 1 | NO (from binomial) |

### 2.10 Set Theory

| Operation | Arity | Primitive? |
|-----------|-------|-----------|
| member | 2 | YES |
| union | 2 | YES |
| complement | 1 | YES |
| cartesian_product | 2 | YES |
| power_set | 1 | YES |
| cardinality | 1 | YES |
| empty_set | 0 | YES (constant) |
| intersection | 2 | NO |
| difference | 2 | NO |
| subset | 2 | NO |

### 2.11 Graph Theory

| Operation | Arity | Primitive? |
|-----------|-------|-----------|
| graph | 2 | YES (constructor: V, E) |
| vertices | 1 | YES |
| edges | 1 | YES |
| adjacency_matrix | 1 | YES |
| degree | 2 | YES (graph, vertex) |
| neighbors | 2 | YES |
| shortest_path | 3 | YES |
| connected_components | 1 | YES |
| chromatic_number | 1 | YES |
| matching_max | 1 | YES |
| spanning_tree_min | 1 | YES |
| is_planar | 1 | YES |
| graph_complement | 1 | YES |
| graph_union | 2 | YES |
| subgraph | 2 | YES |
| isomorphic | 2 | YES |
| clique_max | 1 | YES |

### 2.12 Optimization

| Operation | Arity | Primitive? |
|-----------|-------|-----------|
| minimize | 2-3 | YES (function, variable, [constraints]) |
| gradient | 1 | YES (already in calculus) |
| hessian | 1 | YES (already in calculus) |
| linear_program | 3 | YES (objective, constraints, bounds) |
| convex_hull | 1 | YES |
| maximize | 2-3 | NO (negate + minimize) |

### 2.13 Differential Equations

| Operation | Arity | Primitive? |
|-----------|-------|-----------|
| ode_solve | 3+ | YES (equation, function, variable) |
| pde_solve | 3+ | YES |
| laplace_transform | 2 | YES |
| inverse_laplace | 2 | YES |
| fourier_transform | 2 | YES |
| inverse_fourier | 2 | YES |
| z_transform | 2 | YES |
| inverse_z_transform | 2 | YES |

### 2.14 Signal Processing

| Operation | Arity | Primitive? |
|-----------|-------|-----------|
| fft | 1 | YES |
| ifft | 1 | YES |
| convolve | 2 | YES |
| filter_apply | 2 | YES |
| downsample | 2 | YES |
| upsample | 2 | YES |
| correlate | 2 | NO (convolve with reversed) |

### 2.15 Information Theory

| Operation | Arity | Primitive? |
|-----------|-------|-----------|
| entropy | 1 | YES |
| cross_entropy | 2 | YES |
| joint_entropy | 2 | YES |
| kl_divergence | 2 | NO |
| mutual_information | 2 | NO |

### 2.16 Probability & Statistics

| Operation | Arity | Primitive? |
|-----------|-------|-----------|
| probability | 2 | YES (event, space) |
| expected_value | 2 | YES (function, distribution) |
| sample | 2 | YES (distribution, count) |
| pdf | 2 | YES (distribution, point) |
| cdf | 2 | YES (distribution, point) |
| quantile | 2 | YES (distribution, probability) |
| variance | 2 | NO (E[X^2] - E[X]^2) |
| std_deviation | 2 | NO (sqrt(variance)) |
| covariance | 3 | NO |
| conditional_prob | 3 | NO |

### 2.17 Special Functions

| Operation | Arity | Primitive? |
|-----------|-------|-----------|
| gamma | 1 | YES |
| zeta | 1 | YES (Riemann) |
| erf | 1 | YES (error function) |
| bessel_j | 2 | YES (order, argument) |
| bessel_y | 2 | YES |
| legendre_p | 2 | YES |
| chebyshev_t | 2 | YES |
| hermite_h | 2 | YES |
| laguerre_l | 2 | YES |
| hypergeometric | 4+ | YES (generalized) |
| elliptic_k | 1 | YES |
| elliptic_e | 1 | YES |
| airy_ai | 1 | YES |
| dirac_delta | 1 | YES |
| polylog | 2 | YES |
| beta | 2 | NO (gamma compositions) |
| heaviside | 1 | NO (integral of delta) |

### 2.18 Abstract Algebra

| Operation | Arity | Primitive? |
|-----------|-------|-----------|
| group_op | 2 | YES |
| group_identity | 1 | YES |
| group_inverse | 2 | YES |
| group_order | 1 | YES |
| homomorphism | 3 | YES |
| kernel | 1 | YES |
| image | 1 | YES |
| quotient_group | 2 | YES |
| direct_product | 2 | YES |
| ring_multiply | 2 | YES |
| ideal_generate | 2 | YES |

### 2.19 Category Theory

| Operation | Arity | Primitive? |
|-----------|-------|-----------|
| compose | 2 | YES |
| identity_morphism | 1 | YES |
| source | 1 | YES |
| target | 1 | YES |
| functor_apply | 2 | YES |
| natural_transform | 3 | YES |
| pullback | 3 | YES |
| pushout | 3 | YES |
| limit_cat | 2 | YES |
| colimit | 2 | YES |
| adjoint_left | 1 | YES |
| adjoint_right | 1 | YES |

### 2.20 Topology

| Operation | Arity | Primitive? |
|-----------|-------|-----------|
| closure | 1 | YES |
| interior | 1 | YES |
| continuous | 1 | YES (predicate) |
| homeomorphic | 2 | YES (predicate) |
| fundamental_group | 2 | YES |
| homology_group | 2 | YES |
| homotopy_group | 2 | YES |
| compact | 1 | YES (predicate) |
| connected | 1 | YES (predicate) |
| boundary_top | 1 | NO (closure minus interior) |

### 2.21 Numerical Methods

| Operation | Arity | Primitive? |
|-----------|-------|-----------|
| interpolate | 3 | YES (points, method, target) |
| root_find | 2-3 | YES |
| iterate | 3 | YES (function, initial, count) |
| approximate | 2 | YES (expression, precision) |

### 2.22 Control / Structural

| Operation | Arity | Notes |
|-----------|-------|-------|
| if_then_else | 3 | Conditional |
| let_bind | 3 | Variable binding (name, value, body) |
| lambda | 2 | Function definition (param, body) |
| apply | 2 | Function application |

---

## 3. Constants (Arity 0)

| Name | Symbol | Value |
|------|--------|-------|
| pi | pi | 3.14159... |
| e | e | 2.71828... |
| i | i | sqrt(-1) |
| infinity | inf | positive infinity |
| neg_infinity | -inf | negative infinity |
| true | T | boolean |
| false | F | boolean |
| empty_set | {} | empty set |
| euler_gamma | gamma | 0.5772... |
| phi | phi | 1.6180... (golden ratio) |

---

## 4. Linearization Systems — Prior Art for Machines

### OpenMath Binary Encoding (Closest to Mathlete)

OpenMath has 218 Content Dictionaries covering all major math domains. It has a **binary encoding** designed for efficient machine exchange. Symbols reference Content Dictionaries (e.g., `arith1` contains: abs, divide, gcd, lcm, minus, plus, power, product, root, sum, times, unary_minus). This is the closest existing work to what we're building.

### Lean 4 Core Term Constructors

Lean 4 has 8 core term constructors: Var, Sort, Const, App, Lam, Pi, Let, Lit. All of mathematics in Lean reduces to these 8 primitives plus axiom definitions. This is the formal minimum for a dependently-typed proof system.

### Coq / Rocq

Same Calculus of Inductive Constructions as Lean. Sorts: SProp, Prop, Set, Type(i). Terms: variables, constants, abstraction, application, product, let-bindings, inductive types, match/fix.

### Metamath

Most minimalist: one proof rule (substitution). No built-in logic — everything from axioms. Proofs are sequences of label references. Extremely compact.

### MathML Content Encoding

~120 elements representing operators. The `apply` element wraps operator + operands in prefix style. Essentially prefix notation serialized as XML.

### Key Insight on Math Tokenization

Research (2024) shows tokenization significantly impacts arithmetic performance. Right-to-left tokenization improves addition accuracy. Different digit groupings create systematic error patterns. **Our byte-per-concept approach avoids all of these tokenization artifacts** because each operation is one byte, each digit is one byte. No tokenization ambiguity.

---

## 5. Training Data Sources

### Structured Problem/Solution Datasets

| Dataset | Size | Content |
|---------|------|---------|
| GSM8K | 8.5K problems | Grade school word problems, 2-8 step solutions |
| MATH (Hendrycks) | 12,500 problems | Competition math (AMC 10/12, AIME), LaTeX solutions, difficulty-rated |
| AMPS | 23 GB | Khan Academy (693 exercise types) + Mathematica-generated (5M+ problems) |
| MathQA | 37K problems | GRE/GMAT-style with operation programs |
| OpenMathInstruct-1 | 1.8M pairs | Synthesized from GSM8K/MATH |
| NuminaMath | 152K pairs | Olympiad-level |

### Large-Scale Pretraining Corpora

| Dataset | Size | Content |
|---------|------|---------|
| Proof-Pile-2 | 55B tokens | Scientific papers, math web, math code |
| OpenWebMath | 14.7B tokens | Math web pages from Common Crawl |
| AlgebraicStack | 11B tokens | Math code (Python, C++, Lean, Isabelle) |

### Formal Mathematics

| Dataset | Content |
|---------|---------|
| Lean's Mathlib | Largest formalized math library |
| Isabelle/AFP | Archive of Formal Proofs |
| Metamath set.mm | One of largest formal proof databases |

### Synthetic Generation

- AMPS Mathematica modules: 100 hand-designed problem generators
- Khan Academy: 693 exercise types, programmatically structured
- These are the most relevant for Mathlete — we can generate unlimited equation/answer pairs

---

## 6. Byte Budget Recommendation

256 single-byte codes allocated as:

| Range | Count | Contents |
|-------|-------|----------|
| 0x00-0x0F | 16 | Constants and structural (END, digits, pi, e, i, inf, true, false) |
| 0x10-0x5F | 80 | Core primitives (arithmetic, logic, comparison, trig, calculus, linear algebra) |
| 0x60-0x9F | 64 | Extended math (number theory, combinatorics, abstract algebra, topology, graph theory, optimization, signal, info theory) |
| 0xA0-0xCF | 48 | Special functions and transforms (Bessel, Legendre, Fourier, Laplace, etc.) |
| 0xD0-0xEF | 32 | Statistics, probability, numerical methods |
| 0xF0-0xFE | 15 | Structural/control (VAR, let-bind, lambda, apply, vector constructors) |
| 0xFF | 1 | Extension byte (prefix for 256 more second-byte opcodes if needed) |

**Key design decisions:**
1. Fixed arity per opcode makes prefix notation unambiguous — no brackets needed
2. Variadic operations need a count byte immediately after the opcode
3. ~80 truly primitive operations form the irreducible core; everything else composes
4. OpenMath's 218 content dictionaries validate that 200-300 operations cover practical mathematics

---

## Sources

- APL Primitive Functions — APL Wiki
- J Language Vocabulary/Verbs
- SKI Combinator Calculus — Wikipedia
- Functional Completeness (Post's Theorem) — Wikipedia
- Wolfram Mathematical Functions Reference
- OpenMath Content Dictionaries and Standard (om20-2019-07-01)
- ISO 80000-2:2019 (mathematical notation standard)
- Polish Notation — Wikipedia
- Lean 4 Type System documentation
- Coq CIC Reference
- Metamath — Wikipedia
- MATH Dataset (Hendrycks et al., NeurIPS 2021)
- GSM8K — HuggingFace
- Llemma Paper (arXiv:2310.10631)
- Proof-Pile-2 — HuggingFace/EleutherAI
- OpenWebMath Paper (arXiv:2310.06786)
- Tokenization Impact on Arithmetic (arXiv:2402.14903)

---

*Travis Edward Holley*
*TNT Holley, Inc.*
*April 6, 2026*
