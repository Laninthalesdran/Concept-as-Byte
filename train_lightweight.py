"""
Train Strawweight — Phase 1 Reasoning Engine

Trains the 10.7M parameter Strawweight model on Phase 1 training data.
Uses byte-level input — each byte in the training data is a token (0-255).

Usage:
  python train_strawweight.py                     # train with defaults
  python train_strawweight.py --epochs 20         # more epochs
  python train_strawweight.py --batch_size 64     # adjust batch size
  python train_strawweight.py --resume checkpoint.pt  # resume from checkpoint

Author: Travis Holley / Claude
Date: March 31, 2026
"""

import os
import time
import math
import argparse
import torch
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from strawweight import Strawweight


# ============================================================
# DATASET
# ============================================================

class ByteDataset(Dataset):
    """
    Reads a text file as raw bytes. Each byte is a token (0-255).
    Returns chunks of seq_len+1 bytes — input is [:seq_len], target is [1:seq_len+1].
    """
    def __init__(self, file_path, seq_len=512):
        self.seq_len = seq_len
        import numpy as np
        raw = np.fromfile(file_path, dtype=np.uint8)
        self.data = torch.from_numpy(raw.astype(np.int64))
        # Number of complete sequences we can extract
        self.n_sequences = (len(self.data) - 1) // seq_len

    def __len__(self):
        return self.n_sequences

    def __getitem__(self, idx):
        start = idx * self.seq_len
        chunk = self.data[start:start + self.seq_len + 1]
        x = chunk[:-1]
        y = chunk[1:]
        return x, y


# ============================================================
# LEARNING RATE SCHEDULE
# ============================================================

def get_lr(step, warmup_steps, max_steps, max_lr, min_lr):
    """Cosine decay with linear warmup."""
    if step < warmup_steps:
        return max_lr * (step + 1) / warmup_steps
    if step >= max_steps:
        return min_lr
    decay_ratio = (step - warmup_steps) / (max_steps - warmup_steps)
    coeff = 0.5 * (1.0 + math.cos(math.pi * decay_ratio))
    return min_lr + coeff * (max_lr - min_lr)


# ============================================================
# TRAINING LOOP
# ============================================================

