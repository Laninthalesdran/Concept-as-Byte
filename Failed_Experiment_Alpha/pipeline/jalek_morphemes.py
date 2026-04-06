"""
JalekCore Morpheme Loader — Reads ROOTS directly from the base table.

DEFAULT TO TABLE LOOKUP.

This module loads morpheme→byte mappings from JalekCore_Base_Table.txt
so generators never hardcode hex values. The table is the single source of truth.

Author: Travis Edward Holley
Module: Claude (Anthropic)
"""

import os

# Control bytes (fixed by architecture, not from table)
END = 0x00
BOUNDARY = 0x01
SPACE = 0x02
NEWLINE = 0x03
PARAGRAPH = 0x04
QA = 0x05
SKIP = 0x06
JALEKON = 0x07
NAME = 0x08
COIN = 0x09

# Punctuation (shared layer — same byte codes in both tables)
COMMA = 0x35      # ,
QUESTION = 0x36   # ?
EXCLAIM = 0x37    # !
PERIOD = 0x14     # .

# Punctuation bytes for insertion in chains.
# sentence() already adds SPACE between words, so these only need
# the punctuation byte itself. sentence() handles the surrounding spaces.
# Use these AS words in sentence() / chain() calls.
P_COMMA = bytes([COMMA])        # , (sentence() adds SPACE around it)
P_PERIOD = bytes([PERIOD])      # .
P_QUESTION = bytes([QUESTION])  # ?
P_EXCLAIM = bytes([EXCLAIM])    # !

# Grammatical endings (fixed by architecture)
NOUN = 0x38       # -o
ADJ = 0x39        # -a
ADV = 0x3a        # -e
INF = 0x3b        # -i
PRESENT = 0x3c    # -as
PAST = 0x3d       # -is
FUTURE = 0x3e     # -os
COND = 0x3f       # -us
IMPER = 0x40      # -u
PLURAL = 0x41     # -j
ACC = 0x42        # -n
THE = 0x43        # la

# Suffixes (fixed by architecture)
ONGOING = 0x44    # -ad-
MEMBER = 0x45     # -an-
GROUP = 0x46      # -ar-
THING = 0x47      # -aĵ-
POSSIBLE = 0x48   # -ebl-
QUALITY = 0x49    # -ec-
BIG = 0x4a        # -eg-
PLACE = 0x4b      # -ej-
TENDENCY = 0x4c   # -em-
MUST_DO = 0x4d    # -end-
PIECE = 0x4e      # -er-
LEADER = 0x4f     # -estr-
SMALL = 0x50      # -et-
OFFSPRING = 0x51  # -id-
CAUSE = 0x52      # -ig-
TOOL = 0x53       # -il-
FEMALE = 0x54     # -in-
WORTHY = 0x55     # -ind-
HOLDER = 0x56     # -ing-
SYSTEM = 0x57     # -ism-
PROFESSIONAL = 0x58  # -ist-
BECOME = 0x59     # -iĝ-
NICK_F = 0x5a     # -nj-
MULTIPLE = 0x5b   # -obl-
FRACTION = 0x5c   # -on-
COLLECTIVE = 0x5d # -op-
FUTURE_PASS = 0x5e # -ot-
CONTAINER = 0x5f  # -uj-
PERSON = 0x60     # -ul-
INDEF = 0x61      # -um-
NICK_M = 0x62     # -ĉj-

# Prefixes (fixed by architecture)
IN_LAW = 0x63     # bo-
APART = 0x64      # dis-
START = 0x65      # ek-
FORMER = 0x66     # eks-
AWAY = 0x67       # for-
BOTH_SEXES = 0x68 # ge-
MAL = 0x69        # mal- (opposite)
WRONG = 0x6a      # mis-
NE_PREFIX = 0x6b  # ne- (not)
ANCIENT = 0x6c    # pra-
RE = 0x6d         # re- (again)
WITHOUT = 0x6e    # sen-
UNDER = 0x6f      # sub-
OVER = 0x70       # super-


