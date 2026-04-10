# Primary Research Paper — Matched Comparison Results

## BPE vs Concept Byte Encoding on Identical Data
## Travis Edward Holley — April 9, 2026

---

## Experiment

Two models with matched architecture and parameter count trained on the same 414,515 Tatoeba Esperanto sentences. The ONLY difference is the encoding method.

## Results

| | Concept Bytes | BPE Baseline |
|--|--|--|
| **Parameters** | 7,178,880 | 7,185,024 |
| **Vocab size** | 256 | 2,000 |
| **Architecture** | 3L d=384 8h ff=1536 | 3L d=384 8h ff=1344 |
| **Best eval loss** | **0.9305** | 2.5737 |
| **Best perplexity** | **2.54** | 13.11 |
| **Peaked at epoch** | 6 | 6 |
| **Early stopped** | Epoch 9 (patience=3) | Epoch 9 (patience=3) |
| **Training time** | 100 min | 100 min |

### Normalized Comparison (fair cross-vocabulary)

Raw perplexity is not directly comparable across different vocabulary sizes. Normalized by original sentence length:

| | Concept Bytes | BPE |
|--|--|--|
| Avg tokens per sentence | 22.8 bytes | 12.2 tokens |
| Nats per sentence | 21.2 | 31.4 |
| **Normalized efficiency** | **1.48x better** | baseline |

Concept byte encoding extracts 48% more learning from identical training data at matched parameter count.

## What Was Controlled

- Same 414,515 Tatoeba Esperanto sentences
- Same Transformer architecture (RoPE, RMSNorm, SwiGLU, tied embeddings)
- Matched parameter count (~7.18M, d_ff adjusted to compensate for BPE's larger embedding)
- Same hyperparameters (batch=256, seq=512, lr=3e-4, warmup=1000, patience=3)
- Same hardware (NVIDIA RTX PRO 6000 Blackwell, 98GB VRAM)
- Same random seed for train/eval split (seed=42, 95/5 split)
- Same optimizer (AdamW, betas=(0.9, 0.95), weight_decay=0.01)
- Same precision (BF16)

## What Differs

- Encoding method: concept bytes (morpheme-level, 256 vocab) vs BPE (subword, 2000 vocab)
- d_ff: 1536 (concept byte) vs 1344 (BPE) — compensates for BPE's larger embedding layer to match total param count
- Sequence representation: concept bytes average 22.8 bytes/sentence vs BPE's 12.2 tokens/sentence

## Files

| File | Description |
|------|-------------|
| `concept_byte_7.18M_weights.pt` | Trained concept byte model weights (best checkpoint) |
| `bpe_7.18M_weights.pt` | Trained BPE baseline weights (best checkpoint) |
| `results_concept_byte.json` | Epoch-by-epoch training metrics (concept byte) |
| `results_bpe.json` | Epoch-by-epoch training metrics (BPE) |
| `training_concept_byte.log` | Full training log (concept byte) |
| `training_bpe.log` | Full training log (BPE) |
| `train_concept_byte.py` | Self-contained training script (concept byte) |
| `train_bpe.py` | Self-contained training script (BPE) |
| `build_matched_data.py` | Data preparation script (encodes same sentences both ways) |
| `bpe_esperanto.model` | SentencePiece BPE tokenizer (trained on the 414K sentences) |

## Reproduction

1. Download Tatoeba Esperanto-English sentence pairs from tatoeba.org
2. Run `build_matched_data.py` with the Esperanto encoder table to produce both training binaries
3. Run `train_concept_byte.py` and `train_bpe.py` on a CUDA-capable GPU
4. Compare `results_concept_byte.json` and `results_bpe.json`

## Hardware

- Training: NVIDIA RTX PRO 6000 Blackwell Server Edition (98GB VRAM) on RunPod
- Pod ID: 3qv9tnhdes39k7 (juicy_copper_lynx)

---

*Travis Edward Holley — April 9, 2026*
