# Mathlete Byte Table — Draft v0.1

## Author: Travis Edward Holley
## Architecture: Claude (Anthropic)
## Date: April 6, 2026

---

## Rules

1. Control bytes 0x00-0x09 reserved — same positions as JalekCore
2. Digits 0x0A-0x13 + decimal 0x14 — same as JalekCore
3. Letters 0x15-0x34 — same as JalekCore (32 slots)
4. Math operators fill 0x35-0xFF (203 slots) — grouped by domain
5. Related operations sit together in the table
6. 2-byte codes (0x35-0xFF as first byte, 0x0A-0xFF as second byte) for extended operations
7. Every operator has FIXED ARITY — prefix notation, no parentheses needed
8. Arity determines how many operands the model expects after seeing the operator

---

## TIER 0 — Control Bytes (0x00-0x09) — RESERVED

| Hex | Name | Purpose |
|-----|------|---------|
| 0x00 | END | End of sequence |
| 0x01 | BOUNDARY | Component separator |
| 0x02 | SPACE | Token separator |
| 0x03 | NEWLINE | Line break |
| 0x04 | PARAGRAPH | Paragraph break |
| 0x05 | Q/A | Equation -> Answer transition |
| 0x06 | SKIP | Attention-masked routing |
| 0x07 | JALEKON | Code mode toggle |
| 0x08 | NAME | Named constant/function prefix |
| 0x09 | COIN | Novel term prefix |

---

## TIER 1 — Digits & Decimal (0x0A-0x14)

| Hex | Symbol | Meaning |
|-----|--------|---------|
| 0x0A | 0 | zero |
| 0x0B | 1 | one |
| 0x0C | 2 | two |
| 0x0D | 3 | three |
| 0x0E | 4 | four |
| 0x0F | 5 | five |
| 0x10 | 6 | six |
| 0x11 | 7 | seven |
| 0x12 | 8 | eight |
| 0x13 | 9 | nine |
| 0x14 | . | decimal point |

---

## TIER 1 — Letters (0x15-0x34) — Variables

| Hex | Letter | Hex | Letter | Hex | Letter | Hex | Letter |
|-----|--------|-----|--------|-----|--------|-----|--------|
| 0x15 | a | 0x1D | g | 0x25 | m | 0x2D | u |
| 0x16 | b | 0x1E | h | 0x26 | n | 0x2E | v |
| 0x17 | c | 0x1F | i | 0x27 | o | 0x2F | w |
| 0x18 | d | 0x20 | j | 0x28 | p | 0x30 | x |
| 0x19 | e | 0x21 | k | 0x29 | q | 0x31 | y |
| 0x1A | f | 0x22 | l | 0x2A | r | 0x32 | z |
| 0x1B | unused | 0x23 | unused | 0x2B | s | 0x33 | unused |
| 0x1C | unused | 0x24 | unused | 0x2C | t | 0x34 | unused |

Note: 26 Roman letters for variables. 6 unused slots (from JalekCore Esperanto characters) available for Greek variable letters or reallocation. Candidates: alpha, beta, theta, lambda, sigma, omega.

---

## TIER 2 — Constants (0x35-0x3E) — Arity 0

| Hex | Name | Symbol | Value |
|-----|------|--------|-------|
| 0x35 | pi | pi | 3.14159... |
| 0x36 | euler | e | 2.71828... |
| 0x37 | imaginary | i | sqrt(-1) |
| 0x38 | infinity | inf | +inf |
| 0x39 | neg_infinity | -inf | -inf |
| 0x3A | true | T | boolean true |
| 0x3B | false | F | boolean false |
| 0x3C | empty_set | {} | empty set |
| 0x3D | euler_gamma | gamma | 0.57721... (Euler-Mascheroni) |
| 0x3E | golden_ratio | phi | 1.61803... |

---

## TIER 2 — Arithmetic (0x3F-0x53) — 21 operators

