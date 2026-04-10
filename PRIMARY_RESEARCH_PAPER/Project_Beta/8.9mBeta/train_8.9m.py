"""
Experiment Beta — 8.9M Model (Config 6)
d=280, L=7, h=7, ff=1120

Self-contained: model, training, and all 3 instrumentation layers.
No external imports beyond PyTorch and stdlib.

Three Layers of Instrumentation:
  Layer 1: Training data statistics (byte frequencies, morpheme counts, chain lengths)
  Layer 2: Neural recorder snapshots at each eval on fixed reference sentence
  Layer 3: Frequency-to-weight correlation (does frequency predict attention, or does relevance?)

Author: Travis Edward Holley
Architecture: Claude (Anthropic)
"""

import sys
import os
import time
import math
import json
import logging
import struct
from collections import Counter, defaultdict

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader

sys.stdout.reconfigure(encoding='utf-8')

# ============================================================
# CONFIG — this model
# ============================================================
CONFIG_NUM = 6
D_MODEL = 280
N_LAYERS = 7
N_HEADS = 7
D_FF = 1120
PARAMS_LABEL = '8.9M'
SEQ_LEN = 512
BATCH_SIZE = 256
MAX_EPOCHS = 10
PATIENCE = 3
LR = 3e-4
WARMUP = 1000
USE_COMPILE = False  # Triton not available on Windows
USE_BF16 = True
NUM_WORKERS = 4
DATA_FILE = '8.9m_beta_training.bin'
TABLE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'JalekCore_Base_Table.txt')

# Output directories (relative to this script)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(SCRIPT_DIR, 'logs')
CHECKPOINT_DIR = os.path.join(SCRIPT_DIR, 'checkpoints')
LAYER1_DIR = os.path.join(SCRIPT_DIR, 'layer1_stats')
LAYER2_DIR = os.path.join(SCRIPT_DIR, 'layer2_recordings')
LAYER3_DIR = os.path.join(SCRIPT_DIR, 'layer3_correlation')

for d in [LOG_DIR, CHECKPOINT_DIR, LAYER1_DIR, LAYER2_DIR, LAYER3_DIR]:
    os.makedirs(d, exist_ok=True)

# ============================================================
# BYTE TABLE LOADER — decode bytes to concept labels
# ============================================================

def load_byte_table(table_path):
    """Load JalekCore base table. Returns hex_code -> (morpheme, english, type) dict."""
    table = {}
    if not os.path.exists(table_path):
        print(f"WARNING: Table not found at {table_path}")
        return table
    with open(table_path, 'r', encoding='utf-8') as f:
        header = f.readline()
        for line in f:
            parts = line.rstrip('\n').split('\t')
            if len(parts) >= 6:
                morpheme = parts[2]
                hex_code = parts[3]
                english = parts[4]
                entry_type = parts[5]
                # Strip 0x prefix and lowercase
                hex_key = hex_code[2:].lower() if hex_code.startswith('0x') else hex_code.lower()
                table[hex_key] = (morpheme, english, entry_type)
    return table


CONTROL_BYTES = {
    0x00: 'END', 0x01: 'BOUNDARY', 0x02: 'SPACE', 0x03: 'NEWLINE',
    0x04: 'PARAGRAPH', 0x05: 'Q/A', 0x06: 'SKIP', 0x07: 'JALEKON',
    0x08: 'NAME', 0x09: 'COIN',
}


def label_byte_sequence(byte_seq, table):
    """Decode a byte sequence to human-readable concept labels using greedy longest match."""
    labels = []
    i = 0
    while i < len(byte_seq):
        b = byte_seq[i]

        # Control bytes
        if b in CONTROL_BYTES:
            labels.append((i, 1, f'[{CONTROL_BYTES[b]}]', 'control'))
            i += 1
            continue

        # Greedy longest match: try 4, 3, 2, 1 byte codes
        matched = False
        for length in [4, 3, 2, 1]:
            if i + length > len(byte_seq):
                continue
            # Don't span across control bytes
            span = byte_seq[i:i+length]
            if any(s in CONTROL_BYTES for s in span[1:]):
                continue
            hex_key = ''.join(f'{byte_seq[i+j]:02x}' for j in range(length))
            if hex_key in table:
                morpheme, english, entry_type = table[hex_key]
                labels.append((i, length, morpheme, entry_type))
                i += length
                matched = True
                break

        if not matched:
            labels.append((i, 1, f'0x{b:02x}', 'unknown'))
            i += 1

    return labels


