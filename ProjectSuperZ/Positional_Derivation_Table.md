# Positional Derivation Table — Project Superz

## The Complete 4D Byte Language
## Travis Edward Holley — April 9, 2026

---

## The Principle

Everything derives from a handful of base bytes plus 24 positional bytes. Roots, grammar, numbers, punctuation, and every alphabet on earth — all from position.

**59 base bytes + 24 positional bytes = the entire system.**
**197 root slots remain for concept atoms.**
**Each root × 24 positions = 4,728+ derived concepts.**
**26 letters × 24 positions = 650 letter forms (every alphabet on earth).**
**1 zero byte × positions = all digits.**
**1 mark byte × positions = all punctuation and symbols.**

---

## The 24 Positional Bytes

| # | Byte | Name | Spatial/Temporal Meaning |
|---|------|------|-------------------------|
| 1 | P01 | POS_CENTER | occupies space, the point |
| 2 | P02 | POS_TOP | above, modifies |
| 3 | P03 | POS_BESIDE | alongside, manner |
| 4 | P04 | POS_FRONT | forward, acts, causes |
| 5 | P05 | POS_BEHIND | behind, receives, effect |
| 6 | P06 | POS_BOTTOM | below, lesser |
| 7 | P07 | POS_INSIDE | contained within, essence |
| 8 | P08 | POS_OUTSIDE | surrounds, contains |
| 9 | P09 | POS_LEFT | left, feminine, Greek mode |
| 10 | P10 | POS_RIGHT | right, masculine, Cyrillic mode |
| 11 | P11 | POS_NEAR | close, small, diminutive |
| 12 | P12 | POS_FAR | distant, large, augmentative |
| 13 | P13 | POS_OVERLAP | shared space, group, collective |
| 14 | P14 | POS_BETWEEN | in the middle, fraction, hybrid |
| 15 | P15 | POS_AROUND | surrounds all, domain, system |
| 16 | P16 | T_BEFORE | past, former, ancient, origin |
| 17 | P17 | T_AFTER | future, result, offspring |
| 18 | P18 | T_DURING | present, ongoing, simultaneous |
| 19 | P19 | T_GROW | increasing, becoming, starting |
| 20 | P20 | T_DECAY | diminishing, aging, ending |
| 21 | P21 | T_RATE | speed, frequency, rate of change |
| 22 | P22 | T_DEADLINE | time boundary, imperative, must do |
| 23 | P23 | POS_MIRROR | opposite, reversal |
| 24 | P24 | POS_VOID | absence, negation, nothing |

---

## NUMBERS — One Zero Byte + Positions

The zero byte IS the number system. Position after it defines the digit.

| Combo | Digit |
|-------|-------|
| 0 alone | 0 |
| 0 POS_TOP | 1 |
| 0 POS_BOTTOM | 2 |
| 0 POS_LEFT | 3 |
| 0 POS_RIGHT | 4 |
| 0 POS_FRONT | 5 |
| 0 POS_BEHIND | 6 |
| 0 POS_INSIDE | 7 |
| 0 POS_OUTSIDE | 8 |
| 0 POS_CENTER | 9 |

**Multi-digit numbers:** string the pairs.

| Number | Encoding |
|--------|----------|
| 10 | 0 POS_TOP 0 |
| 42 | 0 POS_RIGHT 0 POS_BOTTOM |
| 347 | 0 POS_LEFT 0 POS_RIGHT 0 POS_INSIDE |
| 1000 | 0 POS_TOP 0 0 0 |
| 3.14 | 0 POS_LEFT MARK 0 POS_TOP 0 POS_RIGHT |

10 digits from 1 byte. No dedicated digit bytes consumed.

---

## PUNCTUATION & SYMBOLS — One Mark Byte + Positions

The mark byte (period) IS the punctuation system. Position after it defines the symbol.

