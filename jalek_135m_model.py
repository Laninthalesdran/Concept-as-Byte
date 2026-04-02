"""
JalekLM — Custom Transformer Architecture for Jalek Encoding

Why this exists instead of SmolLM:

SmolLM was designed for a 49,152-token BPE vocabulary. Its embedding layer
consumes 49,152 × 576 = 28.3M parameters. When we swap in vocab_size=256
(Jalek v1) or vocab_size=705 (Jalek v2), that embedding shrinks to ~147K
or ~406K parameters. The remaining ~28M parameters just disappear — they
are not reallocated. You end up running a 106M parameter model while the
architecture was budgeted for 135M.

JalekLM reallocates those freed parameters into transformer depth — 8
additional reasoning layers — giving a 38-layer model at the same 135M
parameter budget. For reasoning-heavy tasks, depth outperforms width.

Additional differences from SmolLM / LlamaForCausalLM:
- No HuggingFace dependency in the model itself (pure PyTorch)
- Clean config class with explicit Jalek v1 and v2 presets
- Documented parameter budget so you can see exactly where every param goes
- Compatible with standard PyTorch training loops

Architecture:
- RMSNorm (pre-norm, same as Llama)
- Grouped Query Attention with Rotary Position Embeddings
- SwiGLU feed-forward (same as Llama)
- Tied input/output embeddings (saves vocab_size × hidden_size params)

Usage:
    from jalek_model import JalekForCausalLM, JalekConfig

    # Jalek v1 (256-byte vocabulary)
    config = JalekConfig.v1()
    model = JalekForCausalLM(config)

    # Jalek v2 (705-concept vocabulary)
    config = JalekConfig.v2()
    model = JalekForCausalLM(config)

    # Forward pass
    logits = model(input_ids)           # (batch, seq_len, vocab_size)
    loss = model(input_ids, labels)     # scalar
"""

import math
from dataclasses import dataclass
from typing import Optional

import torch
import torch.nn as nn
import torch.nn.functional as F


# ============================================================
# CONFIG
# ============================================================

@dataclass
class JalekConfig:
    vocab_size: int        = 256     # 256 for v1, 705 for v2
    hidden_size: int       = 576
    intermediate_size: int = 1536
    num_layers: int        = 38      # 30 SmolLM + 8 reallocated from embedding savings
    num_heads: int         = 9
    num_kv_heads: int      = 3       # Grouped Query Attention
    max_seq_len: int       = 2048
    rope_theta: float      = 10000.0
    rms_norm_eps: float    = 1e-5
    dropout: float         = 0.0

    @classmethod
    def v1(cls) -> "JalekConfig":
        """Jalek v1: 256-byte vocabulary. ~135M parameters."""
        return cls(vocab_size=256, num_layers=38)

    @classmethod
    def v2(cls) -> "JalekConfig":
        """Jalek v2: 705-concept vocabulary. ~135M parameters."""
        return cls(vocab_size=705, num_layers=38)

    def parameter_budget(self) -> dict:
        """
        Break down where every parameter goes.
        Useful for verifying reallocation from embedding to layers.
        """
        embed = self.vocab_size * self.hidden_size  # shared w/ LM head (tied)
        head_dim = self.hidden_size // self.num_heads
        kv_dim = head_dim * self.num_kv_heads

        attn = (
            self.hidden_size * self.hidden_size +   # Q
            self.hidden_size * kv_dim +             # K
            self.hidden_size * kv_dim +             # V
            self.hidden_size * self.hidden_size     # O
        )
        ffn = (
            self.hidden_size * self.intermediate_size +  # gate
            self.hidden_size * self.intermediate_size +  # up
            self.intermediate_size * self.hidden_size    # down
        )
        norms = self.hidden_size * 2   # pre-attn + pre-ffn RMSNorm per layer
        per_layer = attn + ffn + norms
        layers_total = per_layer * self.num_layers
        final_norm = self.hidden_size
        total = embed + layers_total + final_norm  # embed tied with LM head

        return {
            "embedding (tied)": f"{embed:,}",
            "per layer": f"{per_layer:,}",
            "all layers": f"{layers_total:,}",
            "total": f"{total:,}",
            "total_M": f"{total/1e6:.1f}M",
        }


# ============================================================
# ROTARY POSITION EMBEDDING
# ============================================================

