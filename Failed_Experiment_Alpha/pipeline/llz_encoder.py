"""
LLZ English Encoder/Decoder

Pure table lookup. English word in, bytes out. Bytes in, English word out.

DEFAULT TO TABLE LOOKUP.

Author: Travis Edward Holley
Encoder: Claude (Anthropic)
"""

import re
import os
import sys

# Control bytes (shared with Esperanto table)
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

CONTROL_BYTES = set(range(0x00, 0x0A))


class LLZEncoder:
    """
    Encodes English text to byte streams using the LLZ English word table.
    Decodes byte streams back to English text.

    Pure table lookup. Word in, bytes out. Bytes in, word out.
    """

    def __init__(self, table_path=None):
        base = os.path.dirname(__file__)

        if table_path is None:
            table_path = os.path.join(base, 'llz_english_table.txt')

        self.encode_table = {}   # word -> bytes
        self.decode_table = {}   # bytes (as hex string) -> word
        self._max_phrase_len = 1  # single words only for now

        self._load_table(table_path)

    def _load_table(self, path):
        """Load encode and decode tables from llz_english_table.txt.

        Format: Index<TAB>Entry<TAB>Hex Code<TAB>Type
        Builds both directions in one pass. DEFAULT TO TABLE LOOKUP.
        """
        print(f"Loading LLZ table...", end='', flush=True)
        skipped_types = {'Control Byte'}
        collisions = 0

        with open(path, 'r', encoding='utf-8') as f:
            header = f.readline()  # skip header
            for line in f:
                line = line.rstrip('\n')
                if not line:
                    continue
                parts = line.split('\t')
                if len(parts) < 4:
                    continue

                entry = parts[1]
                hex_code = parts[2]
                entry_type = parts[3]

                # Skip control bytes — handled as constants
                if entry_type in skipped_types:
                    continue

                # Convert hex string (e.g. "0x0a0b") to bytes
                try:
                    code_bytes = bytes.fromhex(hex_code[2:])  # strip "0x"
                except ValueError:
                    continue

                # Encode direction: entry -> bytes
                # First occurrence wins (higher frequency = earlier in file)
                if entry not in self.encode_table:
                    self.encode_table[entry] = code_bytes

                # Decode direction: bytes -> entry
                hex_key = code_bytes.hex()
                if hex_key not in self.decode_table:
                    self.decode_table[hex_key] = entry
                else:
                    collisions += 1

        print(f" {len(self.encode_table):,} encode, {len(self.decode_table):,} decode")
        if collisions:
            print(f"  WARNING: {collisions:,} byte code collisions (first entry wins)")

    # ------------------------------------------------------------------
    # TEXT NORMALIZATION
    # ------------------------------------------------------------------

    @staticmethod
    def normalize(text):
        """Normalize text for encoding. Lowercase, fix unicode."""
        text = text.lower()
        # Smart quotes to straight
        text = (text
            .replace('\u2019', "'").replace('\u2018', "'")
            .replace('\u201c', '"').replace('\u201d', '"')
            .replace('\u2014', '-').replace('\u2013', '-')
            .replace('\u2026', '...')
        )
        return text

    # ------------------------------------------------------------------
    # ENCODE
    # ------------------------------------------------------------------

    def encode(self, text):
        """Encode English text to byte stream.

        Returns bytearray of encoded bytes.
        Words separated by SPACE (0x02).
        Punctuation is its own token with SPACE on both sides.
        Unknown words are spelled out letter by letter with BOUNDARY between.
        """
        text = self.normalize(text)
        result = bytearray()

        # Tokenize: split ALL punctuation into separate tokens with spaces
        # "the cat sat." -> ["the", "cat", "sat", "."]
        # "double-edged" -> ["double", "-", "edged"]
        # "2:30" -> ["2", ":", "30"]
        # "hello" -> ['"', "hello", '"']
        # Word chars include accented letters (àáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿ etc.)
        tokens = re.findall(r"[\w]+(?:'[\w]+)*|[.,!?;:\"\'\-]", text, re.UNICODE)

        for t_idx, token in enumerate(tokens):
            if not token:
                continue

            # Look up token (word or punctuation)
            if token in self.encode_table:
                result.extend(self.encode_table[token])
            else:
                # Unknown word — spell it out letter by letter
                for c_idx, char in enumerate(token):
                    if char in self.encode_table:
                        result.extend(self.encode_table[char])
                    # BOUNDARY between letters of spelled word
                    if c_idx < len(token) - 1:
                        result.append(BOUNDARY)

            # SPACE between all tokens (words AND punctuation)
            if t_idx < len(tokens) - 1:
                result.append(SPACE)

        return bytes(result)

    # ------------------------------------------------------------------
    # DECODE
    # ------------------------------------------------------------------

    def decode(self, data):
        """Decode byte stream back to English text.

        SPACE (0x02) dumps accumulator — token boundary.
        Punctuation is its own SPACE-separated token; reassembled naturally.
        BOUNDARY (0x01) stays in accumulator (part of spelled-out word).
        END (0x00) terminates.
        """
        if isinstance(data, (bytes, bytearray)):
            pass
        else:
            raise TypeError("Expected bytes or bytearray")

        tokens = []
        acc = bytearray()

        for b in data:
            if b == END:
                if acc:
                    tokens.append(self._lookup(acc))
                    acc = bytearray()
                break

            elif b == SPACE:
                if acc:
                    tokens.append(self._lookup(acc))
                    acc = bytearray()

            elif b == NEWLINE:
                if acc:
                    tokens.append(self._lookup(acc))
                    acc = bytearray()
                tokens.append('\n')

            elif b == BOUNDARY:
                acc.append(b)

            else:
                acc.append(b)

        if acc:
            tokens.append(self._lookup(acc))

        # Reassemble: join tokens with spaces — punctuation keeps its spaces
        return ' '.join(tokens)

    def _lookup(self, acc):
        """Look up accumulated bytes in decode table."""
        # Try full sequence first
        hex_key = bytes(acc).hex()
        if hex_key in self.decode_table:
            result = self.decode_table[hex_key]
            if isinstance(result, list):
                return result[0]  # Pick first option
            return result

        # If has BOUNDARY, try splitting on it
        if BOUNDARY in acc:
            parts = []
            current = bytearray()
            for b in acc:
                if b == BOUNDARY:
                    if current:
                        hex_part = bytes(current).hex()
                        if hex_part in self.decode_table:
                            result = self.decode_table[hex_part]
                            parts.append(result if isinstance(result, str) else result[0])
                        else:
                            parts.append(f'[?{hex_part}]')
                        current = bytearray()
                else:
                    current.append(b)
            if current:
                hex_part = bytes(current).hex()
                if hex_part in self.decode_table:
                    result = self.decode_table[hex_part]
                    parts.append(result if isinstance(result, str) else result[0])
                else:
                    parts.append(f'[?{hex_part}]')
            return ''.join(parts)

        return f'[?{hex_key}]'