# ============================================================
# MODEL
# ============================================================

class RMSNorm(nn.Module):
    def __init__(self, dim, eps=1e-6):
        super().__init__()
        self.eps = eps
        self.weight = nn.Parameter(torch.ones(dim))
    def forward(self, x):
        return x * torch.rsqrt(x.pow(2).mean(-1, keepdim=True) + self.eps) * self.weight


class RotaryEmbedding(nn.Module):
    def __init__(self, dim, max_seq_len=512):
        super().__init__()
        inv_freq = 1.0 / (10000 ** (torch.arange(0, dim, 2).float() / dim))
        self.register_buffer('inv_freq', inv_freq)
    def forward(self, seq_len, device):
        t = torch.arange(seq_len, device=device, dtype=self.inv_freq.dtype)
        freqs = torch.outer(t, self.inv_freq)
        emb = torch.cat((freqs, freqs), dim=-1)
        return emb.cos(), emb.sin()


def rotate_half(x):
    x1, x2 = x.chunk(2, dim=-1)
    return torch.cat((-x2, x1), dim=-1)


def apply_rotary(q, k, cos, sin):
    cos = cos.unsqueeze(0).unsqueeze(0)
    sin = sin.unsqueeze(0).unsqueeze(0)
    return (q * cos) + (rotate_half(q) * sin), (k * cos) + (rotate_half(k) * sin)


class SwiGLU(nn.Module):
    def __init__(self, d, ff):
        super().__init__()
        self.w1 = nn.Linear(d, ff, bias=False)
        self.w2 = nn.Linear(ff, d, bias=False)
        self.w3 = nn.Linear(d, ff, bias=False)
    def forward(self, x):
        return self.w2(F.silu(self.w1(x)) * self.w3(x))


class Attention(nn.Module):
    def __init__(self, d, h):
        super().__init__()
        self.n_heads = h
        self.head_dim = d // h
        self.wq = nn.Linear(d, d, bias=False)
        self.wk = nn.Linear(d, d, bias=False)
        self.wv = nn.Linear(d, d, bias=False)
        self.wo = nn.Linear(d, d, bias=False)

    def forward(self, x, cos, sin, mask, return_attention=False):
        B, T, C = x.shape
        q = self.wq(x).view(B, T, self.n_heads, self.head_dim).transpose(1, 2)
        k = self.wk(x).view(B, T, self.n_heads, self.head_dim).transpose(1, 2)
        v = self.wv(x).view(B, T, self.n_heads, self.head_dim).transpose(1, 2)
        q, k = apply_rotary(q, k, cos[:T], sin[:T])
        att = (q @ k.transpose(-2, -1)) * (self.head_dim ** -0.5)
        att = att.masked_fill(mask[:, :, :T, :T] == 0, float('-inf'))
        att = F.softmax(att, dim=-1)
        out = self.wo((att @ v).transpose(1, 2).contiguous().view(B, T, C))
        if return_attention:
            return out, att
        return out


class Block(nn.Module):
    def __init__(self, d, h, ff):
        super().__init__()
        self.attn = Attention(d, h)
        self.ffn = SwiGLU(d, ff)
        self.n1 = RMSNorm(d)
        self.n2 = RMSNorm(d)

    def forward(self, x, cos, sin, mask, return_attention=False):
        if return_attention:
            attn_out, att_weights = self.attn(self.n1(x), cos, sin, mask, return_attention=True)
            x = x + attn_out
            x = x + self.ffn(self.n2(x))
            return x, att_weights
        x = x + self.attn(self.n1(x), cos, sin, mask)
        x = x + self.ffn(self.n2(x))
        return x


class BetaModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.d = D_MODEL
        self.n_layers = N_LAYERS
        self.n_heads = N_HEADS
        self.d_ff = D_FF

        self.embed = nn.Embedding(256, self.d)
        self.rotary = RotaryEmbedding(self.d // self.n_heads)
        self.layers = nn.ModuleList([Block(self.d, self.n_heads, self.d_ff) for _ in range(self.n_layers)])
        self.norm = RMSNorm(self.d)
        self.output = nn.Linear(self.d, 256, bias=False)
        self.output.weight = self.embed.weight  # tied embeddings
        mask = torch.tril(torch.ones(SEQ_LEN, SEQ_LEN))
        self.register_buffer('mask', mask.unsqueeze(0).unsqueeze(0))
        self._init_weights()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, std=0.02)
            elif isinstance(m, nn.Embedding):
                nn.init.normal_(m.weight, std=0.02)

    def forward(self, idx, targets=None):
        B, T = idx.shape
        x = self.embed(idx)
        cos, sin = self.rotary(T, idx.device)
        for layer in self.layers:
            x = layer(x, cos, sin, self.mask)
        logits = self.output(self.norm(x))
        loss = None
        if targets is not None:
            loss = F.cross_entropy(logits.view(-1, 256), targets.view(-1), ignore_index=-1)
        return logits, loss

    def forward_with_attention(self, idx):
        """Forward pass that returns attention weights from every layer."""
        B, T = idx.shape
        x = self.embed(idx)
        cos, sin = self.rotary(T, idx.device)
        all_attention = []
        for layer in self.layers:
            x, att_weights = layer(x, cos, sin, self.mask, return_attention=True)
            all_attention.append(att_weights.detach().cpu())
        logits = self.output(self.norm(x))
        return logits, all_attention

    def count_parameters(self):
        return sum(p.numel() for p in self.parameters() if p.requires_grad)


# ============================================================
# DATASET
# ============================================================

class ByteDataset(Dataset):
    def __init__(self, bin_path, seq_len=512):
        self.seq_len = seq_len
        with open(bin_path, 'rb') as f:
            data = f.read()
        self.chains = []
        current = bytearray()
        for b in data:
            current.append(b)
            if b == 0x00:  # END byte
                if len(current) >= 4:
                    self.chains.append(bytes(current))
                current = bytearray()

    def __len__(self):
        return len(self.chains)

    def __getitem__(self, idx):
        chain = self.chains[idx]
        if len(chain) > self.seq_len + 1:
            chain = chain[:self.seq_len + 1]
        data = torch.tensor(list(chain), dtype=torch.long)
        if len(data) < self.seq_len + 1:
            pad = torch.full((self.seq_len + 1 - len(data),), -1, dtype=torch.long)
            data = torch.cat([data, pad])
        x = data[:-1].clamp(min=0)
        y = data[1:]
        return x, y


# ============================================================
# LAYER 1 — TRAINING DATA STATISTICS
# ============================================================

