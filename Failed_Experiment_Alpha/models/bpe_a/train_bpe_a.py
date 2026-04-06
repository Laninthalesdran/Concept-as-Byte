"""BPE Baseline A — English-only, BPE tokenized. 3 epochs. Control model."""
import sys, os, time, math, logging, torch, torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
sys.stdout.reconfigure(encoding='utf-8')
from bpe_baseline_model import BPEBaselineModel

TRAINING_BIN = os.path.join(os.path.dirname(__file__), 'bpe_a_training.bin')
CHECKPOINT_DIR = os.path.join(os.path.dirname(__file__), 'bpe_a_checkpoints')
LOG_FILE = os.path.join(os.path.dirname(__file__), 'bpe_a_training.log')
BATCH_SIZE = 64; SEQ_LEN = 512; LEARNING_RATE = 3e-4; WEIGHT_DECAY = 0.01
EPOCHS = 3; WARMUP_STEPS = 1000; EVAL_INTERVAL = 1000; SAVE_INTERVAL = 5000; GRAD_CLIP = 1.0
DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'

class BPEDataset(Dataset):
    def __init__(self, bin_path, seq_len, vocab_size=2000):
        self.seq_len = seq_len
        with open(bin_path, 'rb') as f:
            data = f.read()
        # 16-bit token IDs, EOS=1
        all_ids = []
        for i in range(0, len(data)-1, 2):
            tid = int.from_bytes(data[i:i+2], 'little')
            all_ids.append(tid)
        # Split on EOS
        self.chains = []
        current = []
        for tid in all_ids:
            current.append(tid)
            if tid == 1:  # EOS
                if len(current) >= 4:
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
        x = data[:-1]; y = data[1:]
        x = x.clamp(min=0)
        return x, y

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(message)s',
        handlers=[logging.FileHandler(LOG_FILE, encoding='utf-8', mode='a'), logging.StreamHandler(sys.stdout)])
    return logging.getLogger(__name__)

def get_lr(step, warmup, max_lr, total):
    if step < warmup: return max_lr * (step + 1) / warmup
    progress = (step - warmup) / max(1, total - warmup)
    return max_lr * 0.5 * (1.0 + math.cos(math.pi * progress))

def train():
    logger = setup_logging()
    logger.info("=" * 60); logger.info("BPE Baseline A — English-only, BPE tokenized"); logger.info("=" * 60)
    logger.info(f"Device: {DEVICE}"); os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    dataset = BPEDataset(TRAINING_BIN, SEQ_LEN)
    logger.info(f"Chains: {len(dataset):,}")
    train_size = int(0.95 * len(dataset)); eval_size = len(dataset) - train_size
    train_ds, eval_ds = torch.utils.data.random_split(dataset, [train_size, eval_size], generator=torch.Generator().manual_seed(42))
    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True, drop_last=True, num_workers=0, pin_memory=(DEVICE=='cuda'))
    eval_loader = DataLoader(eval_ds, batch_size=BATCH_SIZE, shuffle=False, num_workers=0, pin_memory=(DEVICE=='cuda'))
    logger.info(f"Train: {len(train_ds):,} | Eval: {len(eval_ds):,} | Batches/epoch: {len(train_loader):,}")
    model = BPEBaselineModel().to(DEVICE)
    logger.info(f"Params: {model.count_parameters():,} | Arch: {model.n_layers}L d={model.d_model} {model.n_heads}h ff={model.d_ff} vocab={model.vocab_size}")
    optimizer = torch.optim.AdamW(model.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY, betas=(0.9, 0.95))
    total_steps = len(train_loader) * EPOCHS
    logger.info(f"Steps: {total_steps:,} | Epochs: {EPOCHS} | Batch: {BATCH_SIZE} | LR: {LEARNING_RATE}"); logger.info("")
    global_step = 0; best_eval = float('inf'); start = time.time()
    for epoch in range(1, EPOCHS + 1):
        model.train(); epoch_loss = 0.0
        for x, y in train_loader:
            x, y = x.to(DEVICE), y.to(DEVICE)
            lr = get_lr(global_step, WARMUP_STEPS, LEARNING_RATE, total_steps)
            for pg in optimizer.param_groups: pg['lr'] = lr
            logits, loss = model(x, y); optimizer.zero_grad(); loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), GRAD_CLIP); optimizer.step()
            epoch_loss += loss.item(); global_step += 1
            if global_step % 100 == 0:
                logger.info(f"Epoch {epoch}/{EPOCHS} | Step {global_step:,} | Loss: {loss.item():.4f} | LR: {lr:.2e}")
            if global_step % EVAL_INTERVAL == 0:
                model.eval(); el = 0.0; eb = 0
                with torch.no_grad():
                    for ex, ey in eval_loader: ex, ey = ex.to(DEVICE), ey.to(DEVICE); _, eloss = model(ex, ey); el += eloss.item(); eb += 1
                avg = el / max(1, eb); ppl = math.exp(min(avg, 20))
                logger.info(f"  EVAL | Loss: {avg:.4f} | Perplexity: {ppl:.2f}")
                if avg < best_eval:
                    best_eval = avg
                    torch.save({'model_state_dict': model.state_dict(), 'epoch': epoch, 'step': global_step, 'eval_loss': avg}, os.path.join(CHECKPOINT_DIR, 'best.pt'))
                    logger.info(f"  NEW BEST")
                model.train()
        logger.info(f"Epoch {epoch} complete | Avg loss: {epoch_loss/len(train_loader):.4f} | Time: {(time.time()-start)/60:.1f}m")
    torch.save({'model_state_dict': model.state_dict(), 'epoch': EPOCHS, 'step': global_step}, os.path.join(CHECKPOINT_DIR, 'final.pt'))
    logger.info(f"Training complete in {(time.time()-start)/60:.1f}m | Best eval: {best_eval:.4f} | Best ppl: {math.exp(min(best_eval,20)):.2f}")

if __name__ == '__main__': train()
