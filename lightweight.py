"""
Strawweight — 10M Parameter Reasoning Engine

Decoder-only transformer trained on Phase 1 concept algebra.
256-byte vocabulary (JalekCore single-byte tier).
Designed to run on anything — phone, thermostat, toaster.

Architecture:
  vocab_size: 256
  d_model: 320
  n_heads: 8 (head_dim 40)
  n_layers: 8
  d_ff: 1280 (4x d_model)
  context_length: 512
  ~10M parameters

Author: Travis Holley / Claude
Date: March 31, 2026
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F


class RMSNorm(nn.Module):
    """Root Mean Square Layer Normalization — simpler, faster than LayerNorm."""
    def __init__(self, dim, eps=1e-6):
        super().__init__()
        self.eps = eps
        self.weight = nn.Parameter(torch.ones(dim))

    def forward(self, x):
        norm = torch.rsqrt(x.pow(2).mean(-1, keepdim=True) + self.eps)
        return x * norm * self.weight


class RotaryEmbedding(nn.Module):
    """Rotary Position Embedding (RoPE) — no learned position embeddings needed."""
    def __init__(self, dim, max_seq_len=512):
        super().__init__()
        inv_freq = 1.0 / (10000 ** (torch.arange(0, dim, 2).float() / dim))
        self.register_buffer("inv_freq", inv_freq)
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
    cos = cos.unsqueeze(0).unsqueeze(0)  # [1, 1, seq, dim]
    sin = sin.unsqueeze(0).unsqueeze(0)
    q_embed = (q * cos) + (rotate_half(q) * sin)
    k_embed = (k * cos) + (rotate_half(k) * sin)
    return q_embed, k_embed


class Attention(nn.Module):
    def __init__(self, d_model, n_heads):
        super().__init__()
        self.n_heads = n_heads
        self.head_dim = d_model // n_heads
        self.d_model = d_model

        self.q_proj = nn.Linear(d_model, d_model, bias=False)
        self.k_proj = nn.Linear(d_model, d_model, bias=False)
        self.v_proj = nn.Linear(d_model, d_model, bias=False)
        self.o_proj = nn.Linear(d_model, d_model, bias=False)

    def forward(self, x, cos, sin, mask=None):
        B, T, C = x.shape

        q = self.q_proj(x).view(B, T, self.n_heads, self.head_dim).transpose(1, 2)
        k = self.k_proj(x).view(B, T, self.n_heads, self.head_dim).transpose(1, 2)
        v = self.v_proj(x).view(B, T, self.n_heads, self.head_dim).transpose(1, 2)

        q, k = apply_rotary_pos_emb(q, k, cos, sin)

        att = (q @ k.transpose(-2, -1)) * (self.head_dim ** -0.5)
        if mask is not None:
            att = att.masked_fill(mask == 0, float('-inf'))
        att = F.softmax(att, dim=-1)

        out = (att @ v).transpose(1, 2).contiguous().view(B, T, C)
        return self.o_proj(out)


class FeedForward(nn.Module):
    """SwiGLU-style feed-forward — better than ReLU for small models."""
    def __init__(self, d_model, d_ff):
        super().__init__()
        self.gate_proj = nn.Linear(d_model, d_ff, bias=False)
        self.up_proj = nn.Linear(d_model, d_ff, bias=False)
        self.down_proj = nn.Linear(d_ff, d_model, bias=False)

    def forward(self, x):
        return self.down_proj(F.silu(self.gate_proj(x)) * self.up_proj(x))


class TransformerBlock(nn.Module):
    def __init__(self, d_model, n_heads, d_ff):
        super().__init__()
        self.attn_norm = RMSNorm(d_model)
        self.attn = Attention(d_model, n_heads)
        self.ff_norm = RMSNorm(d_model)
        self.ff = FeedForward(d_model, d_ff)

    def forward(self, x, cos, sin, mask=None):
        x = x + self.attn(self.attn_norm(x), cos, sin, mask)
        x = x + self.ff(self.ff_norm(x))
        return x


class Strawweight(nn.Module):
    """
    Strawweight: 10M parameter reasoning engine.

    256-byte vocab, 8 layers, d_model 320.
    RoPE positions, RMSNorm, SwiGLU FFN.
    Modern architecture choices from LLaMA/Mistral lineage
    scaled down to fit on a thermostat.
    """
    def __init__(
        self,
        vocab_size=256,
        d_model=320,
        n_heads=8,
        n_layers=8,
        d_ff=1280,
        max_seq_len=512,
    ):
        super().__init__()
        self.d_model = d_model
        self.max_seq_len = max_seq_len

        self.tok_emb = nn.Embedding(vocab_size, d_model)
        self.rotary = RotaryEmbedding(d_model // n_heads, max_seq_len)

        self.layers = nn.ModuleList([
            TransformerBlock(d_model, n_heads, d_ff)
            for _ in range(n_layers)
        ])

        self.norm = RMSNorm(d_model)
        self.output = nn.Linear(d_model, vocab_size, bias=False)

        # Tie embedding weights
        self.output.weight = self.tok_emb.weight

        self._init_weights()

    def _init_weights(self):
        for module in self.modules():
            if isinstance(module, nn.Linear):
                torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)
            elif isinstance(module, nn.Embedding):
                torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)

    def forward(self, idx, targets=None):
        B, T = idx.shape
        device = idx.device

        x = self.tok_emb(idx)

        cos, sin = self.rotary(T, device)

        # Causal mask
        mask = torch.tril(torch.ones(T, T, device=device)).unsqueeze(0).unsqueeze(0)

        for layer in self.layers:
            x = layer(x, cos, sin, mask)

        x = self.norm(x)
        logits = self.output(x)

        loss = None
        if targets is not None:
            loss = F.cross_entropy(logits.view(-1, logits.size(-1)), targets.view(-1))

        return logits, loss

    def count_parameters(self):
        return sum(p.numel() for p in self.parameters())

    @torch.no_grad()
    def generate(self, idx, max_new_tokens, temperature=1.0, top_k=None):
        for _ in range(max_new_tokens):
            idx_cond = idx[:, -self.max_seq_len:]
            logits, _ = self(idx_cond)
            logits = logits[:, -1, :] / temperature
            if top_k is not None:
                v, _ = torch.topk(logits, min(top_k, logits.size(-1)))
                logits[logits < v[:, [-1]]] = float('-inf')
            probs = F.softmax(logits, dim=-1)
            idx_next = torch.multinomial(probs, num_samples=1)
            idx = torch.cat((idx, idx_next), dim=1)
        return idx


def count_params():
    """Quick parameter count check."""
    model = Strawweight()
    total = model.count_parameters()
    print(f"Strawweight: {total:,} parameters ({total/1e6:.1f}M)")
    print(f"Model size at fp32: {total * 4 / 1024 / 1024:.1f} MB")
    print(f"Model size at fp16: {total * 2 / 1024 / 1024:.1f} MB")
    print()

    # Breakdown
    emb = sum(p.numel() for p in model.tok_emb.parameters())
    layers = sum(p.numel() for n, p in model.named_parameters() if 'layers' in n)
    norm = sum(p.numel() for n, p in model.named_parameters() if n == 'norm.weight')
    print(f"  Embedding (tied): {emb:,}")
    print(f"  Transformer layers: {layers:,}")
    print(f"  Final norm: {norm:,}")
    print(f"  Output head: tied with embedding")


if __name__ == "__main__":
    count_params()