def run_layer1(data_path, table, output_dir):
    """Compute and save training data statistics before training begins."""
    print("=" * 60)
    print("LAYER 1 — Training Data Statistics")
    print("=" * 60)

    with open(data_path, 'rb') as f:
        raw = f.read()

    total_bytes = len(raw)

    # Split into chains on END byte
    chains = []
    current = bytearray()
    for b in raw:
        current.append(b)
        if b == 0x00:
            if len(current) >= 4:
                chains.append(bytes(current))
            current = bytearray()

    # Byte frequency
    byte_freq = Counter(raw)

    # Chain length distribution
    chain_lengths = [len(c) for c in chains]

    # Morpheme frequency (using greedy decode on each chain)
    morpheme_freq = Counter()
    type_freq = Counter()
    for chain in chains:
        labels = label_byte_sequence(list(chain), table)
        for pos, length, label, entry_type in labels:
            morpheme_freq[label] += 1
            type_freq[entry_type] += 1

    # Build stats
    stats = {
        'total_bytes': total_bytes,
        'total_chains': len(chains),
        'unique_byte_values': len(byte_freq),
        'chain_length': {
            'min': min(chain_lengths),
            'max': max(chain_lengths),
            'mean': sum(chain_lengths) / len(chain_lengths),
            'median': sorted(chain_lengths)[len(chain_lengths) // 2],
        },
        'byte_frequency': {f'0x{b:02x}': count for b, count in byte_freq.most_common()},
        'morpheme_frequency_top100': {label: count for label, count in morpheme_freq.most_common(100)},
        'type_distribution': dict(type_freq),
    }

    # Save
    stats_path = os.path.join(output_dir, 'data_statistics.json')
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    # Print summary
    print(f"  Total bytes: {total_bytes:,}")
    print(f"  Total chains: {len(chains):,}")
    print(f"  Unique byte values: {len(byte_freq)}")
    print(f"  Chain length: min={min(chain_lengths)}, max={max(chain_lengths)}, "
          f"mean={sum(chain_lengths)/len(chain_lengths):.1f}")
    print(f"  Type distribution:")
    for t, c in sorted(type_freq.items(), key=lambda x: -x[1]):
        print(f"    {t}: {c:,}")
    print(f"  Top 10 morphemes:")
    for label, count in morpheme_freq.most_common(10):
        print(f"    {label}: {count:,}")
    print(f"  Saved to: {stats_path}")
    print()

    return byte_freq


# ============================================================
# LAYER 2 — NEURAL RECORDER SNAPSHOT
# ============================================================

def get_fixed_reference_sentence(data_path):
    """Extract a reference sentence from the training data for consistent snapshots."""
    with open(data_path, 'rb') as f:
        raw = f.read()
    # Find the first chain that's between 15-40 bytes (a good representative sentence)
    current = bytearray()
    for b in raw:
        current.append(b)
        if b == 0x00:
            if 15 <= len(current) <= 40:
                return list(current)
            current = bytearray()
    # Fallback: just use first chain
    current = bytearray()
    for b in raw:
        current.append(b)
        if b == 0x00:
            return list(current)
    return list(raw[:40])


def run_layer2(model, reference_sentence, table, epoch, output_dir, device):
    """Run neural recorder on the fixed reference sentence and save snapshot."""
    model.eval()
    seq = reference_sentence

    # Decode the reference sentence for logging
    labels = label_byte_sequence(seq, table)
    decoded = ' '.join(label for _, _, label, _ in labels)

    # Prepare input tensor
    input_tensor = torch.tensor([seq[:-1]], dtype=torch.long).to(device)  # all but last byte
    if input_tensor.shape[1] == 0:
        return

    with torch.no_grad():
        logits, all_attention = model.forward_with_attention(input_tensor)

    T = input_tensor.shape[1]
    probs = F.softmax(logits[0], dim=-1).cpu()

    snapshot = {
        'epoch': epoch,
        'reference_hex': [f'0x{b:02x}' for b in seq],
        'reference_decoded': decoded,
        'sequence_length': len(seq),
        'positions': [],
    }

    for pos in range(T):
        byte_val = seq[pos]
        pos_label = next((l for p, _, l, _ in labels if p == pos), f'0x{byte_val:02x}')

        # Top 5 predictions at this position
        top_vals, top_idxs = torch.topk(probs[pos], 5)
        predictions = []
        for val, idx in zip(top_vals, top_idxs):
            pred_hex = f'{idx.item():02x}'
            if idx.item() in CONTROL_BYTES:
                pred_label = f'[{CONTROL_BYTES[idx.item()]}]'
            elif pred_hex in table:
                pred_label = table[pred_hex][0]
            else:
                pred_label = f'0x{pred_hex}'
            predictions.append({
                'byte': idx.item(),
                'label': pred_label,
                'prob': round(val.item(), 4),
            })

        # What's actually next
        actual_next = seq[pos + 1] if pos + 1 < len(seq) else -1
        correct = predictions[0]['byte'] == actual_next if actual_next >= 0 else None

        # Attention per layer per head — top 3 attended positions
        attention_info = []
        for layer_idx, att in enumerate(all_attention):
            # att shape: [1, n_heads, T, T]
            layer_heads = []
            for head_idx in range(att.shape[1]):
                weights = att[0, head_idx, pos, :pos+1]  # causal: only attend to past
                if len(weights) == 0:
                    continue
                top_k = min(3, len(weights))
                vals, idxs = torch.topk(weights, top_k)
                head_info = []
                for v, idx in zip(vals, idxs):
                    target_byte = seq[idx.item()]
                    target_label = next((l for p, _, l, _ in labels if p == idx.item()), f'0x{target_byte:02x}')
                    head_info.append({
                        'target_pos': idx.item(),
                        'target_label': target_label,
                        'weight': round(v.item(), 4),
                    })
                layer_heads.append({
                    'head': head_idx,
                    'top_attended': head_info,
                })
            attention_info.append({
                'layer': layer_idx,
                'heads': layer_heads,
            })

        snapshot['positions'].append({
            'pos': pos,
            'byte': byte_val,
            'label': pos_label,
            'predictions': predictions,
            'actual_next': actual_next,
            'correct': correct,
            'attention': attention_info,
        })

    # Accuracy
    total = sum(1 for p in snapshot['positions'] if p['correct'] is not None)
    correct_count = sum(1 for p in snapshot['positions'] if p['correct'] is True)
    snapshot['accuracy'] = round(correct_count / max(1, total), 4)

    # Save
    snapshot_path = os.path.join(output_dir, f'snapshot_epoch_{epoch:03d}.json')
    with open(snapshot_path, 'w', encoding='utf-8') as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)

    print(f"  [Layer 2] Snapshot epoch {epoch}: accuracy={snapshot['accuracy']:.1%} "
          f"({correct_count}/{total}) | Saved: {snapshot_path}")

    model.train()
    return snapshot