| Hex | Name | Arity | Example (prefix) | Result |
|-----|------|-------|-------------------|--------|
| 0x3F | add | 2 | add 3 5 | 8 |
| 0x40 | subtract | 2 | subtract 10 3 | 7 |
| 0x41 | multiply | 2 | multiply 4 6 | 24 |
| 0x42 | divide | 2 | divide 15 3 | 5 |
| 0x43 | power | 2 | power 2 10 | 1024 |
| 0x44 | mod | 2 | mod 17 5 | 2 |
| 0x45 | negate | 1 | negate 7 | -7 |
| 0x46 | reciprocal | 1 | reciprocal 4 | 0.25 |
| 0x47 | abs | 1 | abs negate 5 | 5 |
| 0x48 | floor | 1 | floor 3.7 | 3 |
| 0x49 | ceil | 1 | ceil 3.2 | 4 |
| 0x4A | round | 1 | round 3.5 | 4 |
| 0x4B | sqrt | 1 | sqrt 16 | 4 |
| 0x4C | cbrt | 1 | cbrt 27 | 3 |
| 0x4D | root | 2 | root 32 5 | 2 |
| 0x4E | factorial | 1 | factorial 5 | 120 |
| 0x4F | ln | 1 | ln euler | 1 |
| 0x50 | exp | 1 | exp 1 | 2.71828... |
| 0x51 | log | 2 | log 100 10 | 2 |
| 0x52 | max | 2 | max 3 7 | 7 |
| 0x53 | min | 2 | min 3 7 | 3 |

---

## TIER 2 — Comparison (0x54-0x59) — 6 operators, all arity 2

| Hex | Name | Example | Result |
|-----|------|---------|--------|
| 0x54 | equal | equal 3 3 | true |
| 0x55 | not_equal | not_equal 3 4 | true |
| 0x56 | less_than | less_than 2 5 | true |
| 0x57 | greater_than | greater_than 7 3 | true |
| 0x58 | less_equal | less_equal 3 3 | true |
| 0x59 | greater_equal | greater_equal 5 5 | true |

---

## TIER 2 — Logic (0x5A-0x62) — 9 operators

| Hex | Name | Arity | Example | Result |
|-----|------|-------|---------|--------|
| 0x5A | not | 1 | not true | false |
| 0x5B | and | 2 | and true false | false |
| 0x5C | or | 2 | or true false | true |
| 0x5D | xor | 2 | xor true true | false |
| 0x5E | nand | 2 | nand true true | false |
| 0x5F | implies | 2 | implies false true | true |
| 0x60 | iff | 2 | iff true true | true |
| 0x61 | forall | 2 | forall (pred) (domain) | T/F |
| 0x62 | exists | 2 | exists (pred) (domain) | T/F |

---

## TIER 2 — Trigonometry (0x63-0x6F) — 13 operators, all arity 1 except atan2

| Hex | Name | Arity | Notes |
|-----|------|-------|-------|
| 0x63 | sin | 1 | |
| 0x64 | cos | 1 | |
| 0x65 | tan | 1 | |
| 0x66 | arcsin | 1 | inverse sin |
| 0x67 | arccos | 1 | inverse cos |
| 0x68 | arctan | 1 | inverse tan |
| 0x69 | atan2 | 2 | two-argument arctan(y, x) |
| 0x6A | sinh | 1 | hyperbolic sin |
| 0x6B | cosh | 1 | hyperbolic cos |
| 0x6C | tanh | 1 | hyperbolic tan |
| 0x6D | arcsinh | 1 | inverse hyperbolic sin |
| 0x6E | arccosh | 1 | inverse hyperbolic cos |
| 0x6F | arctanh | 1 | inverse hyperbolic tan |

---

## TIER 2 — Calculus (0x70-0x7C) — 13 operators

