"""
Build Matched Training Data — BPE vs Concept Bytes
===================================================
Same 414K Tatoeba Esperanto sentences, two encodings.

1. Load Esperanto concept byte encoder
2. Read Tatoeba TSV, extract Esperanto sentences
3. Encode each with concept bytes — keep only the ones that succeed
4. Train a SentencePiece BPE tokenizer on the SAME sentences
5. BPE-encode those sentences
6. Write both training binaries

Output:
  concept_byte_training.bin — concept byte encoded (same as Beta)
  bpe_training.bin — BPE tokenized (matched control)
  esperanto_sentences.txt — the raw text (for verification)

Author: Travis Edward Holley
Builder: Claude (Anthropic)
"""

import sys
import os
import json
import re
import time
import struct

sys.stdout.reconfigure(encoding='utf-8')

t0 = time.time()

# ============================================================
# CONFIG
# ============================================================
WORK_DIR = os.path.dirname(os.path.abspath(__file__))
TSV_FILE = os.path.join(WORK_DIR, 'tatoeba.tsv')
ENCODER_FILE = os.path.join(WORK_DIR, 'wiktionary_full_esperanto.json')
BPE_VOCAB_SIZE = 2000  # match bpe_baseline_model.py

# Control bytes (must match Beta exactly)
END = 0x00
SPACE = 0x02
PERIOD = 0x14

# ============================================================
# LOAD ESPERANTO CONCEPT BYTE ENCODER
# ============================================================
print("Loading Esperanto concept byte encoder...", flush=True)
esp_word_to_bytes = {}
with open(ENCODER_FILE, 'r', encoding='utf-8') as f:
    wikt = json.load(f)

for word, record in wikt.items():
    bs = record.get('byte_sequence', '')
    if bs:
        try:
            code = bytes.fromhex(bs[2:] if bs.startswith('0x') else bs)
            esp_word_to_bytes[word.lower()] = code
        except:
            pass

print(f"  Encoder loaded: {len(esp_word_to_bytes):,} Esperanto words", flush=True)


def x_to_esp(s):
    """Convert x-notation to Esperanto diacritics."""
    s = s.replace('cx', '\u0109').replace('gx', '\u011d').replace('hx', '\u0125')
    s = s.replace('jx', '\u0135').replace('sx', '\u015d').replace('ux', '\u016d')
    return s


def encode_esperanto(text):
    """Encode Esperanto text to concept bytes. Returns bytes or None if too short."""
    text = text.lower().strip()
    tokens = re.findall(r"[\w]+(?:'[\w]+)*|[.,!?;:\"\'\-]", text, re.UNICODE)
    result = bytearray()
    for i, token in enumerate(tokens):
        tl = token.lower()
        tl_conv = x_to_esp(tl)
        if tl in esp_word_to_bytes:
            result.extend(esp_word_to_bytes[tl])
        elif tl_conv in esp_word_to_bytes:
            result.extend(esp_word_to_bytes[tl_conv])
        else:
            continue
        if i < len(tokens) - 1:
            result.append(SPACE)
    return bytes(result) if len(result) >= 2 else None


# ============================================================
# PASS 1: READ TSV, ENCODE WITH CONCEPT BYTES, FILTER
# ============================================================
print("Reading Tatoeba TSV and encoding with concept bytes...", flush=True)

esperanto_sentences = []  # raw text of successfully encoded sentences
concept_byte_chains = []  # encoded byte chains

total_lines = 0
encoded_count = 0

with open(TSV_FILE, 'r', encoding='utf-8-sig') as f:
    for line in f:
        total_lines += 1
        parts = line.rstrip('\n').split('\t')
        # TSV format: esp_id \t esperanto_text \t eng_id \t english_text
        if len(parts) < 4:
            continue
        esp_text = parts[1].strip()
        if not esp_text:
            continue

        encoded = encode_esperanto(esp_text)
        if encoded is None:
            continue

        # Build chain: [encoded bytes] SPACE PERIOD END
        chain = encoded + bytes([SPACE, PERIOD, END])
        if len(chain) > 510:
            continue

        esperanto_sentences.append(esp_text)
        concept_byte_chains.append(chain)
        encoded_count += 1

        if encoded_count % 100000 == 0:
            print(f"  {encoded_count:,} encoded...", flush=True)

print(f"  Total lines: {total_lines:,}", flush=True)
print(f"  Successfully encoded: {encoded_count:,}", flush=True)
print(f"  Encode rate: {encoded_count/total_lines*100:.1f}%", flush=True)

