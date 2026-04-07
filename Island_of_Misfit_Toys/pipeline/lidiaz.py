"""
LidiaZ — The Bridge Between AdamZ and LLZ

Pure table lookup. Esperanto byte sequence in, English byte code
candidates out. One dict. No reasoning.

At init: builds a flat lookup table mapping every known Esperanto
byte sequence to a list of LLZ English byte codes.

At runtime: dict[esp_bytes] -> [llz_bytes, llz_bytes, ...]

Named after Lidia Zamenhof (1904-1942), translator and Esperanto
advocate who bridged languages and cultures. Murdered at Treblinka.

Author: Travis Edward Holley
Architecture: Claude (Anthropic)
"""

import os
import sys
import json

from llz_encoder import LLZEncoder, END, BOUNDARY, SPACE, NEWLINE, QA, COIN, NAME

CONTROL_BYTES = set(range(0x00, 0x0A))


class LidiaZ:
    """
    The Bridge. Bidirectional.

    esp_bytes -> [llz_bytes, ...]   (output: AdamZ -> English)
    llz_bytes -> [esp_bytes, ...]   (input: English -> AdamZ)

    Two dicts. One lookup each direction. That's it.
    """

    def __init__(self, base_table_path=None, dict_path=None):
        base = os.path.dirname(__file__)
        desktop = os.path.dirname(base)

        if base_table_path is None:
            base_table_path = os.path.join(desktop, 'JalekCore_Base_Table.txt')
        if dict_path is None:
            dict_path = os.path.join(desktop, 'Failed', 'english_to_esperanto.json')

        # Output direction: esperanto byte hex -> list of llz byte codes
        self.table = {}
        # Input direction: llz byte hex -> list of esperanto byte codes
        self.reverse = {}

        # Load LLZ encoder for English word -> byte code conversion
        self.llz = LLZEncoder()
        valid_english = set(self.llz.encode_table.keys())

        # Step 1: Load base table — get byte_hex -> (morpheme, english, type)
        byte_to_info = {}
        with open(base_table_path, 'r', encoding='utf-8') as f:
            f.readline()
            for line in f:
                parts = line.rstrip('\n').split('\t')
                if len(parts) < 6:
                    continue
                morpheme, hex_code, english, typ = parts[2], parts[3], parts[4].strip(), parts[5]
                try:
                    code_bytes = bytes.fromhex(hex_code[2:])
                except ValueError:
                    continue
                byte_to_info[code_bytes.hex()] = (morpheme.lower(), english.lower() if english else '', typ)

        # Step 2: Load reversed dictionary — esperanto composed form -> [english words]
        esp_to_eng = {}
        if os.path.exists(dict_path):
            print("Loading translation dictionary...", end='', flush=True)
            with open(dict_path, 'r', encoding='utf-8') as f:
                eng2esp = json.load(f)
            kept = 0
            for eng, esp in eng2esp.items():
                eng_lower = eng.lower().strip()
                esp_lower = esp.lower().strip()
                if eng_lower in valid_english:
                    if esp_lower not in esp_to_eng:
                        esp_to_eng[esp_lower] = []
                    esp_to_eng[esp_lower].append(eng_lower)
                    kept += 1
            print(f" {kept:,} entries")

        # Step 3: Build root -> [english words] from both sources
        root_to_english = {}  # morpheme name -> set of english words

        # From base table English column
        for hex_key, (morpheme, english, typ) in byte_to_info.items():
            if typ == 'Root' and english:
                if morpheme not in root_to_english:
                    root_to_english[morpheme] = set()
                root_to_english[morpheme].add(english)

        # From reversed dictionary — match root names to dictionary entries
        # Dictionary has composed forms (kuri, domo, granda) not bare roots (kur, dom, grand)
        # So we try root + common endings
        ending_suffixes = ['o', 'a', 'e', 'i', 'as', 'is', 'os', 'us', 'u']
        for morpheme in list(root_to_english.keys()):
            for suffix in ending_suffixes:
                composed = morpheme + suffix
                if composed in esp_to_eng:
                    for eng in esp_to_eng[composed]:
                        root_to_english[morpheme].add(eng)

        # Also add roots that are only in the dictionary (no base table English column)
        for hex_key, (morpheme, english, typ) in byte_to_info.items():
            if typ == 'Root' and morpheme not in root_to_english:
                for suffix in ending_suffixes:
                    composed = morpheme + suffix
                    if composed in esp_to_eng:
                        root_to_english[morpheme] = set(esp_to_eng[composed])
                        break

        # Step 4: Build the final table
        # For each root, map its byte code to English LLZ byte codes
        # Base table English column goes FIRST (clean), then dictionary entries
        print("Building LidiaZ lookup table...", end='', flush=True)

        for hex_key, (morpheme, english, typ) in byte_to_info.items():
            if typ == 'Root' and morpheme in root_to_english:
                esp_bytes_hex = hex_key
                primary = []   # base table english — clean, goes first
                secondary = [] # dictionary entries — may have garbage
                seen = set()

                # Base table English column first
                if english and english in self.llz.encode_table and english not in seen:
                    seen.add(english)
                    primary.append(self.llz.encode_table[english])

                # Then dictionary entries
                for eng_word in root_to_english[morpheme]:
                    if eng_word in self.llz.encode_table and eng_word not in seen:
                        seen.add(eng_word)
                        secondary.append(self.llz.encode_table[eng_word])

                llz_candidates = primary + secondary
                if llz_candidates:
                    self.table[esp_bytes_hex] = llz_candidates

        # Also map special entries: la (the), endings as themselves, punctuation, digits
        # These share codes between tables — they pass through
        for hex_key, (morpheme, english, typ) in byte_to_info.items():
            if typ in ('Control Byte', 'Digit', 'Letter', 'Punctuation', 'Accented Letter'):
                # Shared codes — same byte in both tables
                code_bytes = bytes.fromhex(hex_key)
                self.table[hex_key] = [code_bytes]
            elif typ == 'Ending':
                # Endings don't translate to English words directly
                # but 'la' (the article) does
                if morpheme == 'la' and 'the' in self.llz.encode_table:
                    self.table[hex_key] = [self.llz.encode_table['the']]

        print(f" {len(self.table):,} entries")

        # Step 5: Build reverse table (English bytes -> Esperanto bytes)
        # Flip the forward table: for each esp_hex -> [llz_bytes], create llz_hex -> [esp_bytes]
        print("Building reverse table (Eng→Esp)...", end='', flush=True)

        for esp_hex, llz_list in self.table.items():
            esp_bytes = bytes.fromhex(esp_hex)
            for llz_bytes in llz_list:
                llz_hex = llz_bytes.hex()
                if llz_hex not in self.reverse:
                    self.reverse[llz_hex] = []
                self.reverse[llz_hex].append(esp_bytes)

        print(f" {len(self.reverse):,} entries")

    def lookup(self, esp_byte_hex):
        """Esp→Eng. Returns list of LLZ byte codes or empty list."""
        return self.table.get(esp_byte_hex, [])

    def lookup_reverse(self, llz_byte_hex):
        """Eng→Esp. Returns list of Esperanto byte codes or empty list."""
        return self.reverse.get(llz_byte_hex, [])

    def bridge(self, adamz_bytes):
        """Process AdamZ byte stream word by word.

        Splits on SPACE/END/QA/NEWLINE. For each word, splits on
        BOUNDARY to get individual morphemes, looks up the root,
        and returns candidates.

        Returns list of:
          ('control', byte_value) — pass-through
          ('candidates', [llz_bytes, ...]) — English byte code options
        """
        if isinstance(adamz_bytes, (bytes, bytearray)):
            adamz_bytes = list(adamz_bytes)

        result = []
        current_word = bytearray()
        splitters = {END, SPACE, QA, NEWLINE, COIN, NAME}

        for b in adamz_bytes:
            if b in splitters:
                if current_word:
                    result.append(('candidates', self._translate_word(current_word)))
                    current_word = bytearray()
                result.append(('control', b))
            else:
                current_word.append(b)

        if current_word:
            result.append(('candidates', self._translate_word(current_word)))

        return result

    def bridge_reverse(self, llz_bytes):
        """Process LLZ English byte stream → Esperanto byte candidates.

        Input side: English bytes from LLZ encoder → Esperanto bytes for AdamZ.
        Same structure as bridge() but in reverse direction.
        """
        if isinstance(llz_bytes, (bytes, bytearray)):
            llz_bytes = list(llz_bytes)

        result = []
        current_word = bytearray()
        splitters = {END, SPACE, QA, NEWLINE, COIN, NAME}

        for b in llz_bytes:
            if b in splitters:
                if current_word:
                    result.append(('candidates', self._translate_word_reverse(current_word)))
                    current_word = bytearray()
                result.append(('control', b))
            else:
                current_word.append(b)

        if current_word:
            result.append(('candidates', self._translate_word_reverse(current_word)))

        return result

    def _translate_word(self, word_bytes):
        """Esp→Eng. Split on BOUNDARY, find root, look it up."""
        parts = []
        current = bytearray()
        for b in word_bytes:
            if b == BOUNDARY:
                if current:
                    parts.append(bytes(current))
                    current = bytearray()
            else:
                current.append(b)
        if current:
            parts.append(bytes(current))

        for part in parts:
            candidates = self.lookup(part.hex())
            if candidates:
                return candidates
        return []

    def _translate_word_reverse(self, word_bytes):
        """Eng→Esp. Look up the full LLZ byte sequence."""
        candidates = self.lookup_reverse(bytes(word_bytes).hex())
        if candidates:
            return candidates
        return []