| Hex | Name | Arity | Description |
|-----|------|-------|-------------|
| 0x70 | derivative | 2 | d/d(var) of expr |
| 0x71 | partial_deriv | 2 | partial derivative |
| 0x72 | integral_indef | 2 | indefinite integral (expr, var) |
| 0x73 | integral_def | 4 | definite integral (expr, var, lo, hi) |
| 0x74 | limit | 3 | limit (expr, var, point) |
| 0x75 | summation | 4 | sum (expr, var, lo, hi) |
| 0x76 | product_sum | 4 | product (expr, var, lo, hi) |
| 0x77 | gradient | 1 | vector of partials |
| 0x78 | hessian | 1 | matrix of 2nd partials |
| 0x79 | jacobian | 1 | matrix of 1st partials |
| 0x7A | divergence | 1 | div of vector field |
| 0x7B | curl | 1 | curl of vector field |
| 0x7C | laplacian | 1 | divergence of gradient |

---

## TIER 2 — Linear Algebra (0x7D-0x8F) — 19 operators

| Hex | Name | Arity | Description |
|-----|------|-------|-------------|
| 0x7D | mat_mul | 2 | matrix multiply |
| 0x7E | transpose | 1 | transpose |
| 0x7F | det | 1 | determinant |
| 0x80 | inverse | 1 | matrix inverse |
| 0x81 | trace | 1 | sum of diagonal |
| 0x82 | rank | 1 | matrix rank |
| 0x83 | eigenval | 1 | eigenvalues |
| 0x84 | eigenvec | 1 | eigenvectors |
| 0x85 | dot | 2 | dot product |
| 0x86 | cross | 2 | cross product (3D) |
| 0x87 | outer | 2 | outer product |
| 0x88 | kronecker | 2 | Kronecker product |
| 0x89 | norm | 2 | norm (vector, p) |
| 0x8A | solve_linear | 2 | solve Ax=b |
| 0x8B | lu | 1 | LU decomposition |
| 0x8C | qr | 1 | QR decomposition |
| 0x8D | svd | 1 | singular value decomposition |
| 0x8E | cholesky | 1 | Cholesky decomposition |
| 0x8F | pseudoinverse | 1 | Moore-Penrose pseudoinverse |

---

## TIER 2 — Complex Numbers (0x90-0x95) — 6 operators

| Hex | Name | Arity | Description |
|-----|------|-------|-------------|
| 0x90 | complex | 2 | construct from (real, imag) |
| 0x91 | real_part | 1 | extract real component |
| 0x92 | imag_part | 1 | extract imaginary component |
| 0x93 | conjugate | 1 | complex conjugate |
| 0x94 | cmodulus | 1 | complex modulus |
| 0x95 | argument | 1 | angle in polar form |

---

## TIER 2 — Set Theory (0x96-0xA1) — 12 operators

| Hex | Name | Arity | Description |
|-----|------|-------|-------------|
| 0x96 | member | 2 | element in set? |
| 0x97 | union | 2 | set union |
| 0x98 | intersect | 2 | set intersection |
| 0x99 | complement | 1 | set complement |
| 0x9A | set_diff | 2 | set difference |
| 0x9B | sym_diff | 2 | symmetric difference |
| 0x9C | subset | 2 | is subset? |
| 0x9D | proper_subset | 2 | is proper subset? |
| 0x9E | cartesian | 2 | Cartesian product |
| 0x9F | power_set | 1 | power set |
| 0xA0 | cardinality | 1 | number of elements |
| 0xA1 | set_build | 2 | set builder (pred, domain) |

---

## TIER 2 — Number Theory (0xA2-0xAC) — 11 operators

| Hex | Name | Arity | Description |
|-----|------|-------|-------------|
| 0xA2 | gcd | 2 | greatest common divisor |
| 0xA3 | lcm | 2 | least common multiple |
| 0xA4 | is_prime | 1 | primality test |
| 0xA5 | nth_prime | 1 | nth prime number |
| 0xA6 | factor | 1 | prime factorization |
| 0xA7 | totient | 1 | Euler's totient |
| 0xA8 | divisors | 1 | list of divisors |
| 0xA9 | mod_power | 3 | modular exponentiation (base, exp, mod) |
| 0xAA | mod_inverse | 2 | modular multiplicative inverse |
| 0xAB | jacobi | 2 | Jacobi symbol |
| 0xAC | moebius | 1 | Mobius mu function |