class RotaryEmbedding(nn.Module):
    def __init__(self, dim: int, max_seq_len: int, theta: float = 10000.0):
        super().__init__()
        inv_freq = 1.0 / (theta ** (torch.arange(0, dim, 2).float() / dim))
        self.register_buffer("inv_freq", inv_freq, persistent=False)
        self._build_cache(max_seq_len)

    def _build_cache(self, seq_len: int):
        t = torch.arange(seq_len, device=self.inv_freq.device).float()
        freqs = torch.outer(t, self.inv_freq)
        emb = torch.cat([freqs, freqs], dim=-1)
        self.register_buffer("cos_cache", emb.cos()[None, None, :, :], persistent=False)
        self.register_buffer("sin_cache", emb.sin()[None, None, :, :], persistent=False)

    def forward(self, q: torch.Tensor, k: torch.Tensor, seq_len: int):
        cos = self.cos_cache[:, :, :seq_len, :]
        sin = self.sin_cache[:, :, :seq_len, :]
        return apply_rotary(q, cos, sin), apply_rotary(k, cos, sin)


def rotate_half(x: torch.Tensor) -> torch.Tensor:
    half = x.shape[-1] // 2
    x1, x2 = x[..., :half], x[..., half:]
    return torch.cat([-x2, x1], dim=-1)


def apply_rotary(x: torch.Tensor, cos: torch.Tensor, sin: torch.Tensor) -> torch.Tensor:
    return x * cos + rotate_half(x) * sin


# ============================================================
# RMS NORM
# ============================================================

class RMSNorm(nn.Module):
    def __init__(self, dim: int, eps: float = 1e-5):
        super().__init__()
        self.eps = eps
        self.weight = nn.Parameter(torch.ones(dim))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        norm = x.float().pow(2).mean(-1, keepdim=True).add(self.eps).rsqrt()
        return (x.float() * norm).to(x.dtype) * self.weight


# ============================================================
# GROUPED QUERY ATTENTION
# ============================================================