# ============================================================
# LAYER 3 — FREQUENCY-TO-WEIGHT CORRELATION
# ============================================================

def run_layer3(model, byte_freq, reference_sentence, table, epoch, output_dir, device):
    """Compute correlation between training byte frequency and attention weight strength."""
    model.eval()
    seq = reference_sentence

    input_tensor = torch.tensor([seq[:-1]], dtype=torch.long).to(device)
    if input_tensor.shape[1] == 0:
        return

    with torch.no_grad():
        _, all_attention = model.forward_with_attention(input_tensor)

    T = input_tensor.shape[1]

    # For each byte in the reference sentence, compute:
    # 1. Its training frequency
    # 2. The average attention weight it RECEIVES across all layers/heads
    byte_attention = defaultdict(list)  # byte_value -> list of attention weights received

    for layer_idx, att in enumerate(all_attention):
        for head_idx in range(att.shape[1]):
            weights = att[0, head_idx]  # [T, T]
            for target_pos in range(T):
                target_byte = seq[target_pos]
                # Sum of attention this position receives from all other positions
                incoming = weights[:, target_pos].sum().item()
                byte_attention[target_byte].append(incoming)

    # Build correlation data
    correlation_data = []
    for byte_val in set(seq[:-1]):
        if byte_val in CONTROL_BYTES and byte_val == 0x00:
            continue  # skip END
        freq = byte_freq.get(byte_val, 0)
        avg_attn = sum(byte_attention.get(byte_val, [0])) / max(1, len(byte_attention.get(byte_val, [0])))
        hex_key = f'{byte_val:02x}'
        if byte_val in CONTROL_BYTES:
            label = f'[{CONTROL_BYTES[byte_val]}]'
        elif hex_key in table:
            label = table[hex_key][0]
        else:
            label = f'0x{hex_key}'

        correlation_data.append({
            'byte': byte_val,
            'hex': f'0x{byte_val:02x}',
            'label': label,
            'training_frequency': freq,
            'avg_attention_received': round(avg_attn, 6),
        })

    # Sort by training frequency
    correlation_data.sort(key=lambda x: -x['training_frequency'])

    # Compute Spearman rank correlation
    freqs = [d['training_frequency'] for d in correlation_data]
    attns = [d['avg_attention_received'] for d in correlation_data]

    # Rank-based correlation (manual Spearman)
    n = len(freqs)
    if n >= 3:
        freq_ranks = _rank(freqs)
        attn_ranks = _rank(attns)
        d_sq = sum((fr - ar) ** 2 for fr, ar in zip(freq_ranks, attn_ranks))
        spearman = 1 - (6 * d_sq) / (n * (n**2 - 1))
    else:
        spearman = None

    result = {
        'epoch': epoch,
        'spearman_correlation': round(spearman, 4) if spearman is not None else None,
        'interpretation': (
            'frequency_drives_attention' if spearman is not None and spearman > 0.7
            else 'relevance_overrides_frequency' if spearman is not None and spearman < 0.3
            else 'mixed' if spearman is not None
            else 'insufficient_data'
        ),
        'n_bytes_analyzed': n,
        'per_byte': correlation_data,
    }

    # Save
    corr_path = os.path.join(output_dir, f'correlation_epoch_{epoch:03d}.json')
    with open(corr_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"  [Layer 3] Epoch {epoch}: Spearman r={spearman:.4f} ({result['interpretation']}) "
          f"| {n} bytes | Saved: {corr_path}")

    model.train()
    return result


def _rank(values):
    """Assign ranks to values (average rank for ties)."""
    indexed = sorted(enumerate(values), key=lambda x: -x[1])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(indexed):
        j = i
        while j < len(indexed) and indexed[j][1] == indexed[i][1]:
            j += 1
        avg_rank = (i + j - 1) / 2.0 + 1
        for k in range(i, j):
            ranks[indexed[k][0]] = avg_rank
        i = j
    return ranks