| Combo | Symbol | Reason |
|-------|--------|--------|
| MARK alone | . | period — base, most frequent |
| MARK POS_TOP | , | comma — slight pause |
| MARK POS_BOTTOM | ; | semicolon — heavier pause |
| MARK POS_FRONT | ! | exclamation — forceful |
| MARK POS_BEHIND | ? | question — pulls back |
| MARK POS_LEFT | ( | open paren |
| MARK POS_RIGHT | ) | close paren |
| MARK POS_INSIDE | " | open quote |
| MARK POS_OUTSIDE | " | close quote |
| MARK POS_BETWEEN | : | colon — between parts |
| MARK POS_BESIDE | - | dash/hyphen |
| MARK POS_OVERLAP | ... | ellipsis |
| MARK POS_AROUND | / | slash |
| MARK POS_NEAR | ' | apostrophe |
| MARK POS_FAR | — | em dash |
| MARK POS_CENTER | @ | at sign |
| MARK POS_MIRROR | # | hash |
| MARK POS_VOID | * | asterisk |
| MARK T_BEFORE | [ | open bracket |
| MARK T_AFTER | ] | close bracket |
| MARK T_DURING | & | ampersand |
| MARK T_GROW | + | plus |
| MARK T_DECAY | − | minus |
| MARK T_RATE | % | percent |
| MARK T_DEADLINE | _ | underscore |

25 symbols from 1 byte. No dedicated punctuation bytes consumed.

---

## ALPHABETS — 26 Base Letters + Positions = Every Writing System

### Base: a b c d e f g h i j k l m n o p q r s t u v w x y z (26 bytes)

26 letters × 24 positions = 624 derived forms + 26 base = **650 total letter forms**.

### Diacritics — Position = Accent Type