---

## TIER 2 — Combinatorics (0xAD-0xB4) — 8 operators

| Hex | Name | Arity | Description |
|-----|------|-------|-------------|
| 0xAD | binomial | 2 | n choose k |
| 0xAE | permute | 2 | P(n,k) permutation count |
| 0xAF | partition | 1 | partition count |
| 0xB0 | stirling1 | 2 | Stirling first kind |
| 0xB1 | stirling2 | 2 | Stirling second kind |
| 0xB2 | bell | 1 | Bell number |
| 0xB3 | catalan | 1 | Catalan number |
| 0xB4 | derange | 1 | derangement count |

---

## TIER 2 — Probability & Statistics (0xB5-0xC5) — 17 operators

| Hex | Name | Arity | Description |
|-----|------|-------|-------------|
| 0xB5 | prob | 2 | probability (event, space) |
| 0xB6 | expect | 2 | expected value (fn, dist) |
| 0xB7 | variance | 2 | variance (fn, dist) |
| 0xB8 | std_dev | 2 | standard deviation |
| 0xB9 | covar | 2 | covariance |
| 0xBA | corr | 2 | correlation |
| 0xBB | cond_prob | 3 | conditional P(A|B) |
| 0xBC | bayes | 3 | Bayesian update |
| 0xBD | sample | 2 | draw from distribution |
| 0xBE | pdf | 2 | probability density |
| 0xBF | cdf | 2 | cumulative distribution |
| 0xC0 | quantile | 2 | inverse CDF |
| 0xC1 | mean | 1 | arithmetic mean |
| 0xC2 | median | 1 | median |
| 0xC3 | mode | 1 | mode |
| 0xC4 | percentile | 2 | percentile (data, pct) |
| 0xC5 | zscore | 2 | z-score (value, dist) |

---

## TIER 2 — Transforms (0xC6-0xCF) — 10 operators, all arity 1-2

| Hex | Name | Arity | Description |
|-----|------|-------|-------------|
| 0xC6 | laplace | 2 | Laplace transform (fn, var) |
| 0xC7 | inv_laplace | 2 | inverse Laplace |
| 0xC8 | fourier | 2 | Fourier transform |
| 0xC9 | inv_fourier | 2 | inverse Fourier |
| 0xCA | z_transform | 2 | Z-transform |
| 0xCB | inv_z | 2 | inverse Z-transform |
| 0xCC | fft | 1 | fast Fourier transform |
| 0xCD | ifft | 1 | inverse FFT |
| 0xCE | convolve | 2 | convolution |
| 0xCF | correlate | 2 | correlation |

---

## TIER 2 — Differential Equations & Optimization (0xD0-0xD7) — 8 operators

| Hex | Name | Arity | Description |
|-----|------|-------|-------------|
| 0xD0 | ode_solve | 3 | solve ODE (eq, fn, var) |
| 0xD1 | pde_solve | 3 | solve PDE |
| 0xD2 | minimize | 2 | minimize (fn, var) |
| 0xD3 | maximize | 2 | maximize (fn, var) |
| 0xD4 | lin_prog | 3 | linear program (obj, constraints, bounds) |
| 0xD5 | root_find | 2 | find zeros of function |
| 0xD6 | interpolate | 3 | interpolate (points, method, target) |
| 0xD7 | iterate | 3 | iterate (fn, init, count) |

---

## TIER 2 — Information Theory (0xD8-0xDC) — 5 operators

