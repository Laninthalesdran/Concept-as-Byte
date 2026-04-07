"""
LLZ (The Zamenhof) — Context-Aware Translator Model

7.18M parameter model. Wide and shallow: big memory, pattern matching.
Translates between English and ZofiaZ bytes by holding input context
in reserve and making judgment calls on output.

Architecture: 3-layer Transformer, d_model=384, 8 heads, d_ff=1536
Tied embeddings. RoPE. RMSNorm. SwiGLU.
Vocab: 256 (byte-level, same as AdamZ)

The LLZ does NOT reason. It translates. It picks the right English word
from the decode list based on input AND output context.

Named for Ludwik Lejzer Zamenhof (1859-1917).

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


class LLZModel(nn.Module):
    """
    The Zamenhof — LLZ Translator

    7.18M parameters. Wide attention, shallow depth.
    Holds input context in reserve, picks the right translation.

    This model does NOT reason. It translates.
    """

    def __init__(
        self,
        vocab_size=256,
        d_model=384,
        n_heads=8,
        n_layers=3,
        d_ff=1536,
        max_seq_len=512,
    ):
        super().__init__()
        self.vocab_size = vocab_size
        self.d_model = d_model
        self.n_heads = n_heads
        self.n_layers = n_layers
        self.d_ff = d_ff
        self.max_seq_len = max_seq_len

        # Embedding (tied with output)
        self.embed = nn.Embedding(vocab_size, d_model)

        # Rotary position encoding
        self.rotary = RotaryEmbedding(d_model // n_heads, max_seq_len)

        # Transformer layers
        self.layers = nn.ModuleList([
            TransformerBlock(d_model, n_heads, d_ff)
            for _ in range(n_layers)
        ])

        # Output norm
        self.norm = RMSNorm(d_model)

        # Tied output projection (shares weights with embedding)
        self.output = nn.Linear(d_model, vocab_size, bias=False)
        self.output.weight = self.embed.weight  # tie weights

        # Causal mask
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
        assert T <= self.max_seq_len, f"Sequence length {T} exceeds max {self.max_seq_len}"

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

    @torch.no_grad()
    def generate(self, idx, max_new_tokens, temperature=1.0, top_k=None):
        """Generate tokens autoregressively."""
        for _ in range(max_new_tokens):
            idx_cond = idx if idx.size(1) <= self.max_seq_len else idx[:, -self.max_seq_len:]
            logits, _ = self(idx_cond)
            logits = logits[:, -1, :] / temperature

            if top_k is not None:
                v, _ = torch.topk(logits, min(top_k, logits.size(-1)))
                logits[logits < v[:, [-1]]] = float('-inf')

            probs = F.softmax(logits, dim=-1)
            idx_next = torch.multinomial(probs, num_samples=1)
            idx = torch.cat((idx, idx_next), dim=1)

            # Stop on END byte
            if idx_next.item() == 0x00:
                break

        return idx


if __name__ == '__main__':
    model = LLZModel()
    print(f"LLZ (The Zamenhof) — Translator Model")
    print(f"Parameters: {model.count_parameters():,}")
    print(f"Architecture: {model.n_layers} layers, d_model={model.d_model}, "
          f"{model.n_heads} heads, d_ff={model.d_ff}")
    print(f"Vocab: {model.vocab_size} (byte-level)")
    print(f"Max sequence: {model.max_seq_len}")
    print()

    # Test forward pass
    x = torch.randint(0, 256, (1, 64))
    logits, _ = model(x)
    print(f"Input shape: {x.shape}")
    print(f"Output shape: {logits.shape}")
    print(f"Forward pass: OK")

    # Architecture summary
    print()
    print("=== DESIGN PHILOSOPHY ===")
    print("Wide attention (384 dim, 8 heads) = large memory per position")
    print("Shallow depth (3 layers) = pattern matching, not reasoning")
    print("The LLZ remembers. It does not think.")
    print("It holds English input in reserve and picks the right word.")