# ------------------------------------------------------------------
# PASSTHROUGH TEST
# ------------------------------------------------------------------

def tokenize_normalized(text):
    """Tokenize text the same way the encoder does, for comparison."""
    text = LLZEncoder.normalize(text)
    tokens = re.findall(r"[\w]+(?:'[\w]+)*|[.,!?;:\"\'\-]", text, re.UNICODE)
    return ' '.join(tokens)


def passthrough_test(encoder, sentences):
    """Encode then decode, check if original is recoverable."""
    passed = 0
    failed = 0

    for sent in sentences:
        encoded = encoder.encode(sent)
        decoded = encoder.decode(encoded)

        # Compare tokenized forms — both should be space-separated tokens
        orig = tokenize_normalized(sent)
        dec = decoded.strip()

        if orig == dec:
            passed += 1
        else:
            failed += 1
            if failed <= 10:
                print(f'  FAIL:')
                print(f'    IN:  {orig}')
                print(f'    OUT: {dec}')

    return passed, failed


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')

    enc = LLZEncoder()

    print(f'\n=== BASIC ENCODE/DECODE TEST ===')
    test_sentences = [
        "Hello world.",
        "I love you.",
        "The cat sat on the mat.",
        "Don't worry about it.",
        "She can't believe what happened.",
        "We're going to the store.",
        "How much does that cost?",
        "It's raining outside.",
        "The quick brown fox jumps over the lazy dog.",
        "Turn your brain back on.",
    ]

    for sent in test_sentences:
        encoded = enc.encode(sent)
        decoded = enc.decode(encoded)
        orig = tokenize_normalized(sent)
        match = 'PASS' if orig == decoded.strip() else 'FAIL'
        print(f'  [{match}] {sent}')
        if match == 'FAIL':
            print(f'         IN:  {orig}')
            print(f'         OUT: {decoded.strip()}')
            print(f'         HEX: {encoded.hex()}')

    print(f'\n=== PASSTHROUGH TEST (Tatoeba sample) ===')
    tatoeba_path = os.path.join(os.path.dirname(__file__), 'llz_english_sentences.txt')
    if os.path.exists(tatoeba_path):
        with open(tatoeba_path, 'r', encoding='utf-8') as f:
            tatoeba = [line.strip() for line in f if line.strip()][:10000]

        p, fail = passthrough_test(enc, tatoeba)
        total = p + fail
        print(f'\n  Tested: {total:,}')
        print(f'  PASS:    {p:,} ({p/total*100:.1f}%)')
        print(f'  FAIL:    {fail:,} ({fail/total*100:.1f}%)')