| Hex | Name | Arity | Description |
|-----|------|-------|-------------|
| 0xD8 | entropy | 1 | Shannon entropy |
| 0xD9 | cross_entropy | 2 | cross entropy |
| 0xDA | kl_div | 2 | KL divergence |
| 0xDB | mutual_info | 2 | mutual information |
| 0xDC | joint_entropy | 2 | joint entropy |

---

## TIER 2 — Special Functions (0xDD-0xEC) — 16 operators

| Hex | Name | Arity | Description |
|-----|------|-------|-------------|
| 0xDD | gamma_fn | 1 | Gamma function |
| 0xDE | beta_fn | 2 | Beta function |
| 0xDF | zeta_fn | 1 | Riemann zeta |
| 0xE0 | erf | 1 | error function |
| 0xE1 | bessel_j | 2 | Bessel J (order, arg) |
| 0xE2 | bessel_y | 2 | Bessel Y (order, arg) |
| 0xE3 | legendre | 2 | Legendre P (degree, arg) |
| 0xE4 | chebyshev | 2 | Chebyshev T (degree, arg) |
| 0xE5 | hermite | 2 | Hermite H (degree, arg) |
| 0xE6 | laguerre | 2 | Laguerre L (degree, arg) |
| 0xE7 | hypergeo | 4 | hypergeometric 2F1(a,b,c,z) |
| 0xE8 | elliptic_k | 1 | complete elliptic K |
| 0xE9 | elliptic_e | 1 | complete elliptic E |
| 0xEA | airy | 1 | Airy Ai |
| 0xEB | dirac | 1 | Dirac delta |
| 0xEC | polylog | 2 | polylogarithm (order, arg) |

---

## TIER 2 — Structural (0xED-0xF5) — 9 codes

| Hex | Name | Arity | Description |
|-----|------|-------|-------------|
| 0xED | if_else | 3 | if_else condition true_val false_val |
| 0xEE | let | 3 | let var value body |
| 0xEF | lambda | 2 | lambda param body |
| 0xF0 | apply | 2 | apply fn arg |
| 0xF1 | vec_start | 0 | begin vector/matrix literal |
| 0xF2 | vec_end | 0 | end vector/matrix literal |
| 0xF3 | dim_sep | 0 | row separator in matrix |
| 0xF4 | count | 1 | variadic arity prefix (count N, then N operands) |
| 0xF5 | assign | 2 | assign var value |

---

## TIER 2 — Greek Variable Letters (0xF6-0xFF) — 10 slots

| Hex | Name | Usage |
|-----|------|-------|
| 0xF6 | alpha | angles, coefficients |
| 0xF7 | beta | angles, coefficients, distributions |
| 0xF8 | gamma_var | angles, Euler's constant (the variable, not the function) |
| 0xF9 | delta | change, small quantity |
| 0xFA | theta | angles, parameters |
| 0xFB | lambda_var | eigenvalues, wavelength (the variable, not the function) |
| 0xFC | mu | mean, micro |
| 0xFD | sigma_var | summation index, std dev (the variable, not the function) |
| 0xFE | omega | angular velocity, frequency |
| 0xFF | epsilon | small positive quantity, error bound |

---

## SINGLE-BYTE TOTALS

| Section | Range | Count |
|---------|-------|-------|
| Control bytes | 0x00-0x09 | 10 |
| Digits + decimal | 0x0A-0x14 | 11 |
| Roman letters | 0x15-0x34 | 32 (26 used, 6 free) |
| Constants | 0x35-0x3E | 10 |
| Arithmetic | 0x3F-0x53 | 21 |
| Comparison | 0x54-0x59 | 6 |
| Logic | 0x5A-0x62 | 9 |
| Trigonometry | 0x63-0x6F | 13 |
| Calculus | 0x70-0x7C | 13 |
| Linear algebra | 0x7D-0x8F | 19 |
| Complex numbers | 0x90-0x95 | 6 |
| Set theory | 0x96-0xA1 | 12 |
| Number theory | 0xA2-0xAC | 11 |
| Combinatorics | 0xAD-0xB4 | 8 |
| Probability/stats | 0xB5-0xC5 | 17 |
| Transforms | 0xC6-0xCF | 10 |
| DiffEq/Optimization | 0xD0-0xD7 | 8 |
| Information theory | 0xD8-0xDC | 5 |
| Special functions | 0xDD-0xEC | 16 |
| Structural | 0xED-0xF5 | 9 |
| Greek variables | 0xF6-0xFF | 10 |
| **TOTAL** | **0x00-0xFF** | **256** |

