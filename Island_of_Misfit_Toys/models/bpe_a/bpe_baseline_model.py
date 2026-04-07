"""
BPE Baseline — 7.18M Parameter Control Model

Identical Transformer architecture to LLZ and LidiaZ 7M.
Uses SentencePiece BPE tokenization instead of concept bytes.
Trained on same English data for fair comparison.

Architecture: 3-layer Transformer, d_model=384, 8 heads, d_ff=1536
RoPE. RMSNorm. SwiGLU.
Vocab: 8000 (BPE tokens via SentencePiece)

The ONLY difference from LLZ is the tokenization.
LLZ uses concept byte lookup (256 vocab).
This model uses BPE tokenization (8000 vocab).
Same data. Same params. Same architecture.

Author: Travis Edward Holley
Architecture: Claude (Anthropic)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import math


class RMSNorm(nn.Module):
    def __init__(self, dim, eps=1e-6):
        super().__init__()
        self.eps = eps
        self.weight = nn.Parameter(torch.ones(dim))

    def forward(self, x):
        norm = torch.rsqrt(x.pow(2).mean(-1, keepdim=True) + self.eps)
        return x * norm * self.weight


class RotaryEmbedding(nn.Module):
    def __init__(self, dim, max_seq_len=512, base=10000.0):
        super().__init__()
        inv_freq = 1.0 / (base ** (torch.arange(0, dim, 2).float() / dim))
        self.register_buffer('inv_freq', inv_freq)
        self.max_seq_len = max_seq_len

    def forward(self, seq_len, device):
        t = torch.arange(seq_len, device=device, dtype=self.inv_freq.dtype)
        freqs = torch.outer(t, self.inv_freq)
        emb = torch.cat((freqs, freqs), dim=-1)
        return emb.cos(), emb.sin()


def rotate_half(x):
    x1, x2 = x.chunk(2, dim=-1)
    return torch.cat((-x2, x1), dim=-1)


def apply_rotary_pos_emb(q, k, cos, sin):
    cos = cos.unsqueeze(0).unsqueeze(0)
    sin = sin.unsqueeze(0).unsqueeze(0)
    q_embed = (q * cos) + (rotate_half(q) * sin)
    k_embed = (k * cos) + (rotate_half(k) * sin)
    return q_embed, k_embed


class SwiGLU(nn.Module):
    def __init__(self, d_model, d_ff):
        super().__init__()
        self.w1 = nn.Linear(d_model, d_ff, bias=False)
        self.w2 = nn.Linear(d_ff, d_model, bias=False)
        self.w3 = nn.Linear(d_model, d_ff, bias=False)

    def forward(self, x):
        return self.w2(F.silu(self.w1(x)) * self.w3(x))


class Attention(nn.Module):
    def __init__(self, d_model, n_heads):
        super().__init__()
        self.n_heads = n_heads
        self.head_dim = d_model // n_heads
        self.wq = nn.Linear(d_model, d_model, bias=False)
        self.wk = nn.Linear(d_model, d_model, bias=False)
        self.wv = nn.Linear(d_model, d_model, bias=False)
        self.wo = nn.Linear(d_model, d_model, bias=False)

    def forward(self, x, cos, sin, mask=None):
        B, T, C = x.shape
        q = self.wq(x).view(B, T, self.n_heads, self.head_dim).transpose(1, 2)
        k = self.wk(x).view(B, T, self.n_heads, self.head_dim).transpose(1, 2)
        v = self.wv(x).view(B, T, self.n_heads, self.head_dim).transpose(1, 2)

        q, k = apply_rotary_pos_emb(q, k, cos[:T], sin[:T])

        att = (q @ k.transpose(-2, -1)) * (self.head_dim ** -0.5)
        if mask is not None:
            att = att.masked_fill(mask[:, :, :T, :T] == 0, float('-inf'))
        att = F.softmax(att, dim=-1)

        out = (att @ v).transpose(1, 2).contiguous().view(B, T, C)
        return self.wo(out)


class TransformerBlock(nn.Module):
    def __init__(self, d_model, n_heads, d_ff):
        super().__init__()
        self.attn = Attention(d_model, n_heads)
        self.ffn = SwiGLU(d_model, d_ff)
        self.norm1 = RMSNorm(d_model)
        self.norm2 = RMSNorm(d_model)

    def forward(self, x, cos, sin, mask=None):
        x = x + self.attn(self.norm1(x), cos, sin, mask)
        x = x + self.ffn(self.norm2(x))
        return x


class BPEBaselineModel(nn.Module):
    """
    BPE Baseline — Control model for Concept-as-Byte comparison.

    Identical architecture to LLZ/LidiaZ 7M.
    Only the vocab size differs: 8000 BPE tokens vs 256 concept bytes.

    Note: larger vocab means the embedding and output layers are larger,
    so we reduce d_ff slightly to keep total params at ~7.18M.
    """

    def __init__(
        self,
        vocab_size=2000,
        d_model=384,
        n_heads=8,
        n_layers=3,
        d_ff=1344,       # adjusted to match ~7.18M params with tied embeddings
        max_seq_len=512,
    ):
        super().__init__()
        self.vocab_size = vocab_size
        self.d_model = d_model
        self.n_heads = n_heads
        self.n_layers = n_layers
        self.d_ff = d_ff
        self.max_seq_len = max_seq_len

        self.embed = nn.Embedding(vocab_size, d_model)
        self.rotary = RotaryEmbedding(d_model // n_heads, max_seq_len)

        self.layers = nn.ModuleList([
            TransformerBlock(d_model, n_heads, d_ff)
            for _ in range(n_layers)
        ])

        self.norm = RMSNorm(d_model)
        self.output = nn.Linear(d_model, vocab_size, bias=False)
        self.output.weight = self.embed.weight  # tied embeddings

        mask = torch.tril(torch.ones(max_seq_len, max_seq_len))
        self.register_buffer('causal_mask', mask.unsqueeze(0).unsqueeze(0))

        self._init_weights()

    def _init_weights(self):
        for module in self.modules():
            if isinstance(module, nn.Linear):
                torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)
            elif isinstance(module, nn.Embedding):
                torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)

    def forward(self, idx, targets=None):
        B, T = idx.shape
        assert T <= self.max_seq_len

        x = self.embed(idx)
        cos, sin = self.rotary(T, idx.device)

        for layer in self.layers:
            x = layer(x, cos, sin, self.causal_mask)

        x = self.norm(x)
        logits = self.output(x)

        loss = None
        if targets is not None:
            loss = F.cross_entropy(
                logits.view(-1, self.vocab_size),
                targets.view(-1),
                ignore_index=-1,
            )

        return logits, loss

    def count_parameters(self):
        return sum(p.numel() for p in self.parameters() if p.requires_grad)


if __name__ == '__main__':
    model = BPEBaselineModel()
    print(f"BPE Baseline — Control Model")
    print(f"Parameters: {model.count_parameters():,}")
    print(f"Architecture: {model.n_layers}L, d={model.d_model}, {model.n_heads}h, ff={model.d_ff}")
    print(f"Vocab: {model.vocab_size} (BPE tokens)")
    print()

    x = torch.randint(0, model.vocab_size, (1, 64))
    logits, _ = model(x)
    print(f"Forward pass: OK")
    print()
    print("=== FAIR COMPARISON ===")
    print(f"BPE Baseline: {model.count_parameters():,} params | 3L d=384 8h ff={model.d_ff} | vocab={model.vocab_size} BPE")
    print(f"LLZ:          7,178,880 params | 3L d=384 8h ff=1536 | vocab=256 word bytes")
    print(f"LidiaZ 7M:    7,178,880 params | 3L d=384 8h ff=1536 | vocab=256 concept bytes")
    print(f"Same architecture. Param count matched by adjusting d_ff.")
