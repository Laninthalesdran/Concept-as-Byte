"""
Jalek Encoder/Decoder

Pure table lookup. Word in, bytes out. Bytes in, word out.

DEFAULT TO TABLE LOOKUP WITH ANY REASONING FOR JALEKCORE TABLE ENCODER DECODER

IMPORTANT: This encoder operates on the JalekCore Base Table only. It encodes
individual Esperanto morphemes to byte codes. It does NOT support automatic
morphological decomposition of English words. If you input "hospital", it will
not decompose it into mal·san·ul·ej·o. The English-to-Esperanto morpheme
decomposition pipeline is not included in this release.

License: CC-BY-NC-SA 4.0
Patent: U.S. Application No. 64/017,122
Author: Travis Edward Holley
"""

import os

# Control bytes
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


class JalekEncoder:
    """
    Encodes text to Jalek byte streams using the JalekCore table.
    Decodes Jalek byte streams back to text.

    The encoder is a pure table lookup. Greedy longest match.
    Word in, bytes out. Bytes in, word out.
    """

    def __init__(self, table_path=None):
        if table_path is None:
            table_path = os.path.join(os.path.dirname(__file__), 'JalekCore_Base_Table.txt')

        self.encode_table = {}  # morpheme -> bytes
        self.decode_table = {}  # bytes -> morpheme

        self._load_table(table_path)

    def _load_table(self, path):
        """Load the tab-delimited JalekCore table."""
        with open(path, 'r', encoding='utf-8') as f:
            header = f.readline()  # skip header
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split('\t')
                if len(parts) < 4:
                    continue

                tier = parts[0]
                index = parts[1]
                morpheme = parts[2]
                hex_code = parts[3]

                if morpheme.startswith('---'):
                    continue

                # Strip 0x prefix
                hex_clean = hex_code.replace('0x', '')

                # Convert to bytes
                code_bytes = bytes.fromhex(hex_clean)

                self.encode_table[morpheme] = code_bytes
                self.decode_table[code_bytes] = morpheme

        print(f"JalekEncoder loaded: {len(self.encode_table)} entries")

    def encode(self, text):
        """
        Encode text to Jalek byte stream.

        Greedy longest match against the table.
        Words separated by SPACE byte.
        Lines separated by NEWLINE byte.
        """
        result = bytearray()
        lines = text.split('\n')

        for line_idx, line in enumerate(lines):
            words = line.strip().split()

            for word_idx, word in enumerate(words):
                word_lower = word.lower().strip()

                # Numbers: encode as digit bytes directly
                if word_lower.replace('.', '').isdigit():
                    for ci, char in enumerate(word_lower):
                        if char in self.encode_table:
                            result.extend(self.encode_table[char])
                        if ci < len(word_lower) - 1:
                            result.append(BOUNDARY)
                # Try table lookup (greedy longest match for multi-word)
                elif word_lower in self.encode_table:
                    result.extend(self.encode_table[word_lower])
                else:
                    # COIN: spell letter by letter
                    result.append(COIN)
                    for i, char in enumerate(word_lower):
                        if char in self.encode_table:
                            result.extend(self.encode_table[char])
                        if i < len(word_lower) - 1:
                            result.append(BOUNDARY)

                # SPACE between words
                if word_idx < len(words) - 1:
                    result.append(SPACE)

            # NEWLINE between lines
            if line_idx < len(lines) - 1:
                result.append(NEWLINE)

        result.append(END)
        return bytes(result)

    def _flush_acc(self, accumulator, current_word):
        """Look up accumulator in decode table, append to current word."""
        if accumulator:
            key = bytes(accumulator)
            if key in self.decode_table:
                current_word.append(self.decode_table[key])
            else:
                current_word.append(f"[0x{key.hex()}]")

    def decode(self, data):
        """
        Decode Jalek byte stream back to text.

        Simple rules:
        - Content byte → accumulate
        - BOUNDARY → flush accumulator as morpheme lookup, stay in same word
        - SPACE → flush accumulator, dump whole word, start new word
        - END → flush everything, done
        - All other control bytes → flush accumulator

        No special digit handling. No NOT gate. Digits are in the decode
        table like any other morpheme. The decoder just accumulates between
        control bytes and looks up what it collected.
        """
        if isinstance(data, (bytes, bytearray)):
            data = list(data)

        result = []
        current_word = []
        accumulator = bytearray()

        for byte in data:
            if byte == SPACE:
                # Dump: look up everything accumulated, output the word
                self._flush_acc(accumulator, current_word)
                accumulator = bytearray()
                if current_word:
                    result.append(''.join(current_word))
                    current_word = []

            elif byte == END:
                self._flush_acc(accumulator, current_word)
                accumulator = bytearray()
                if current_word:
                    result.append(''.join(current_word))
                    current_word = []
                break

            elif byte == NEWLINE:
                self._flush_acc(accumulator, current_word)
                accumulator = bytearray()
                if current_word:
                    result.append(''.join(current_word))
                    current_word = []
                result.append('\n')

            elif byte == QA:
                self._flush_acc(accumulator, current_word)
                accumulator = bytearray()
                if current_word:
                    result.append(''.join(current_word))
                    current_word = []

            else:
                # Everything else — content bytes AND boundary bytes — accumulate
                accumulator.append(byte)

        # Flush anything remaining
        self._flush_acc(accumulator, current_word)
        if current_word:
            result.append(''.join(current_word))

        return ' '.join(result)

    def table_stats(self):
        """Print table statistics."""
        one_byte = sum(1 for k in self.encode_table.values() if len(k) == 1)
        two_byte = sum(1 for k in self.encode_table.values() if len(k) == 2)
        print(f"Encode table: {len(self.encode_table)} entries")
        print(f"  Single-byte: {one_byte}")
        print(f"  Two-byte: {two_byte}")
        print(f"Decode table: {len(self.decode_table)} entries")


# ============================================================
# Standalone test
# ============================================================
if __name__ == "__main__":
    encoder = JalekEncoder()
    encoder.table_stats()

    print("\n--- Encode/Decode Test ---")
    test = "la mal san ul o"
    encoded = encoder.encode(test)
    print(f"Input:   {test}")
    print(f"Encoded: {[f'0x{b:02x}' for b in encoded]}")
    decoded = encoder.decode(encoded)
    print(f"Decoded: {decoded}")