# ============================================================
# LR SCHEDULE
# ============================================================

def get_lr(step, warmup, max_lr, total):
    if step < warmup:
        return max_lr * (step + 1) / warmup
    return max_lr * 0.5 * (1.0 + math.cos(math.pi * (step - warmup) / max(1, total - warmup)))


# ============================================================
# MAIN TRAINING LOOP
# ============================================================

def train():
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    data_path = os.path.join(SCRIPT_DIR, DATA_FILE)

    # Setup logging
    log_path = os.path.join(LOG_DIR, f'training_{PARAMS_LABEL}.log')
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(message)s',
        handlers=[
            logging.FileHandler(log_path, encoding='utf-8', mode='w'),
            logging.StreamHandler(sys.stdout),
        ]
    )
    logger = logging.getLogger(f'beta_{CONFIG_NUM}')

    logger.info("=" * 60)
    logger.info(f"EXPERIMENT BETA — Config {CONFIG_NUM} ({PARAMS_LABEL})")
    logger.info(f"d={D_MODEL} L={N_LAYERS} h={N_HEADS} ff={D_FF}")
    logger.info(f"Device: {device}")
    logger.info("=" * 60)

    # Load byte table
    table = load_byte_table(TABLE_FILE)
    logger.info(f"Loaded byte table: {len(table)} entries from {TABLE_FILE}")

    # ---- LAYER 1: Training data statistics ----
    byte_freq = run_layer1(data_path, table, LAYER1_DIR)

    # ---- Dataset ----
    dataset = ByteDataset(data_path, seq_len=SEQ_LEN)
    train_size = int(0.95 * len(dataset))
    eval_size = len(dataset) - train_size
    train_ds, eval_ds = torch.utils.data.random_split(
        dataset, [train_size, eval_size],
        generator=torch.Generator().manual_seed(42)
    )

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True,
                              drop_last=True, num_workers=NUM_WORKERS, pin_memory=(device == "cuda"), persistent_workers=(NUM_WORKERS > 0))
    eval_loader = DataLoader(eval_ds, batch_size=BATCH_SIZE, shuffle=False,
                             num_workers=NUM_WORKERS, pin_memory=(device == "cuda"), persistent_workers=(NUM_WORKERS > 0))

    # ---- Model ----
    model = BetaModel().to(device)
    if USE_BF16:
        model = model.to(torch.bfloat16)
        logger.info("bfloat16 enabled")
    logger.info(f"Parameters: {model.count_parameters():,}")
    logger.info(f"Train: {len(train_ds):,} | Eval: {len(eval_ds):,} | Batches/epoch: {len(train_loader):,}")

    optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=0.01, betas=(0.9, 0.95))

    # ---- Fixed reference sentence for Layer 2 ----
    ref_sentence = get_fixed_reference_sentence(data_path)
    ref_labels = label_byte_sequence(ref_sentence, table)
    ref_decoded = ' '.join(l for _, _, l, _ in ref_labels)
    logger.info(f"Reference sentence ({len(ref_sentence)} bytes): {ref_decoded}")

    # Save reference sentence info
    with open(os.path.join(LAYER2_DIR, 'reference_sentence.json'), 'w', encoding='utf-8') as f:
        json.dump({
            'bytes_hex': [f'0x{b:02x}' for b in ref_sentence],
            'decoded': ref_decoded,
            'length': len(ref_sentence),
        }, f, indent=2, ensure_ascii=False)

    # ---- Layer 2 snapshot at epoch 0 (untrained model) ----
    run_layer2(model, ref_sentence, table, 0, LAYER2_DIR, device)
    run_layer3(model, byte_freq, ref_sentence, table, 0, LAYER3_DIR, device)

    # ---- Training ----
    best_eval = float('inf')
    epochs_without_improvement = 0
    start = time.time()
    training_log = []  # JSONL metrics

    for epoch in range(1, MAX_EPOCHS + 1):
        model.train()
        epoch_loss = 0.0
        steps_in_epoch = 0
        total_steps = len(train_loader) * MAX_EPOCHS
        global_step = (epoch - 1) * len(train_loader)

        for x, y in train_loader:
            x, y = x.to(device), y.to(device)
            lr = get_lr(global_step, WARMUP, LR, total_steps)
            for pg in optimizer.param_groups:
                pg['lr'] = lr

            with torch.amp.autocast('cuda', dtype=torch.bfloat16, enabled=USE_BF16):
                logits, loss = model(x, y)
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()

            epoch_loss += loss.item()
            steps_in_epoch += 1
            global_step += 1

            if global_step % 200 == 0:
                logger.info(f"Epoch {epoch} | Step {global_step:,} | "
                           f"Loss: {loss.item():.4f} | LR: {lr:.2e}")

        avg_train = epoch_loss / steps_in_epoch

        # ---- Eval ----
        model.eval()
        eval_loss = 0.0
        eval_batches = 0
        with torch.no_grad(), torch.amp.autocast('cuda', dtype=torch.bfloat16, enabled=USE_BF16):
            for ex, ey in eval_loader:
                ex, ey = ex.to(device), ey.to(device)
                _, eloss = model(ex, ey)
                eval_loss += eloss.item()
                eval_batches += 1

        avg_eval = eval_loss / max(1, eval_batches)
        ppl = math.exp(min(avg_eval, 20))
        elapsed = (time.time() - start) / 60

        logger.info(f"Epoch {epoch} | Train: {avg_train:.4f} | Eval: {avg_eval:.4f} | "
                   f"PPL: {ppl:.2f} | Time: {elapsed:.1f}m")

        # Log metrics
        step_log = {
            'epoch': epoch,
            'train_loss': round(avg_train, 6),
            'eval_loss': round(avg_eval, 6),
            'perplexity': round(ppl, 4),
            'lr': lr,
            'elapsed_min': round(elapsed, 2),
        }
        training_log.append(step_log)

        # ---- Layer 2: Neural recorder snapshot ----
        l2_result = run_layer2(model, ref_sentence, table, epoch, LAYER2_DIR, device)

        # ---- Layer 3: Frequency-to-weight correlation ----
        l3_result = run_layer3(model, byte_freq, ref_sentence, table, epoch, LAYER3_DIR, device)

        # Add layer results to log
        if l2_result:
            step_log['layer2_accuracy'] = l2_result['accuracy']
        if l3_result:
            step_log['layer3_spearman'] = l3_result.get('spearman_correlation')

        # ---- Checkpoint ----
        if avg_eval < best_eval:
            best_eval = avg_eval
            epochs_without_improvement = 0
            torch.save({
                'model_state_dict': model.state_dict(),
                'config_num': CONFIG_NUM,
                'epoch': epoch,
                'eval_loss': avg_eval,
                'perplexity': ppl,
                'params': model.count_parameters(),
            }, os.path.join(CHECKPOINT_DIR, 'best.pt'))
            logger.info(f"  NEW BEST — saved")
        else:
            epochs_without_improvement += 1
            logger.info(f"  No improvement ({epochs_without_improvement}/{PATIENCE})")

        if epochs_without_improvement >= PATIENCE:
            logger.info(f"  EARLY STOP — loss flattened after {epoch} epochs")
            break

    # ---- Save training log ----
    log_jsonl_path = os.path.join(LOG_DIR, f'training_metrics_{PARAMS_LABEL}.jsonl')
    with open(log_jsonl_path, 'w', encoding='utf-8') as f:
        for entry in training_log:
            f.write(json.dumps(entry) + '\n')

    # ---- Final summary ----
    total_time = (time.time() - start) / 60
    best_ppl = math.exp(min(best_eval, 20))

    summary = {
        'config_num': CONFIG_NUM,
        'params_label': PARAMS_LABEL,
        'params': model.count_parameters(),
        'd_model': D_MODEL,
        'n_layers': N_LAYERS,
        'n_heads': N_HEADS,
        'd_ff': D_FF,
        'best_eval_loss': round(best_eval, 6),
        'best_perplexity': round(best_ppl, 4),
        'epochs_trained': epoch,
        'total_time_minutes': round(total_time, 2),
        'device': device,
    }

    summary_path = os.path.join(SCRIPT_DIR, f'results_{PARAMS_LABEL}.json')
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)

    logger.info("")
    logger.info("=" * 60)
    logger.info(f"Config {CONFIG_NUM} ({PARAMS_LABEL}) COMPLETE")
    logger.info(f"Best eval loss: {best_eval:.4f} | Best PPL: {best_ppl:.2f}")
    logger.info(f"Total time: {total_time:.1f}m | Epochs: {epoch}")
    logger.info("=" * 60)


if __name__ == '__main__':
    train()