# ============================================================
# TEST
# ============================================================

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')

    lz = LidiaZ()

    from jalek_morphemes import (ROOTS, word, noun, verb, adj, sentence,
                                  PRESENT as J_PRESENT, PAST as J_PAST)

    print("\n=== LOOKUP TEST ===")
    test_roots = ['hund', 'grand', 'kur', 'akv', 'bon', 'dom', 'nov', 'labor']

    for root_name in test_roots:
        root_bytes = ROOTS.get(root_name)
        if root_bytes:
            candidates = lz.lookup(root_bytes.hex())
            eng = [lz.llz.decode_table.get(c.hex(), '?') for c in candidates[:8]]
            print(f"  {root_name} ({root_bytes.hex()}): {eng}")

    print("\n=== BRIDGE TEST ===")
    test_chain = sentence(
        bytes([0x43]),       # la (the)
        noun('hund'),        # hundo (dog)
        verb('kur', J_PAST), # kuris (ran)
    ) + bytes([END])

    bridge_result = lz.bridge(test_chain)
    ctrl_names = {0x00: 'END', 0x02: 'SPACE', 0x05: 'QA', 0x03: 'NEWLINE'}
    print("  Input: la hundo kuris [END]")
    for entry_type, data in bridge_result:
        if entry_type == 'control':
            print(f"    [{ctrl_names.get(data, hex(data))}]")
        else:
            eng = []
            for c in data[:8]:
                w = lz.llz.decode_table.get(c.hex(), '?')
                eng.append(w)
            print(f"    -> {eng}")

    print("\n=== REVERSE LOOKUP TEST (Eng→Esp) ===")
    test_eng = ['dog', 'run', 'water', 'house', 'good', 'new', 'the']
    for eng_word in test_eng:
        if eng_word in lz.llz.encode_table:
            llz_bytes = lz.llz.encode_table[eng_word]
            esp_candidates = lz.lookup_reverse(llz_bytes.hex())
            esp_morphemes = []
            for eb in esp_candidates[:5]:
                # Look up what Esperanto morpheme this is
                info = None
                for hex_key, val in lz.table.items():
                    if bytes.fromhex(hex_key) == eb:
                        # Find morpheme name from byte_to_info would be ideal
                        # but just show hex for now
                        esp_morphemes.append(hex_key)
                        break
                if not esp_morphemes or esp_morphemes[-1] != eb.hex():
                    esp_morphemes.append(eb.hex())
            print(f"  '{eng_word}' ({llz_bytes.hex()}) -> esp: {esp_morphemes}")

    print("\n=== REVERSE BRIDGE TEST ===")
    # Encode "the dog ran" through LLZ encoder, then bridge_reverse to Esperanto
    encoded = lz.llz.encode("the dog ran")
    print(f"  Input: 'the dog ran' -> LLZ bytes: {encoded.hex()}")
    rev_result = lz.bridge_reverse(encoded)
    for entry_type, data in rev_result:
        if entry_type == 'control':
            print(f"    [{ctrl_names.get(data, hex(data))}]")
        else:
            print(f"    -> {len(data)} Esperanto candidate(s): {[c.hex() for c in data[:5]]}")

    print("\n=== COVERAGE ===")
    print(f"  Forward table (Esp→Eng): {len(lz.table):,} entries")
    print(f"  Reverse table (Eng→Esp): {len(lz.reverse):,} entries")
