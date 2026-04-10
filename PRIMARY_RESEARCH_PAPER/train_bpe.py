"""
Matched Comparison — BPE Baseline Model (7.18M)
================================================
Same architecture, same Esperanto sentences, BPE tokenization.
Vocab: 2000 (SentencePiece BPE tokens)
d_model=384, n_layers=3, n_heads=8, d_ff=1344 (adjusted to match param count)

Self-contained: model + training + logging. No external model imports.

Author: Travis Edward Holley
Architecture: Claude (Anthropic)
"""

import sys
import os
import time
import math
import json
import struct
import logging
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader

sys.stdout.reconfigure(encoding='utf-8')

# ============================================================
# CONFIG
# ============================================================
VOCAB_SIZE = 2000
D_MODEL = 384
N_LAYERS = 3
N_HEADS = 8
D_FF = 1344  # adjusted down from 1536 to match ~7.18M total params with larger embedding
SEQ_LEN = 512
BATCH_SIZE = 256
MAX_EPOCHS = 10
PATIENCE = 3
LR = 3e-4
WARMUP = 1000
USE_BF16 = True
NUM_WORKERS = 4

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(SCRIPT_DIR, 'bpe_training.bin')
CHECKPOINT_DIR = os.path.join(SCRIPT_DIR, 'bpe_checkpoints')
LOG_DIR = os.path.join(SCRIPT_DIR, 'bpe_logs')
RESULTS_FILE = os.path.join(SCRIPT_DIR, 'results_bpe.json')

for d in [CHECKPOINT_DIR, LOG_DIR]:
    os.makedirs(d, exist_ok=True)

DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'

# BPE EOS token (SentencePiece default: 1 = <s>/BOS, 2 = </s>/EOS)
# In build_matched_data.py we wrote EOS as token ID 1, matching SentencePiece convention
EOS_TOKEN = 1

# ============================================================
# MODEL — 7.18M BPE Baseline (vocab=2000, d_ff=1344)
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
    def forward(self, x, cos, sin, mask):
        B, T, C = x.shape
        q = self.wq(x).view(B, T, self.n_heads, self.head_dim).transpose(1, 2)
        k = self.wk(x).view(B, T, self.n_heads, self.head_dim).transpose(1, 2)
        v = self.wv(x).view(B, T, self.n_heads, self.head_dim).transpose(1, 2)
        q, k = apply_rotary(q, k, cos[:T], sin[:T])
        att = (q @ k.transpose(-2, -1)) * (self.head_dim ** -0.5)
        att = att.masked_fill(mask[:, :, :T, :T] == 0, float('-inf'))
        att = F.softmax(att, dim=-1)
        return self.wo((att @ v).transpose(1, 2).contiguous().view(B, T, C))

class Block(nn.Module):
    def __init__(self, d, h, ff):
        super().__init__()
        self.attn = Attention(d, h)
        self.ffn = SwiGLU(d, ff)
        self.n1 = RMSNorm(d)
        self.n2 = RMSNorm(d)
    def forward(self, x, cos, sin, mask):
        x = x + self.attn(self.n1(x), cos, sin, mask)
        x = x + self.ffn(self.n2(x))
        return x

class BPEModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.vocab_size = VOCAB_SIZE
        self.d_model = D_MODEL
        self.n_layers = N_LAYERS
        self.n_heads = N_HEADS
        self.d_ff = D_FF

        self.embed = nn.Embedding(VOCAB_SIZE, D_MODEL)
        self.rotary = RotaryEmbedding(D_MODEL // N_HEADS)
        self.layers = nn.ModuleList([Block(D_MODEL, N_HEADS, D_FF) for _ in range(N_LAYERS)])
        self.norm = RMSNorm(D_MODEL)
        self.output = nn.Linear(D_MODEL, VOCAB_SIZE, bias=False)
        self.output.weight = self.embed.weight  # tied embeddings
        mask = torch.tril(torch.ones(SEQ_LEN, SEQ_LEN))
        self.register_buffer('mask', mask.unsqueeze(0).unsqueeze(0))
        self._init()

    def _init(self):
        for m in self.modules():
            if isinstance(m, nn.Linear): nn.init.normal_(m.weight, std=0.02)
            elif isinstance(m, nn.Embedding): nn.init.normal_(m.weight, std=0.02)

    def forward(self, idx, targets=None):
        B, T = idx.shape
        x = self.embed(idx)
        cos, sin = self.rotary(T, idx.device)
        for layer in self.layers:
            x = layer(x, cos, sin, self.mask)
        logits = self.output(self.norm(x))
        loss = None
        if targets is not None:
            loss = F.cross_entropy(logits.view(-1, VOCAB_SIZE), targets.view(-1), ignore_index=-1)
        return logits, loss

    def count_parameters(self):
        return sum(p.numel() for p in self.parameters() if p.requires_grad)

# ============================================================
# DATASET — BPE token chains (16-bit IDs, split on EOS)
# ============================================================

class BPEChainDataset(Dataset):
    def __init__(self, bin_path, seq_len=512):
        self.seq_len = seq_len

        # Read 16-bit token IDs
        with open(bin_path, 'rb') as f:
            raw = f.read()

        num_tokens = len(raw) // 2
        all_ids = []
        for i in range(num_tokens):
            token_id = struct.unpack_from('<H', raw, i * 2)[0]
            all_ids.append(token_id)

        # Split on EOS token into chains
        self.chains = []
        current = []
        for tid in all_ids:
            current.append(tid)
            if tid == EOS_TOKEN:
                if len(current) >= 3:
                    self.chains.append(current)
                current = []

    def __len__(self):
        return len(self.chains)

    def __getitem__(self, idx):
        chain = self.chains[idx]
        if len(chain) > self.seq_len + 1:
            chain = chain[:self.seq_len + 1]
        data = torch.tensor(chain, dtype=torch.long)
        if len(data) < self.seq_len + 1:
            pad = torch.full((self.seq_len + 1 - len(data),), -1, dtype=torch.long)
            data = torch.cat([data, pad])
        x = data[:-1].clamp(min=0)
        y = data[1:]
        return x, y

# ============================================================
# TRAINING
# ============================================================

def get_lr(step, warmup, max_lr, total):
    if step < warmup:
        return max_lr * (step + 1) / warmup
    return max_lr * 0.5 * (1.0 + math.cos(math.pi * (step - warmup) / max(1, total - warmup)))

def train():
    log_file = os.path.join(LOG_DIR, 'training_bpe.log')
    logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(message)s',
        handlers=[logging.FileHandler(log_file, encoding='utf-8', mode='w'),
                  logging.StreamHandler(sys.stdout)])
    logger = logging.getLogger('bpe')

    logger.info("=" * 60)
    logger.info("MATCHED COMPARISON — BPE Baseline Model")
    logger.info(f"Vocab: {VOCAB_SIZE} | d={D_MODEL} L={N_LAYERS} h={N_HEADS} ff={D_FF}")
    logger.info("=" * 60)
    logger.info(f"Device: {DEVICE}")

    dataset = BPEChainDataset(DATA_FILE, SEQ_LEN)
    train_size = int(0.95 * len(dataset))
    eval_size = len(dataset) - train_size
    train_ds, eval_ds = torch.utils.data.random_split(
        dataset, [train_size, eval_size],
        generator=torch.Generator().manual_seed(42)
    )

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True,
        drop_last=True, num_workers=NUM_WORKERS, pin_memory=True)
    eval_loader = DataLoader(eval_ds, batch_size=BATCH_SIZE, shuffle=False,
        num_workers=NUM_WORKERS, pin_memory=True)

    model = BPEModel().to(DEVICE)
    param_count = model.count_parameters()
    logger.info(f"Parameters: {param_count:,}")
    logger.info(f"Training chains: {len(dataset):,}")
    logger.info(f"Train: {len(train_ds):,} | Eval: {len(eval_ds):,}")
    logger.info(f"Batches/epoch: {len(train_loader):,}")
    logger.info(f"Hyperparams: batch={BATCH_SIZE} seq={SEQ_LEN} lr={LR} warmup={WARMUP}")
    logger.info(f"BF16: {USE_BF16}")
    logger.info("")

    optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=0.01, betas=(0.9, 0.95))
    scaler = torch.amp.GradScaler('cuda', enabled=USE_BF16)

    best_eval = float('inf')
    epochs_no_improve = 0
    results = []
    start = time.time()

    for epoch in range(1, MAX_EPOCHS + 1):
        model.train()
        epoch_loss = 0.0
        steps = 0
        total_steps = len(train_loader) * MAX_EPOCHS
        global_step = (epoch - 1) * len(train_loader)

        for x, y in train_loader:
            x, y = x.to(DEVICE), y.to(DEVICE)
            lr = get_lr(global_step + steps, WARMUP, LR, total_steps)
            for pg in optimizer.param_groups:
                pg['lr'] = lr

            with torch.amp.autocast('cuda', dtype=torch.bfloat16, enabled=USE_BF16):
                _, loss = model(x, y)

            optimizer.zero_grad()
            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            scaler.step(optimizer)
            scaler.update()

            epoch_loss += loss.item()
            steps += 1

        avg_train = epoch_loss / steps

        # Eval
        model.eval()
        eval_loss = 0.0
        eval_steps = 0
        with torch.no_grad():
            for x, y in eval_loader:
                x, y = x.to(DEVICE), y.to(DEVICE)
                with torch.amp.autocast('cuda', dtype=torch.bfloat16, enabled=USE_BF16):
                    _, loss = model(x, y)
                eval_loss += loss.item()
                eval_steps += 1

        avg_eval = eval_loss / eval_steps
        ppl = math.exp(avg_eval)
        elapsed = time.time() - start

        logger.info(f"Epoch {epoch:2d} | Train: {avg_train:.4f} | Eval: {avg_eval:.4f} | PPL: {ppl:.2f} | Time: {elapsed:.0f}s")

        results.append({
            'epoch': epoch,
            'train_loss': round(avg_train, 6),
            'eval_loss': round(avg_eval, 6),
            'perplexity': round(ppl, 4),
            'elapsed': round(elapsed, 1),
        })

        # Save best
        if avg_eval < best_eval:
            best_eval = avg_eval
            epochs_no_improve = 0
            torch.save(model.state_dict(), os.path.join(CHECKPOINT_DIR, 'best.pt'))
            logger.info(f"  -> New best! Saved checkpoint.")
        else:
            epochs_no_improve += 1
            if epochs_no_improve >= PATIENCE:
                logger.info(f"  -> Early stopping (no improvement for {PATIENCE} epochs)")
                break

    # Save results
    final = {
        'model': 'bpe_baseline',
        'vocab_size': VOCAB_SIZE,
        'd_model': D_MODEL,
        'n_layers': N_LAYERS,
        'n_heads': N_HEADS,
        'd_ff': D_FF,
        'parameters': param_count,
        'best_eval_loss': round(best_eval, 6),
        'best_ppl': round(math.exp(best_eval), 4),
        'epochs_trained': len(results),
        'training_sentences': len(dataset),
        'results': results,
    }
    with open(RESULTS_FILE, 'w') as f:
        json.dump(final, f, indent=2)

    logger.info("")
    logger.info("=" * 60)
    logger.info(f"BPE BASELINE — FINAL RESULTS")
    logger.info(f"Parameters: {param_count:,}")
    logger.info(f"Best eval loss: {best_eval:.6f}")
    logger.info(f"Best perplexity: {math.exp(best_eval):.4f}")
    logger.info(f"Epochs: {len(results)}")
    logger.info(f"Total time: {time.time()-start:.0f}s")
    logger.info("=" * 60)

if __name__ == '__main__':
    train()