All 256 single-byte codes assigned. Zero waste.

---

## TWO-BYTE TIER — Extended Operations

Two-byte codes use any non-control first byte (0x0A-0xFF = 246 values) + any non-control second byte (0x0A-0xFF = 246 values) = 60,516 possible codes. More than enough.

### 2-Byte: Abstract Algebra

| Code | Name | Arity |
|------|------|-------|
| 0x3F 0x0A | group_op | 2 |
| 0x3F 0x0B | group_identity | 1 |
| 0x3F 0x0C | group_inverse | 2 |
| 0x3F 0x0D | group_order | 1 |
| 0x3F 0x0E | homomorphism | 3 |
| 0x3F 0x0F | kernel | 1 |
| 0x3F 0x10 | image | 1 |
| 0x3F 0x11 | quotient_group | 2 |
| 0x3F 0x12 | direct_product | 2 |
| 0x3F 0x13 | ring_multiply | 2 |
| 0x3F 0x14 | ideal_generate | 2 |
| 0x3F 0x15 | is_abelian | 1 |

### 2-Byte: Category Theory

| Code | Name | Arity |
|------|------|-------|
| 0x40 0x0A | compose | 2 |
| 0x40 0x0B | identity_morph | 1 |
| 0x40 0x0C | source | 1 |
| 0x40 0x0D | target | 1 |
| 0x40 0x0E | functor_apply | 2 |
| 0x40 0x0F | natural_transform | 3 |
| 0x40 0x10 | pullback | 3 |
| 0x40 0x11 | pushout | 3 |
| 0x40 0x12 | limit_cat | 2 |
| 0x40 0x13 | colimit | 2 |
| 0x40 0x14 | adjoint_left | 1 |
| 0x40 0x15 | adjoint_right | 1 |

### 2-Byte: Topology

| Code | Name | Arity |
|------|------|-------|
| 0x41 0x0A | closure | 1 |
| 0x41 0x0B | interior | 1 |
| 0x41 0x0C | boundary_top | 1 |
| 0x41 0x0D | continuous | 1 |
| 0x41 0x0E | homeomorphic | 2 |
| 0x41 0x0F | fund_group | 2 |
| 0x41 0x10 | homology | 2 |
| 0x41 0x11 | homotopy | 2 |
| 0x41 0x12 | compact | 1 |
| 0x41 0x13 | connected | 1 |
| 0x41 0x14 | euler_char | 1 |

### 2-Byte: Graph Theory

| Code | Name | Arity |
|------|------|-------|
| 0x42 0x0A | graph | 2 |
| 0x42 0x0B | vertices | 1 |
| 0x42 0x0C | edges | 1 |
| 0x42 0x0D | adj_matrix | 1 |
| 0x42 0x0E | degree | 2 |
| 0x42 0x0F | neighbors | 2 |
| 0x42 0x10 | shortest_path | 3 |
| 0x42 0x11 | components | 1 |
| 0x42 0x12 | chromatic | 1 |
| 0x42 0x13 | max_matching | 1 |
| 0x42 0x14 | min_span_tree | 1 |
| 0x42 0x15 | is_bipartite | 1 |
| 0x42 0x16 | is_planar | 1 |
| 0x42 0x17 | graph_complement | 1 |
| 0x42 0x18 | graph_union | 2 |
| 0x42 0x19 | subgraph | 2 |
| 0x42 0x1A | isomorphic | 2 |
| 0x42 0x1B | max_clique | 1 |