# ============================================================
# WRITE CONCEPT BYTE TRAINING BINARY
# ============================================================
print("\nWriting concept byte training binary...", flush=True)

cb_path = os.path.join(WORK_DIR, 'concept_byte_training.bin')
total_cb_bytes = 0
with open(cb_path, 'wb') as f:
    for chain in concept_byte_chains:
        f.write(chain)
        total_cb_bytes += len(chain)

cb_size = os.path.getsize(cb_path)
print(f"  Written: {cb_path} ({cb_size/1e6:.1f}MB, {total_cb_bytes:,} bytes)", flush=True)

# ============================================================
# SAVE RAW TEXT FOR BPE TRAINING AND VERIFICATION
# ============================================================
print("\nSaving raw Esperanto text...", flush=True)

text_path = os.path.join(WORK_DIR, 'esperanto_sentences.txt')
with open(text_path, 'w', encoding='utf-8') as f:
    for sent in esperanto_sentences:
        f.write(sent + '\n')

print(f"  Written: {text_path} ({len(esperanto_sentences):,} sentences)", flush=True)

# ============================================================
# TRAIN BPE TOKENIZER ON THE SAME SENTENCES
# ============================================================
print(f"\nTraining SentencePiece BPE tokenizer (vocab={BPE_VOCAB_SIZE})...", flush=True)

import sentencepiece as spm

bpe_prefix = os.path.join(WORK_DIR, 'bpe_esperanto')
spm.SentencePieceTrainer.Train(
    input=text_path,
    model_prefix=bpe_prefix,
    vocab_size=BPE_VOCAB_SIZE,
    model_type='bpe',
    character_coverage=0.9995,
    max_sentence_length=4096,
    input_sentence_size=500000,
    shuffle_input_sentence=True,
)
print(f"  Tokenizer trained: {bpe_prefix}.model", flush=True)

# ============================================================
# BPE-ENCODE THE SAME SENTENCES
# ============================================================
print("\nEncoding with BPE...", flush=True)

sp = spm.SentencePieceProcessor()
sp.Load(f'{bpe_prefix}.model')

bpe_path = os.path.join(WORK_DIR, 'bpe_training.bin')
total_bpe_tokens = 0
bpe_sentences = 0

with open(bpe_path, 'wb') as f:
    for sent in esperanto_sentences:
        ids = sp.EncodeAsIds(sent)
        if len(ids) < 1:
            # Still write a minimal entry to keep sentence count matched
            ids = [0]
        # Write token IDs as 16-bit integers (little-endian)
        for token_id in ids:
            f.write(struct.pack('<H', token_id))
        # Write EOS (token ID 1 in SentencePiece = </s>)
        f.write(struct.pack('<H', 1))
        total_bpe_tokens += len(ids) + 1
        bpe_sentences += 1

bpe_size = os.path.getsize(bpe_path)
print(f"  Written: {bpe_path} ({bpe_size/1e6:.1f}MB, {total_bpe_tokens:,} tokens)", flush=True)
print(f"  BPE sentences: {bpe_sentences:,}", flush=True)

# ============================================================
# VERIFICATION
# ============================================================
elapsed = time.time() - t0

print(f"\n{'='*60}", flush=True)
print(f"MATCHED DATA BUILD COMPLETE", flush=True)
print(f"{'='*60}", flush=True)
print(f"Concept bytes: {encoded_count:,} sentences, {cb_size/1e6:.1f}MB", flush=True)
print(f"BPE tokens:    {bpe_sentences:,} sentences, {bpe_size/1e6:.1f}MB, {total_bpe_tokens:,} tokens", flush=True)
print(f"Sentence match: {'YES' if encoded_count == bpe_sentences else 'NO — MISMATCH'}", flush=True)
print(f"BPE vocab size: {BPE_VOCAB_SIZE}", flush=True)
print(f"Time: {elapsed:.0f}s", flush=True)

# Quick stats
avg_cb = total_cb_bytes / encoded_count
avg_bpe = total_bpe_tokens / bpe_sentences
print(f"\nAvg concept bytes per sentence: {avg_cb:.1f}", flush=True)
print(f"Avg BPE tokens per sentence:   {avg_bpe:.1f}", flush=True)
print(f"Compression ratio (BPE tokens / CB bytes): {avg_bpe/avg_cb:.2f}x", flush=True)
print("Done.", flush=True)
