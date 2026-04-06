"""
LidiaZ (The Translator) — Training Script
Ludwik Zamenhof Method

Trains on parallel Esperanto-English data.
Format: [Esperanto bytes] [Q/A] [English bytes] [SPACE] [.] [END]

The model learns: given Esperanto bytes, predict the English bytes after Q/A.

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

from lidiaz_model_7m import LidiaZ7MModel as LidiaZModel

# ============================================================
# CONFIG
# ============================================================

BASE_DIR = os.path.dirname(__file__)
TRAINING_BIN = os.path.join(BASE_DIR, 'lidiaz_training_esperanto_only.bin')
CHECKPOINT_DIR = os.path.join(BASE_DIR, 'esperanto_only_checkpoints')
LOG_FILE = os.path.join(BASE_DIR, 'esperanto_only_training.log')

# Control bytes
END = 0x00
QA = 0x05

# Hyperparameters
BATCH_SIZE = 64
SEQ_LEN = 512
LEARNING_RATE = 3e-4
WEIGHT_DECAY = 0.01
EPOCHS = 3
WARMUP_STEPS = 1000
EVAL_INTERVAL = 1000
SAVE_INTERVAL = 5000
GRAD_CLIP = 1.0

DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'


# ============================================================
# DATASET
# ============================================================

class ParallelDataset(Dataset):
    """Dataset of parallel Esperanto-English chains.

    Each chain: [ESP bytes] [Q/A] [ENG bytes] [SPACE] [.] [END]
    Split on END byte.
    """

    def __init__(self, bin_path, seq_len):
        self.seq_len = seq_len

        with open(bin_path, 'rb') as f:
            data = f.read()

        self.chains = []
        current = bytearray()
        for b in data:
            current.append(b)
            if b == END:
                chain = bytes(current)
                if len(chain) >= 6:  # minimum: 2 ESP + QA + 2 ENG + END
                    self.chains.append(chain)
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

        x = data[:-1]
        y = data[1:]

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
    logger.info("LidiaZ 7M — Esperanto Only — Ludwik Zamenhof Method")
    logger.info("=" * 60)
    logger.info(f"Device: {DEVICE}")

    os.makedirs(CHECKPOINT_DIR, exist_ok=True)

    # Load data
    logger.info(f"Loading parallel training data: {TRAINING_BIN}")
    logger.info(f"  Size: {os.path.getsize(TRAINING_BIN)/1e6:.1f}MB")

    dataset = ParallelDataset(TRAINING_BIN, SEQ_LEN)
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

    # Model
    model = LidiaZModel().to(DEVICE)
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

            lr = get_lr(global_step, WARMUP_STEPS, LEARNING_RATE, total_steps)
            for param_group in optimizer.param_groups:
                param_group['lr'] = lr

            logits, loss = model(x, y)

            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), GRAD_CLIP)
            optimizer.step()

            epoch_loss += loss.item()
            epoch_tokens += (y != -1).sum().item()
            global_step += 1

            if global_step % 100 == 0:
                elapsed = time.time() - start_time
                tokens_per_sec = epoch_tokens / elapsed if elapsed > 0 else 0
                logger.info(
                    f"Epoch {epoch}/{EPOCHS} | Step {global_step:,} | "
                    f"Loss: {loss.item():.4f} | LR: {lr:.2e} | "
                    f"Tok/s: {tokens_per_sec:.0f}"
                )

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
                    }, os.path.join(CHECKPOINT_DIR, 'lidiaz_best.pt'))
                    logger.info(f"  NEW BEST — saved checkpoint")

                model.train()

            if global_step % SAVE_INTERVAL == 0:
                torch.save({
                    'model_state_dict': model.state_dict(),
                    'optimizer_state_dict': optimizer.state_dict(),
                    'epoch': epoch,
                    'step': global_step,
                }, os.path.join(CHECKPOINT_DIR, f'lidiaz_step_{global_step}.pt'))

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
    }, os.path.join(CHECKPOINT_DIR, 'lidiaz_final.pt'))

    total_time = time.time() - start_time
    logger.info("")
    logger.info("=" * 60)
    logger.info(f"Training complete in {total_time/60:.1f} minutes")
    logger.info(f"Best eval loss: {best_eval_loss:.4f}")
    logger.info(f"Best perplexity: {math.exp(min(best_eval_loss, 20)):.2f}")
    logger.info("=" * 60)


if __name__ == '__main__':
    train()