### 2-Byte: Tensor Operations

| Code | Name | Arity |
|------|------|-------|
| 0x43 0x0A | tensor_product | 2 |
| 0x43 0x0B | tensor_contract | 3 |
| 0x43 0x0C | symmetrize | 1 |
| 0x43 0x0D | antisymmetrize | 1 |

### 2-Byte: Signal Processing (extended)

| Code | Name | Arity |
|------|------|-------|
| 0x44 0x0A | filter_apply | 2 |
| 0x44 0x0B | downsample | 2 |
| 0x44 0x0C | upsample | 2 |
| 0x44 0x0D | window | 2 |

### 2-Byte: Probability Distributions (as named constructors)

| Code | Name | Arity | Description |
|------|------|-------|-------------|
| 0x45 0x0A | dist_normal | 2 | Normal(mean, std) |
| 0x45 0x0B | dist_uniform | 2 | Uniform(lo, hi) |
| 0x45 0x0C | dist_binomial | 2 | Binomial(n, p) |
| 0x45 0x0D | dist_poisson | 1 | Poisson(lambda) |
| 0x45 0x0E | dist_expon | 1 | Exponential(rate) |
| 0x45 0x0F | dist_gamma_d | 2 | Gamma(shape, rate) |
| 0x45 0x10 | dist_beta_d | 2 | Beta(alpha, beta) |
| 0x45 0x11 | dist_chi2 | 1 | Chi-squared(df) |
| 0x45 0x12 | dist_student | 1 | Student-t(df) |
| 0x45 0x13 | dist_cauchy | 2 | Cauchy(loc, scale) |
| 0x45 0x14 | dist_bernoulli | 1 | Bernoulli(p) |
| 0x45 0x15 | dist_geometric | 1 | Geometric(p) |

### 2-Byte: Remaining Greek Letters

| Code | Name | Usage |
|------|------|-------|
| 0x46 0x0A | zeta_var | variable (not Riemann function) |
| 0x46 0x0B | eta | learning rate, viscosity |
| 0x46 0x0C | iota | index, basis |
| 0x46 0x0D | kappa | curvature, condition number |
| 0x46 0x0E | nu | frequency, degrees of freedom |
| 0x46 0x0F | xi | random variable |
| 0x46 0x10 | rho | density, correlation |
| 0x46 0x11 | tau | time constant, torque |
| 0x46 0x12 | upsilon | rarely used |
| 0x46 0x13 | phi_var | angle, potential (not golden ratio) |
| 0x46 0x14 | chi | chi-squared variable |
| 0x46 0x15 | psi | wave function, digamma |
| 0x46 0x16 | DELTA | uppercase delta (change) |
| 0x46 0x17 | SIGMA | uppercase sigma (summation) |
| 0x46 0x18 | PI_var | uppercase pi (product) |
| 0x46 0x19 | OMEGA | uppercase omega |

---

## Encoding Examples

### Simple arithmetic
`2 + 3 = ?`
```
add 2 3 Q/A 5 END
[0x3F] [0x0C] [0x0D] [0x05] [0x0F] [0x00]
```

### Nested expression
`(4 + 5) * 3 = ?`
```
multiply add 4 5 3 Q/A 27 END
[0x41] [0x3F] [0x0E] [0x0F] [0x0D] [0x05] ... [0x00]
```

### Algebra with variable
`solve 2x + 3 = 11 for x`
```
solve equal add multiply 2 x 3 11 x Q/A equal x 4 END
```

### Calculus
`d/dx(x^3) = ?`
```
derivative power x 3 x Q/A multiply 3 power x 2 END
```

### Trigonometry
`sin(pi/2) = ?`
```
sin divide pi 2 Q/A 1 END
```

### Matrix determinant
`det([[1,2],[3,4]]) = ?`
```
det vec_start 1 2 dim_sep 3 4 vec_end Q/A negate 2 END
```

---

*Travis Edward Holley*
*April 6, 2026*
