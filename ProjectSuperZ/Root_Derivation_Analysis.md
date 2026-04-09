# Root Derivation Analysis — Project Superz

## How Many Roots Do We Actually Need?
## Travis Edward Holley — April 9, 2026

---

## Zamenhof's Original Inventory

From the 1887-1894 publications:

| Category | Count |
|----------|-------|
| Content roots | 801 |
| Grammar/affixes | 25 |
| Function words | 96 |
| **Total** | **922** |

Grammar and affixes are handled by positional bytes (see Positional_Derivation_Table.md).
Function words: some collapse into positions (en = POS_INSIDE, sur = POS_TOP, antau = T_BEFORE), others keep dedicated bytes or get COIN-spelled.

The question is the 801 content roots. We have 197 root slots.

---

## One Root = 25 Concepts

### Example: dom (house)

| Encoding | Meaning |
|----------|---------|
| dom | house — raw concept |
| dom POS_CENTER | a house (noun) |
| dom POS_TOP | house-like, domestic (adjective) |
| dom POS_BESIDE | at home, domestically (adverb) |
| dom POS_FRONT | to house, to shelter (verb) |
| dom POS_BEHIND | housed, sheltered (result) |
| dom POS_BOTTOM | hut, shack (lesser house) |
| dom POS_INSIDE | homeliness, domesticity (quality) |
| dom POS_OUTSIDE | estate, property (contains houses) |
| dom POS_LEFT | housewife, lady of house (feminine) |
| dom POS_RIGHT | master of house (masculine) |
| dom POS_NEAR | cottage (small house) |
| dom POS_FAR | mansion, palace (big house) |
| dom POS_OVERLAP | neighborhood, housing block (group) |
| dom POS_BETWEEN | duplex, shared wall (between) |
| dom POS_AROUND | real estate, housing domain |
| dom POS_MIRROR | homelessness, outdoors (opposite) |
| dom POS_VOID | no house, unhoused (absence) |
| dom T_BEFORE | old house, ruins, former home |
| dom T_AFTER | planned house, future home |
| dom T_DURING | occupied house, home being lived in |
| dom T_GROW | house under construction |
| dom T_DECAY | house crumbling, deteriorating |
| dom T_RATE | housing rate, houses per area |
| dom T_DEADLINE | lease term, mortgage deadline |

**1 root byte = 25 concepts.**

---

## Zamenhof Roots Absorbed by dom + Positions

These are separate roots in Zamenhof's list that don't need their own byte:

| Zamenhof Root | Meaning | Derivation |
|--------------|---------|------------|
| palac | palace | dom POS_FAR |
| kabm | cabin/hut | dom POS_NEAR or dom POS_BOTTOM |
| cxambr | room | dom POS_INSIDE |
| logx | to dwell | dom POS_FRONT |
| hejm | home | dom T_DURING |
| konstru | to build | dom T_GROW |

One root absorbs 6 others. Those 6 roots don't need byte slots.

---

## Cross-Root Absorption Patterns

### Gender (POS_LEFT = feminine)

| Base Root | Meaning | POS_LEFT = | Absorbs |
|-----------|---------|------------|---------|
| patr | father | mother | patrino |
| fil | son | daughter | filino |
| frat | brother | sister | fratino |
| edz | husband | wife | edzino |
| knab | boy | girl | knabino |
| regx | king | queen | regxino |
| nev | nephew | niece | nevino |
| onkl | uncle | aunt | onklino |

8 roots absorb 8 feminine forms. No separate roots needed for any feminine family member.

### Size (POS_NEAR = small, POS_FAR = big)

| Base Root | POS_NEAR = | POS_FAR = |
|-----------|-----------|-----------|
| dom | cottage | palace |
| mont | hill | mountain peak |
| urb | village | city |
| river | stream | great river |
| arb | bush | great tree |
| bird | sparrow | eagle |
| hund | small dog | great dog |

### Time (T_BEFORE = past, T_AFTER = future, T_GROW = beginning, T_DECAY = ending)

| Base Root | T_BEFORE = | T_AFTER = | T_GROW = | T_DECAY = |
|-----------|-----------|-----------|----------|-----------|
| tag | yesterday | tomorrow | dawn | dusk |
| jar | last year | next year | spring | autumn |
| viv | birth | death | growing up | aging |
| dom | ruins | planned house | construction | crumbling |
| flor | bud | seed pod | blooming | wilting |

### Causation (POS_FRONT = cause, POS_BEHIND = effect)

| Base Root | POS_FRONT = | POS_BEHIND = |
|-----------|------------|-------------|
| brul | to ignite | ash, cinder |
| frap | to strike | wound, bruise |
| lern | to teach | knowledge |
| plant | to plant | harvest |
| kuir | to cook | meal |

### Containment (POS_INSIDE, POS_OUTSIDE)

| Base Root | POS_INSIDE = | POS_OUTSIDE = |
|-----------|-------------|--------------|
| dom | room | estate |
| urb | district | country |
| land | province | continent |
| korp | organ | skin |
| arb | sap | forest |

---

## The Math

| | Count |
|-|-------|
| Zamenhof content roots | 801 |
| Estimated absorbable by positional derivation | ~200-300 |
| Remaining independent roots | ~550 |
| Root slots available | 197 |
| Roots needing COIN-spelling | ~353 |

**But:**
- The 197 highest-frequency roots cover ~85-90% of all text
- The 353 COIN-spelled roots appear rarely
- COIN-spelling a 3-4 letter root costs 4-5 bytes (short)

### Root Length Distribution (from Zamenhof's 922 entries)

| Length | Roots | Cumulative |
|--------|-------|-----------|
| 1 char | 8 | 8 |
| 2 chars | 64 | 72 |
| 3 chars | 237 | 309 |
| 4 chars | 282 | 591 |
| 5 chars | 174 | 765 |
| 6 chars | 102 | 867 |
| 7 chars | 47 | 914 |
| 8 chars | 7 | 921 |
| 9 chars | 1 | 922 |

Most roots are 3-4 characters. COIN-spelling cost is minimal.

---

## Total Vocabulary from 197 Root Bytes

| Source | Concepts |
|--------|----------|
| 197 roots × 25 positions | 4,925 |
| Absorbed Zamenhof roots (gender, size, time, cause, containment) | ~250 additional meanings covered |
| COIN-spelled roots × 25 positions | unlimited — same derivation system |
| Multi-position combinations (POS_TOP + POS_TOP = leader, etc.) | hundreds more |
| **Conservative total** | **5,000+ distinct concepts from 197 bytes** |

---

## What This Means

Zamenhof designed 917 roots to cover all of human language through composition. With positional derivation, many of those 917 are redundant — they're positional derivatives of simpler roots that Zamenhof had to spell out because he was designing for human speakers, not for a 4D byte system.

197 root bytes in a positional encoding system may cover MORE vocabulary than Zamenhof's full 917 did, because positions create derivations Zamenhof had to assign separate roots for.

The remaining roots that truly need their own identity (no simpler root to derive from) get COIN-spelled. They're rare and short. The system handles them without dedicated bytes.

---

*Travis Edward Holley*
*April 9, 2026*