| Position | Diacritic | Examples |
|----------|-----------|---------|
| POS_TOP | circumflex/hat ˆ | â ê î ô û ĉ ĝ ĥ ĵ ŝ |
| POS_BOTTOM | cedilla/hook ¸ | ç ş ţ ņ |
| POS_FRONT | acute accent ´ | á é í ó ú ń ś |
| POS_BEHIND | grave accent ` | à è ì ò ù |
| POS_INSIDE | umlaut/diaeresis ¨ | ä ë ï ö ü |
| POS_BESIDE | tilde ~ | ã ñ õ |
| POS_NEAR | ring/dot above ˙ | å ė ż ŭ |
| POS_FAR | macron/bar ¯ | ā ē ī ō ū |
| POS_OVERLAP | stroke/slash | ø ł đ |
| POS_MIRROR | reversed/flipped | ə (schwa) |

### Greek — POS_LEFT = Greek Mode

| Combo | Greek | Letter |
|-------|-------|--------|
| a POS_LEFT | α | alpha |
| b POS_LEFT | β | beta |
| g POS_LEFT | γ | gamma |
| d POS_LEFT | δ | delta |
| e POS_LEFT | ε | epsilon |
| z POS_LEFT | ζ | zeta |
| h POS_LEFT | η | eta |
| t POS_LEFT POS_TOP | θ | theta |
| i POS_LEFT | ι | iota |
| k POS_LEFT | κ | kappa |
| l POS_LEFT | λ | lambda |
| m POS_LEFT | μ | mu |
| n POS_LEFT | ν | nu |
| x POS_LEFT | ξ | xi |
| o POS_LEFT | ο | omicron |
| p POS_LEFT | π | pi |
| r POS_LEFT | ρ | rho |
| s POS_LEFT | σ | sigma |
| t POS_LEFT | τ | tau |
| u POS_LEFT | υ | upsilon |
| f POS_LEFT | φ | phi |
| c POS_LEFT | χ | chi |
| p POS_LEFT POS_TOP | ψ | psi |
| o POS_LEFT POS_FAR | ω | omega |

### Cyrillic — POS_RIGHT = Cyrillic Mode

| Combo | Cyrillic | Letter |
|-------|----------|--------|
| a POS_RIGHT | а | a |
| b POS_RIGHT | б | be |
| v POS_RIGHT | в | ve |
| g POS_RIGHT | г | ge |
| d POS_RIGHT | д | de |
| e POS_RIGHT | е | ye |
| z POS_RIGHT POS_TOP | ж | zhe |
| z POS_RIGHT | з | ze |
| i POS_RIGHT | и | i |
| k POS_RIGHT | к | ka |
| l POS_RIGHT | л | el |
| m POS_RIGHT | м | em |
| n POS_RIGHT | н | en |
| o POS_RIGHT | о | o |
| p POS_RIGHT | п | pe |
| r POS_RIGHT | р | er |
| s POS_RIGHT | с | es |
| t POS_RIGHT | т | te |
| u POS_RIGHT | у | u |
| f POS_RIGHT | ф | ef |
| h POS_RIGHT | х | kha |
| c POS_RIGHT | ц | tse |
| c POS_RIGHT POS_TOP | ч | che |
| s POS_RIGHT POS_TOP | ш | sha |
| y POS_RIGHT | ы | yeru |

### Arabic — T_BEFORE = Arabic Mode (28 letters)
### Hebrew — T_AFTER = Hebrew Mode (22 letters)
### Devanagari — T_DURING = Devanagari Mode (46 base characters)
### CJK Radicals — T_GROW = CJK Mode (214 Kangxi radicals from letter combos)

Each alphabet uses one positional byte as its mode selector. The base 26 Latin letters combine with that mode byte to produce the target alphabet's full character set. Complex alphabets use 2-position combos for characters that don't map to a single Latin equivalent.

---

## GRAMMAR — All Zamenhof Affixes and Endings as Positions

### Grammatical Endings → Positional Bytes

| Ending | Zamenhof | Positional | Why |
|--------|----------|-----------|-----|
| -o | noun | root + POS_CENTER | thing in space |
| -a | adjective | root + POS_TOP | quality above |
| -e | adverb | root + POS_BESIDE | manner alongside |
| -i | infinitive | root + POS_FRONT | action forward |
| -as | present | root + T_DURING | happening now |
| -is | past | root + T_BEFORE | happened before |
| -os | future | root + T_AFTER | will happen |
| -us | conditional | root + POS_INSIDE | contained possibility |
| -u | imperative | root + T_DEADLINE | must do now |
| -j | plural | root + POS_OVERLAP | multiple sharing space |
| -n | accusative | root + POS_BOTTOM | receives action |

### Suffixes → Positional Bytes

| Suffix | Zamenhof | Positional | Why |
|--------|----------|-----------|-----|
| -ad- | ongoing | T_DURING | continuous |
| -eg- | big | POS_FAR | far = large |
| -et- | small | POS_NEAR | near = small |
| -ej- | place | POS_OUTSIDE | place that surrounds |
| -uj- | container | POS_OUTSIDE + POS_CENTER | container as thing |
| -id- | offspring | POS_BOTTOM | below parent |
| -estr- | leader | POS_TOP + POS_TOP | highest above |
| -ig- | cause | POS_FRONT | push forward |
| -iĝ- | become | T_GROW | changing into |
| -ec- | quality | POS_INSIDE | essence within |
| -in- | feminine | POS_LEFT | left |
| -ar- | group | POS_OVERLAP | shared space |
| -op- | collective | POS_OVERLAP + POS_CENTER | group as thing |
| -obl- | multiple | POS_OVERLAP + POS_FAR | many, spread |
| -on- | fraction | POS_BETWEEN | division |
| -end- | must do | T_DEADLINE | time-bound |
| -an- | member | POS_INSIDE + POS_OVERLAP | inside a group |
| -aĵ- | concrete thing | POS_CENTER + POS_BEHIND | result in space |
| -ebl- | possible | POS_INSIDE + T_AFTER | could happen |
| -em- | tendency | T_RATE + POS_FRONT | rate toward |
| -er- | piece | POS_BETWEEN + POS_NEAR | small division |
| -il- | tool | POS_FRONT + POS_BESIDE | acts alongside |
| -ind- | worthy | POS_TOP + POS_INSIDE | quality within above |
| -ing- | holder | POS_OUTSIDE + POS_NEAR | small container |
| -ist- | professional | POS_CENTER + POS_FRONT | person who acts |
| -nj- | nickname fem | POS_LEFT + POS_NEAR | feminine + small |
| -ĉj- | nickname masc | POS_RIGHT + POS_NEAR | masculine + small |
| -ul- | person of | POS_CENTER + POS_TOP | person defined by quality |
| -um- | indefinite | POS_AROUND + POS_INSIDE | vague internal |
| -ism- | system | POS_AROUND | encompasses all |
| -ot- | future passive | T_AFTER + POS_BOTTOM | will be acted upon |

### Prefixes → Positional Bytes

| Prefix | Zamenhof | Positional | Why |
|--------|----------|-----------|-----|
| sub- | under | POS_BOTTOM | below |
| super- | over | POS_TOP | above |
| for- | away | POS_FAR | distance |
| re- | again | T_BEFORE + T_AFTER | back then forward |
| ek- | start | T_GROW | beginning |
| eks- | former | T_BEFORE | was before |
| pra- | ancient | T_BEFORE + POS_FAR | far in past |
| bo- | in-law | POS_BESIDE + POS_OVERLAP | alongside through overlap |
| dis- | apart | POS_FAR + POS_AROUND | spreading far |
| ge- | both sexes | POS_LEFT + POS_RIGHT | feminine + masculine |
| mal- | opposite | POS_MIRROR | reversal |
| mis- | wrong | POS_MIRROR + POS_FRONT | reversed action |
| ne- | not | POS_VOID | negation |
| sen- | without | POS_VOID + POS_OUTSIDE | absence around |

---

## ROOT DERIVATION — Every Root in 4D Space

Every root + every positional byte = a derived concept. Example with `hund` (dog):

| Position | Meaning |
|----------|---------|
| [hund] alone | dog — the raw concept |
| [hund] POS_CENTER | the dog (noun) |
| [hund] POS_TOP | dog-like (adjective) |
| [hund] POS_BESIDE | in a dog way (adverb) |
| [hund] POS_FRONT | to dog / act as dog (verb) |
| [hund] POS_BEHIND | dogged / result of dog action |
| [hund] POS_BOTTOM | puppy (lesser/offspring) |
| [hund] POS_INSIDE | dog-ness (quality/essence) |
| [hund] POS_OUTSIDE | kennel / dog place (container) |
| [hund] POS_LEFT | female dog |
| [hund] POS_RIGHT | male dog |
| [hund] POS_NEAR | small dog |
| [hund] POS_FAR | big dog / great dog |
| [hund] POS_OVERLAP | pack of dogs (group) |
| [hund] POS_BETWEEN | mixed breed |
| [hund] POS_AROUND | everything dog-related (domain) |
| [hund] POS_MIRROR | opposite of dog (cat? anti-dog?) |
| [hund] POS_VOID | absence of dog / no dog |
| [hund] T_BEFORE | ancestor dog / wolf |
| [hund] T_AFTER | future dog / what dog becomes |
| [hund] T_DURING | dog in action |
| [hund] T_GROW | dog growing / puppy becoming dog |
| [hund] T_DECAY | aging dog |
| [hund] T_RATE | dog speed |
| [hund] T_DEADLINE | dog's lifespan |

**25 derived concepts per root.** (24 positions + bare root)

---

## COMPLETE BYTE BUDGET

| Category | Bytes | Derivations |
|----------|-------|-------------|
| Control (END, SPACE, COIN, SKIP, NAME, Q/A) | 6 | 6 functions |
| Zero (number byte) | 1 | × 10 positions = 10 digits |
| Mark (punctuation byte) | 1 | × 25 positions = 25 symbols |
| la (article) | 1 | 1 function word |
| Letters (a-z) | 26 | × 24 positions = 650 letter forms |
| Positional/temporal bytes | 24 | grammar + derivation + digits + symbols + alphabets |
| **Root slots** | **197** | **× 25 = 4,925 derived concepts** |
| **TOTAL** | **256** | **5,616+ unique forms** |

---

## Full Sentence Example

"The big dog quickly chased the small cat yesterday"

```
la [hund] POS_FAR POS_CENTER [ĉas] T_BEFORE POS_FRONT la [kat] POS_NEAR POS_CENTER [rapid] POS_BESIDE T_BEFORE
```

Every word is a root + positions. No suffixes. No prefixes. No endings. Just concepts in 4D spacetime.

---

*Travis Edward Holley*
*April 9, 2026*