def train(args):
    # Device
    if torch.cuda.is_available():
        device = torch.device("cuda")
        print(f"Using GPU: {torch.cuda.get_device_name(0)}")
        print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
    else:
        device = torch.device("cpu")
        print("Using CPU")

    # Model
    model = Strawweight(
        vocab_size=256,
        d_model=320,
        n_heads=8,
        n_layers=8,
        d_ff=1280,
        max_seq_len=args.seq_len,
    ).to(device)

    total_params = model.count_parameters()
    print(f"Model: {total_params:,} parameters ({total_params/1e6:.1f}M)")

    # Resume from checkpoint
    start_epoch = 0
    if args.resume and os.path.exists(args.resume):
        checkpoint = torch.load(args.resume, map_location=device)
        model.load_state_dict(checkpoint['model'])
        start_epoch = checkpoint.get('epoch', 0) + 1
        print(f"Resumed from {args.resume} (epoch {start_epoch})")

    # Dataset
    print(f"Loading data from {args.data}...")
    dataset = ByteDataset(args.data, seq_len=args.seq_len)
    dataloader = DataLoader(
        dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=2,
        pin_memory=True if device.type == 'cuda' else False,
    )

    total_tokens = len(dataset.data)
    print(f"Dataset: {total_tokens:,} bytes ({total_tokens/1024/1024:.1f} MB)")
    print(f"Sequences: {len(dataset):,} (seq_len={args.seq_len})")
    print(f"Batches per epoch: {len(dataloader):,}")

    # Optimizer
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=args.lr,
        betas=(0.9, 0.95),
        weight_decay=0.1,
    )

    # Training
    max_steps = args.epochs * len(dataloader)
    warmup_steps = min(100, max_steps // 10)
    global_step = start_epoch * len(dataloader)

    print(f"\nTraining for {args.epochs} epochs ({max_steps:,} steps)")
    print(f"Warmup: {warmup_steps} steps")
    print(f"LR: {args.lr} -> {args.lr * 0.1} (cosine decay)")
    print(f"Batch size: {args.batch_size}")
    print("=" * 60)

    best_loss = float('inf')

    for epoch in range(start_epoch, args.epochs):
        model.train()
        epoch_loss = 0.0
        epoch_tokens = 0
        t0 = time.time()

        for batch_idx, (x, y) in enumerate(dataloader):
            x, y = x.to(device), y.to(device)

            # LR schedule
            lr = get_lr(global_step, warmup_steps, max_steps, args.lr, args.lr * 0.1)
            for param_group in optimizer.param_groups:
                param_group['lr'] = lr

            # Forward
            logits, loss = model(x, y)

            # Backward
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()

            epoch_loss += loss.item() * x.size(0)
            epoch_tokens += x.numel()
            global_step += 1

            # Progress every 50 batches
            if (batch_idx + 1) % 50 == 0:
                avg = epoch_loss / (batch_idx + 1) / args.batch_size
                elapsed = time.time() - t0
                tok_per_sec = epoch_tokens / elapsed
                print(f"  epoch {epoch+1} | batch {batch_idx+1}/{len(dataloader)} | "
                      f"loss {avg:.4f} | lr {lr:.2e} | "
                      f"{tok_per_sec:.0f} tok/s")

        # Epoch stats
        avg_loss = epoch_loss / len(dataset)
        elapsed = time.time() - t0
        tok_per_sec = epoch_tokens / elapsed

        print(f"Epoch {epoch+1}/{args.epochs} | "
              f"loss {avg_loss:.4f} | "
              f"ppl {math.exp(avg_loss):.2f} | "
              f"lr {lr:.2e} | "
              f"{elapsed:.1f}s | "
              f"{tok_per_sec:.0f} tok/s")

        # Save checkpoint
        checkpoint = {
            'model': model.state_dict(),
            'epoch': epoch,
            'loss': avg_loss,
            'args': vars(args),
        }

        # Save latest
        torch.save(checkpoint, os.path.join(args.output_dir, 'strawweight_latest.pt'))

        # Save best
        if avg_loss < best_loss:
            best_loss = avg_loss
            torch.save(checkpoint, os.path.join(args.output_dir, 'strawweight_best.pt'))
            print(f"  New best: {avg_loss:.4f}")

        # Save every N epochs
        if (epoch + 1) % args.save_every == 0:
            path = os.path.join(args.output_dir, f'strawweight_epoch{epoch+1}.pt')
            torch.save(checkpoint, path)

    print("=" * 60)
    print(f"Training complete. Best loss: {best_loss:.4f} (ppl {math.exp(best_loss):.2f})")
    print(f"Checkpoints saved to {args.output_dir}/")

    # Quick generation test — feed a few bytes from the training data
    print("\n--- Generation test ---")
    model.eval()
    with open(args.data, 'rb') as f:
        seed_bytes = f.read(10)
    prompt = torch.tensor([list(seed_bytes)], dtype=torch.long, device=device)
    generated = model.generate(prompt, max_new_tokens=100, temperature=0.8, top_k=40)
    output_bytes = bytes(generated[0].cpu().tolist())
    print(f"Prompt bytes: {[f'0x{b:02X}' for b in seed_bytes]}")
    print(f"Output bytes: {[f'0x{b:02X}' for b in output_bytes[:50]]}...")
    # Decode with JalekCore if available
    try:
        from jalekcore import JalekCore
        core = JalekCore()
        decoded = core.decode(output_bytes)
        print(f"Decoded: {decoded[:200]}")
    except Exception:
        print("(JalekCore decode not available for preview)")


def main():
    parser = argparse.ArgumentParser(description="Train Strawweight")
    parser.add_argument("--data", type=str, default="phase1_encoded.bin",
                       help="Path to training data file (binary encoded)")
    parser.add_argument("--epochs", type=int, default=10,
                       help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=32,
                       help="Batch size")
    parser.add_argument("--seq_len", type=int, default=512,
                       help="Sequence length")
    parser.add_argument("--lr", type=float, default=3e-4,
                       help="Peak learning rate")
    parser.add_argument("--output_dir", type=str, default="checkpoints",
                       help="Directory for saving checkpoints")
    parser.add_argument("--save_every", type=int, default=5,
                       help="Save checkpoint every N epochs")
    parser.add_argument("--resume", type=str, default=None,
                       help="Path to checkpoint to resume from")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    train(args)


if __name__ == "__main__":
    main()
