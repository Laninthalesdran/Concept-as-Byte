"""
LLZ (The Zamenhof) — Training Script

PPT: Positive Preference Training only. No punishment signals.
Trains on English text encoded through the LLZ English table.
The LLZ learns English word sequencing in byte space.

Training data: 144MB Chinchilla-optimal corpus (Tatoeba + C4 + Gutenberg)
Model: 7.18M params (d=384, h=8, L=3, ff=1536)

Author: Travis Edward Holley
Trainer: Claude (Anthropic)
"""

import sys
import os
import time
import math
import logging
import torch
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader

sys.stdout.reconfigure(encoding='utf-8')

from llz_model import LLZModel
from llz_encoder import LLZEncoder, END, SPACE, NEWLINE

# ============================================================
# CONFIG
# ============================================================

BASE_DIR = os.path.dirname(__file__)
TRAINING_TEXT = os.path.join(BASE_DIR, 'llz_training_corpora', 'llz_training_144mb.txt')
TRAINING_BIN = os.path.join(BASE_DIR, 'llz_training_encoded.bin')
CHECKPOINT_DIR = os.path.join(BASE_DIR, 'llz_checkpoints')
LOG_FILE = os.path.join(BASE_DIR, 'llz_training.log')

# Hyperparameters
BATCH_SIZE = 64
SEQ_LEN = 512          # Match model max_seq_len
LEARNING_RATE = 3e-4
WEIGHT_DECAY = 0.01
EPOCHS = 10
WARMUP_STEPS = 1000
EVAL_INTERVAL = 1000
SAVE_INTERVAL = 5000
GRAD_CLIP = 1.0

DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'


# ============================================================
# PRE-ENCODE
# ============================================================

def pre_encode(text_path, bin_path):
    """Encode plain English text to LLZ byte stream.

    Each sentence becomes: [encoded bytes] END
    Writes a single binary file for fast training.
    """
    encoder = LLZEncoder()

    print(f"Pre-encoding {text_path}...", flush=True)
    t0 = time.time()

    total_sentences = 0
    total_bytes = 0

    with open(text_path, 'r', encoding='utf-8') as fin, \
         open(bin_path, 'wb') as fout:

        for line in fin:
            line = line.strip()
            if not line:
                continue

            encoded = encoder.encode(line)
            if len(encoded) < 2:
                continue

            # Write encoded bytes + END
            fout.write(encoded)
            fout.write(bytes([END]))

            total_sentences += 1
            total_bytes += len(encoded) + 1

            if total_sentences % 500000 == 0:
                elapsed = time.time() - t0
                print(f"  {total_sentences:,} sentences, {total_bytes/1e6:.1f}MB, {elapsed:.0f}s",
                      flush=True)

    elapsed = time.time() - t0
    print(f"Done: {total_sentences:,} sentences, {total_bytes/1e6:.1f}MB in {elapsed:.0f}s")
    return total_sentences, total_bytes


# ============================================================
# DATASET
# ============================================================

class LLZDataset(Dataset):
    """Dataset of LLZ-encoded English byte sequences.

    Loads pre-encoded binary and splits on END byte.
    Each chain is one encoded sentence.
    """

    def __init__(self, bin_path, seq_len):
        self.seq_len = seq_len

        with open(bin_path, 'rb') as f:
            data = f.read()

        # Split on END byte into chains
        self.chains = []
        current = bytearray()
        for b in data:
            current.append(b)
            if b == END:
                chain = bytes(current)
                if len(chain) >= 4:  # minimum viable chain
                    self.chains.append(chain)
                current = bytearray()

    def __len__(self):
        return len(self.chains)

    def __getitem__(self, idx):
        chain = self.chains[idx]

        # Truncate to seq_len + 1 (need input + target)
        if len(chain) > self.seq_len + 1:
            chain = chain[:self.seq_len + 1]

        data = torch.tensor(list(chain), dtype=torch.long)

        # Pad if needed
        if len(data) < self.seq_len + 1:
            pad = torch.full((self.seq_len + 1 - len(data),), -1, dtype=torch.long)
            data = torch.cat([data, pad])

        x = data[:-1]   # input
        y = data[1:]     # target (shifted by 1)

        # Replace -1 padding in x with 0 (masked in loss via ignore_index=-1)
        x = x.clamp(min=0)

        return x, y


# ============================================================
# TRAINING
# ============================================================

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE, encoding='utf-8', mode='a'),
            logging.StreamHandler(sys.stdout),
        ]
    )
    return logging.getLogger(__name__)


def get_lr(step, warmup_steps, max_lr, total_steps):
    """Linear warmup then cosine decay."""
    if step < warmup_steps:
        return max_lr * (step + 1) / warmup_steps
    progress = (step - warmup_steps) / max(1, total_steps - warmup_steps)
    return max_lr * 0.5 * (1.0 + math.cos(math.pi * progress))