def load_table(table_path=None):
    """Load morpheme→bytes mapping from the base table file.

    Returns dict: morpheme_name → bytes
    Skips the header row.
    For duplicates, keeps the first occurrence.
    """
    if table_path is None:
        # Look for table on Desktop first, then in git repo
        candidates = [
            os.path.join(os.path.dirname(__file__), '..', 'JalekCore_Base_Table.txt'),
            'C:/Users/Travi/OneDrive/Desktop/JalekCore_Base_Table.txt',
            os.path.join(os.path.dirname(__file__), '..', 'JalekCore_git', 'JalekCore_Base_Table.txt'),
        ]
        for c in candidates:
            if os.path.exists(c):
                table_path = c
                break
        if table_path is None:
            raise FileNotFoundError("Cannot find JalekCore_Base_Table.txt")

    roots = {}
    seen_hex = set()

    with open(table_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            parts = line.strip().split('\t')
            if len(parts) < 5:
                continue

            morpheme = parts[2].strip()
            hex_code = parts[3].strip().replace('0x', '')
            english = parts[4].strip()
            entry_type = parts[5].strip() if len(parts) > 5 else ''

            # Skip header
            if morpheme == 'Morpheme':
                continue

            # Skip control bytes, endings, suffixes, prefixes — those are hardcoded above
            if entry_type in ['Control Byte', 'Ending', 'Suffix', 'Prefix', 'Letter']:
                continue

            # Validate hex
            try:
                bts = bytes.fromhex(hex_code)
            except ValueError:
                continue

            # Skip duplicates (keep first)
            if hex_code in seen_hex:
                continue
            seen_hex.add(hex_code)

            # Normalize morpheme name for lookup
            # Remove diacritics for key: ĉ→ch, ĝ→gh, ĥ→hh, ĵ→jh, ŝ→sh, ŭ→u
            key = morpheme.lower().replace('-', '')
            key = key.replace('ĉ', 'ch').replace('ĝ', 'gh').replace('ĥ', 'hh')
            key = key.replace('ĵ', 'jh').replace('ŝ', 'sh').replace('ŭ', 'u')

            roots[key] = bts

            # Also store with original (diacritic) key
            orig_key = morpheme.lower().replace('-', '')
            if orig_key != key:
                roots[orig_key] = bts

    return roots


# Load on import
ROOTS = load_table()


# ============================================================
# WORD BUILDER FUNCTIONS
# ============================================================

def word(*parts):
    """Build a word from morpheme parts.
    Each part can be: str (lookup in ROOTS), int (raw byte), bytes (raw bytes).
    Parts are joined with BOUNDARY between them.
    """
    result = bytearray()
    for i, p in enumerate(parts):
        if isinstance(p, int):
            result.append(p)
        elif isinstance(p, bytes):
            result.extend(p)
        elif isinstance(p, str):
            if p in ROOTS:
                result.extend(ROOTS[p])
            else:
                raise ValueError(f"Unknown morpheme: '{p}' — not in base table")
        if i < len(parts) - 1:
            result.append(BOUNDARY)
    return bytes(result)


def sentence(*words_list):
    """Build a sentence from words. SPACE between words."""
    result = bytearray()
    for i, w in enumerate(words_list):
        if isinstance(w, (bytes, bytearray)):
            result.extend(w)
        elif isinstance(w, int):
            result.append(w)
        if i < len(words_list) - 1:
            result.append(SPACE)
    return bytes(result)


def chain(*words_list, punct=PERIOD):
    """Build a complete chain ending with punctuation + END.

    punct=PERIOD (default): ... SPACE . END
    punct=QUESTION: ... SPACE ? END
    punct=EXCLAIM: ... SPACE ! END
    punct=None: ... END (no punctuation, legacy behavior)
    """
    s = sentence(*words_list)
    if punct is not None:
        return s + bytes([SPACE, punct, END])
    return s + bytes([END])


def qa_chain(question_words, answer_words):
    """Build a Q/A chain: question SPACE ? [Q/A] answer SPACE . [END]."""
    q = sentence(*question_words)
    a = sentence(*answer_words)
    return q + bytes([SPACE, QUESTION, QA]) + a + bytes([SPACE, PERIOD, END])


def verb(root, tense=PRESENT):
    """Build verb: root + tense ending."""
    return word(root, tense)


def noun(root, plural=False, acc=False):
    """Build noun: root + -o + optional -j + optional -n."""
    parts = [root, NOUN]
    if plural: parts.append(PLURAL)
    if acc: parts.append(ACC)
    return word(*parts)


def adj(root, plural=False, acc=False):
    """Build adjective: root + -a + optional -j + optional -n."""
    parts = [root, ADJ]
    if plural: parts.append(PLURAL)
    if acc: parts.append(ACC)
    return word(*parts)


def adv(root):
    """Build adverb: root + -e."""
    return word(root, ADV)


def coin_word(root):
    """Build a COIN-tagged word: [COIN][B]root[B]-o."""
    return bytes([COIN, BOUNDARY]) + word(root, NOUN)


def number_word(n):
    """Convert integer to Esperanto number bytes."""
    nums = {
        0: ROOTS.get('nul', b'\x00'), 1: ROOTS['unu'], 2: ROOTS['du'],
        3: ROOTS['tri'], 4: ROOTS['kvar'], 5: ROOTS['kvin'],
        6: ROOTS['ses'], 7: ROOTS['sep'], 8: ROOTS['ok'],
        9: ROOTS['nau'], 10: ROOTS['dek'], 100: ROOTS['cent'],
    }
    if n in nums:
        return nums[n]
    if 10 < n < 20:
        return word(nums[10], nums[n - 10])
    if n < 100:
        tens = n // 10
        ones = n % 10
        if ones == 0:
            return word(nums[tens], 'dek')
        return word(nums[tens], 'dek', nums[ones])
    if n == 100:
        return nums[100]
    if n < 1000:
        hundreds = n // 100
        remainder = n % 100
        h_part = nums[100] if hundreds == 1 else word(nums[hundreds], 'cent')
        if remainder == 0:
            return h_part
        return word(h_part, number_word(remainder))
    return nums.get(n, nums[1])


# Convenience: common prebuilt words
def get_common():
    """Return dict of commonly used word bytes for quick access."""
    r = ROOTS
    return {
        'MI': r['mi'], 'VI': r['vi'], 'LI': r['li'],
        'SHI': r.get('shi', r.get('ŝi', b'')),
        'GHI': r.get('ghi', r.get('ĝi', b'')),
        'NI': r['ni'], 'ILI': r['ili'],
        'LA': bytes([THE]),
        'KAJ': r['kaj'], 'SED': r['sed'], 'SE': r['se'],
        'DO': r['do'], 'CHAR': r.get('char', r.get('ĉar', b'')),
        'TIAM': r['tiam'], 'POST': r['post'],
        'ANTAU': r.get('antau', r.get('antaŭ', b'')),
        'DUM': r['dum'], 'NE': bytes([NE_PREFIX]),
        'AL': r['al'], 'DE': r['de'], 'EN': r['en'],
        'SUR': r['sur'], 'KUN': r['kun'], 'POR': r['por'],
        'DA': r['da'], 'OL': r['ol'], 'KE': r['ke'],
        'CHU': r.get('chu', r.get('ĉu', b'')),
        'JES': r['jes'], 'NUR': r['nur'],
        'AU': r.get('au', r.get('aŭ', b'')),
        'AMBAU': r.get('ambau', r.get('ambaŭ', b'')),
    }


def load_replay_chains(bin_path, count):
    """Load chains from a phase binary file for replay.
    Strips leading SPACE bytes (inter-chain separators from binary format).
    """
    import random as _random
    if not os.path.exists(bin_path):
        return []
    with open(bin_path, 'rb') as f:
        data = f.read()
    chains = []
    current = bytearray()
    for b in data:
        current.append(b)
        if b == END:
            # Strip leading SPACE bytes
            c = bytes(current)
            while c and c[0] == SPACE:
                c = c[1:]
            if c:
                chains.append(c)
            current = bytearray()
    if not chains:
        return []
    return _random.sample(chains, min(count, len(chains)))


if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')

    print(f"Loaded {len(ROOTS)} morphemes from base table")
    print()

    # Verify some key morphemes
    test = ['mi', 'vi', 'li', 'hav', 'est', 'ir', 'ven', 'mangh',
            'pom', 'akv', 'pan', 'mon', 'tag', 'hor', 'dom',
            'hund', 'kat', 'bird', 'arb', 'river', 'fajr',
            'grand', 'bon', 'nov', 'fort',
            'kaj', 'sed', 'se', 'do', 'tiam', 'post',
            'unu', 'du', 'tri', 'kvar', 'kvin', 'dek', 'cent',
            'ne', 'la', 'al', 'de', 'en', 'sur', 'kun', 'por']

    missing = []
    for t in test:
        if t in ROOTS:
            print(f"  {t:12s} -> 0x{ROOTS[t].hex()}")
        else:
            missing.append(t)

    if missing:
        print(f"\nMissing: {missing}")
    else:
        print(f"\nAll {len(test)} test morphemes found.")

    # Test word building
    print()
    print("=== WORD BUILDING TEST ===")
    try:
        w = word('hav', PRESENT)
        print(f"  havas = 0x{w.hex()}")
        w = noun('pom', plural=True, acc=True)
        print(f"  pomojn = 0x{w.hex()}")
        w = word(MAL, ROOTS['bon'], ADJ)
        print(f"  malbona = 0x{w.hex()}")
        s = sentence(ROOTS['mi'], verb('hav', PRESENT), noun('pom', acc=True))
        print(f"  mi havas pomon = {' '.join(f'{b:02x}' for b in s)}")
        c = chain(ROOTS['mi'], verb('hav', PRESENT), noun('pom', acc=True))
        print(f"  mi havas pomon [END] = {' '.join(f'{b:02x}' for b in c)}")
        print("\nAll tests passed.")
    except Exception as e:
        print(f"\nERROR: {e}")