class GQAttention(nn.Module):
    def __init__(self, config: JalekConfig):
        super().__init__()
        self.num_heads = config.num_heads
        self.num_kv_heads = config.num_kv_heads
        self.head_dim = config.hidden_size // config.num_heads
        self.groups = config.num_heads // config.num_kv_heads

        self.q_proj = nn.Linear(config.hidden_size, config.num_heads * self.head_dim, bias=False)
        self.k_proj = nn.Linear(config.hidden_size, config.num_kv_heads * self.head_dim, bias=False)
        self.v_proj = nn.Linear(config.hidden_size, config.num_kv_heads * self.head_dim, bias=False)
        self.o_proj = nn.Linear(config.num_heads * self.head_dim, config.hidden_size, bias=False)

        self.rope = RotaryEmbedding(self.head_dim, config.max_seq_len, config.rope_theta)
        self.dropout = config.dropout

    def forward(self, x: torch.Tensor, mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        B, T, _ = x.shape

        q = self.q_proj(x).view(B, T, self.num_heads, self.head_dim).transpose(1, 2)
        k = self.k_proj(x).view(B, T, self.num_kv_heads, self.head_dim).transpose(1, 2)
        v = self.v_proj(x).view(B, T, self.num_kv_heads, self.head_dim).transpose(1, 2)

        q, k = self.rope(q, k, T)

        # Expand KV heads to match Q heads (GQA)
        if self.groups > 1:
            k = k.repeat_interleave(self.groups, dim=1)
            v = v.repeat_interleave(self.groups, dim=1)

        # Scaled dot-product attention (uses flash attention if available)
        attn_dropout = self.dropout if self.training else 0.0
        out = F.scaled_dot_product_attention(q, k, v, attn_mask=mask,
                                             dropout_p=attn_dropout, is_causal=True)

        out = out.transpose(1, 2).contiguous().view(B, T, -1)
        return self.o_proj(out)


# ============================================================
# SWIGLU FEED-FORWARD
# ============================================================

class SwiGLU(nn.Module):
    def __init__(self, config: JalekConfig):
        super().__init__()
        self.gate = nn.Linear(config.hidden_size, config.intermediate_size, bias=False)
        self.up   = nn.Linear(config.hidden_size, config.intermediate_size, bias=False)
        self.down = nn.Linear(config.intermediate_size, config.hidden_size, bias=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.down(F.silu(self.gate(x)) * self.up(x))


# ============================================================
# DECODER LAYER
# ============================================================

class JalekLayer(nn.Module):
    def __init__(self, config: JalekConfig):
        super().__init__()
        self.norm1 = RMSNorm(config.hidden_size, config.rms_norm_eps)
        self.attn  = GQAttention(config)
        self.norm2 = RMSNorm(config.hidden_size, config.rms_norm_eps)
        self.ffn   = SwiGLU(config)

    def forward(self, x: torch.Tensor, mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        x = x + self.attn(self.norm1(x), mask)
        x = x + self.ffn(self.norm2(x))
        return x


# ============================================================
# FULL MODEL
# ============================================================

class JalekModel(nn.Module):
    """Transformer body — no LM head."""
    def __init__(self, config: JalekConfig):
        super().__init__()
        self.embed = nn.Embedding(config.vocab_size, config.hidden_size)
        self.layers = nn.ModuleList([JalekLayer(config) for _ in range(config.num_layers)])
        self.norm = RMSNorm(config.hidden_size, config.rms_norm_eps)

    def forward(self, input_ids: torch.Tensor,
                mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        x = self.embed(input_ids)
        for layer in self.layers:
            x = layer(x, mask)
        return self.norm(x)


class JalekForCausalLM(nn.Module):
    """
    Full causal language model — transformer body + LM head.

    The LM head weight is tied to the embedding weight (standard practice).
    This means the embedding and output projection share the same parameters,
    saving vocab_size × hidden_size parameters.

    For Jalek v1 (256 vocab): saves 147K params — negligible.
    For Jalek v2 (705 vocab): saves 406K params — still small.
    Both are tiny vs the 28M SmolLM saved by dropping the BPE vocab size,
    which is reallocated to the 8 additional transformer layers.
    """
    def __init__(self, config: JalekConfig):
        super().__init__()
        self.config = config
        self.model = JalekModel(config)
        self.lm_head = nn.Linear(config.hidden_size, config.vocab_size, bias=False)

        # Tie weights
        self.lm_head.weight = self.model.embed.weight

        self._init_weights()

    def _init_weights(self):
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.normal_(module.weight, mean=0.0, std=0.02)
                if module.bias is not None:
                    nn.init.zeros_(module.bias)
            elif isinstance(module, nn.Embedding):
                nn.init.normal_(module.weight, mean=0.0, std=0.02)

    def forward(self, input_ids: torch.Tensor,
                labels: Optional[torch.Tensor] = None,
                mask: Optional[torch.Tensor] = None):
        """
        Args:
            input_ids: (batch, seq_len)
            labels:    (batch, seq_len) — if provided, returns loss
            mask:      optional attention mask

        Returns:
            If labels provided: (loss, logits)
            Otherwise: logits (batch, seq_len, vocab_size)
        """
        hidden = self.model(input_ids, mask)
        logits = self.lm_head(hidden)

        if labels is None:
            return logits

        # Shift for causal LM: predict token[i+1] from token[i]
        shift_logits = logits[:, :-1, :].contiguous()
        shift_labels = labels[:, 1:].contiguous()

        loss = F.cross_entropy(
            shift_logits.view(-1, self.config.vocab_size),
            shift_labels.view(-1),
            ignore_index=-100,
        )
        return loss, logits

    def num_parameters(self, trainable_only: bool = True) -> int:
        if trainable_only:
            return sum(p.numel() for p in self.parameters() if p.requires_grad)
        return sum(p.numel() for p in self.parameters())

    def generate(self, input_ids: torch.Tensor, max_new_tokens: int = 200,
                 temperature: float = 1.0, top_k: int = 0) -> torch.Tensor:
        """Simple autoregressive generation."""
        self.eval()
        with torch.no_grad():
            for _ in range(max_new_tokens):
                # Crop to max_seq_len
                idx = input_ids[:, -self.config.max_seq_len:]
                logits = self(idx)
                logits = logits[:, -1, :] / max(temperature, 1e-8)

                if top_k > 0:
                    v, _ = torch.topk(logits, min(top_k, logits.size(-1)))
                    logits[logits < v[:, [-1]]] = float('-inf')

                probs = F.softmax(logits, dim=-1)
                next_token = torch.multinomial(probs, num_samples=1)
                input_ids = torch.cat([input_ids, next_token], dim=1)

        return input_ids


# ============================================================
# PARAMETER REPORT
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("JalekLM v1 (256-byte vocabulary)")
    print("=" * 60)
    cfg_v1 = JalekConfig.v1()
    model_v1 = JalekForCausalLM(cfg_v1)
    budget = cfg_v1.parameter_budget()
    for k, v in budget.items():
        print(f"  {k:<25} {v}")
    print(f"  actual trainable        {model_v1.num_parameters():,}")
    print()

    print("=" * 60)
    print("JalekLM v2 (705-concept vocabulary)")
    print("=" * 60)
    cfg_v2 = JalekConfig.v2()
    model_v2 = JalekForCausalLM(cfg_v2)
    budget = cfg_v2.parameter_budget()
    for k, v in budget.items():
        print(f"  {k:<25} {v}")
    print(f"  actual trainable        {model_v2.num_parameters():,}")
    print()

    print("=" * 60)
    print("SmolLM equivalent (49,152 vocab, 30 layers) for comparison")
    print("=" * 60)
    cfg_smol = JalekConfig(vocab_size=49152, num_layers=30)
    budget = cfg_smol.parameter_budget()
    for k, v in budget.items():
        print(f"  {k:<25} {v}")
    print()

    print("Depth comparison: JalekLM has 38 layers vs SmolLM's 30.")
    print("Same parameter budget. 27% more reasoning depth.")