def train():
    logger = setup_logging()
    logger.info("=" * 60)
    logger.info("LLZ (The Zamenhof) — Training")
    logger.info("=" * 60)
    logger.info(f"Device: {DEVICE}")

    os.makedirs(CHECKPOINT_DIR, exist_ok=True)

    # Pre-encode if binary doesn't exist or is older than text
    if not os.path.exists(TRAINING_BIN) or \
       os.path.getmtime(TRAINING_TEXT) > os.path.getmtime(TRAINING_BIN):
        logger.info("Pre-encoding training data...")
        n_sent, n_bytes = pre_encode(TRAINING_TEXT, TRAINING_BIN)
        logger.info(f"Encoded: {n_sent:,} sentences, {n_bytes/1e6:.1f}MB")
    else:
        logger.info(f"Using existing encoded data: {TRAINING_BIN}")
        logger.info(f"  Size: {os.path.getsize(TRAINING_BIN)/1e6:.1f}MB")

    # Load data
    logger.info(f"Loading training chains...")
    dataset = LLZDataset(TRAINING_BIN, SEQ_LEN)
    logger.info(f"Training chains: {len(dataset):,}")

    # Split: 95% train, 5% eval
    train_size = int(0.95 * len(dataset))
    eval_size = len(dataset) - train_size
    train_dataset, eval_dataset = torch.utils.data.random_split(
        dataset, [train_size, eval_size],
        generator=torch.Generator().manual_seed(42)
    )

    train_loader = DataLoader(
        train_dataset, batch_size=BATCH_SIZE, shuffle=True,
        drop_last=True, num_workers=0, pin_memory=(DEVICE == 'cuda')
    )
    eval_loader = DataLoader(
        eval_dataset, batch_size=BATCH_SIZE, shuffle=False,
        num_workers=0, pin_memory=(DEVICE == 'cuda')
    )

    logger.info(f"Train: {len(train_dataset):,} | Eval: {len(eval_dataset):,}")
    logger.info(f"Batches per epoch: {len(train_loader):,}")

    # Model — uses updated defaults (d=384, h=8, L=3, ff=1536)
    model = LLZModel().to(DEVICE)
    logger.info(f"Model parameters: {model.count_parameters():,}")
    logger.info(f"Architecture: {model.n_layers}L, d={model.d_model}, "
                f"{model.n_heads}h, ff={model.d_ff}")

    # Optimizer
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=LEARNING_RATE,
        weight_decay=WEIGHT_DECAY,
        betas=(0.9, 0.95),
    )

    total_steps = len(train_loader) * EPOCHS
    logger.info(f"Total steps: {total_steps:,}")
    logger.info(f"Warmup: {WARMUP_STEPS} steps")
    logger.info(f"Epochs: {EPOCHS}")
    logger.info(f"Batch size: {BATCH_SIZE}")
    logger.info(f"Seq length: {SEQ_LEN}")
    logger.info(f"Learning rate: {LEARNING_RATE}")
    logger.info("")

    # Training loop
    global_step = 0
    best_eval_loss = float('inf')
    start_time = time.time()

    for epoch in range(1, EPOCHS + 1):
        model.train()
        epoch_loss = 0.0
        epoch_tokens = 0

        for batch_idx, (x, y) in enumerate(train_loader):
            x, y = x.to(DEVICE), y.to(DEVICE)

            # Update learning rate
            lr = get_lr(global_step, WARMUP_STEPS, LEARNING_RATE, total_steps)
            for param_group in optimizer.param_groups:
                param_group['lr'] = lr

            # Forward
            logits, loss = model(x, y)

            # Backward
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), GRAD_CLIP)
            optimizer.step()

            epoch_loss += loss.item()
            epoch_tokens += (y != -1).sum().item()
            global_step += 1

            # Log
            if global_step % 100 == 0:
                elapsed = time.time() - start_time
                tokens_per_sec = epoch_tokens / elapsed if elapsed > 0 else 0
                logger.info(
                    f"Epoch {epoch}/{EPOCHS} | Step {global_step:,} | "
                    f"Loss: {loss.item():.4f} | LR: {lr:.2e} | "
                    f"Tok/s: {tokens_per_sec:.0f}"
                )

            # Eval
            if global_step % EVAL_INTERVAL == 0:
                model.eval()
                eval_loss = 0.0
                eval_batches = 0
                with torch.no_grad():
                    for ex, ey in eval_loader:
                        ex, ey = ex.to(DEVICE), ey.to(DEVICE)
                        _, eloss = model(ex, ey)
                        eval_loss += eloss.item()
                        eval_batches += 1
                avg_eval = eval_loss / max(1, eval_batches)
                perplexity = math.exp(min(avg_eval, 20))
                logger.info(
                    f"  EVAL | Loss: {avg_eval:.4f} | Perplexity: {perplexity:.2f}"
                )

                if avg_eval < best_eval_loss:
                    best_eval_loss = avg_eval
                    torch.save({
                        'model_state_dict': model.state_dict(),
                        'optimizer_state_dict': optimizer.state_dict(),
                        'epoch': epoch,
                        'step': global_step,
                        'eval_loss': avg_eval,
                    }, os.path.join(CHECKPOINT_DIR, 'llz_best.pt'))
                    logger.info(f"  NEW BEST — saved checkpoint")

                model.train()

            # Save periodic checkpoint
            if global_step % SAVE_INTERVAL == 0:
                torch.save({
                    'model_state_dict': model.state_dict(),
                    'optimizer_state_dict': optimizer.state_dict(),
                    'epoch': epoch,
                    'step': global_step,
                }, os.path.join(CHECKPOINT_DIR, f'llz_step_{global_step}.pt'))

        # End of epoch
        avg_epoch_loss = epoch_loss / len(train_loader)
        elapsed = time.time() - start_time
        logger.info(
            f"Epoch {epoch} complete | Avg loss: {avg_epoch_loss:.4f} | "
            f"Time: {elapsed/60:.1f}m"
        )

    # Final save
    torch.save({
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'epoch': EPOCHS,
        'step': global_step,
    }, os.path.join(CHECKPOINT_DIR, 'llz_final.pt'))

    total_time = time.time() - start_time
    logger.info("")
    logger.info("=" * 60)
    logger.info(f"Training complete in {total_time/60:.1f} minutes")
    logger.info(f"Best eval loss: {best_eval_loss:.4f}")
    logger.info(f"Best perplexity: {math.exp(min(best_eval_loss, 20)):.2f}")
    logger.info("=" * 60)


if __name__ == '__main__':
    train()
