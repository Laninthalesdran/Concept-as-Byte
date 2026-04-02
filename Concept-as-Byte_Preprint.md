# Concept-as-Byte: Dense Morphological Encoding for Language Model Training

**Technical Preprint**

**Travis Edward Holley**
South Carolina, USA
travis@tntholley.com

**Date:** April 2, 2026
**Version:** 1.0

---

## License and Patent Notice

This work is released under **Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC-BY-NC-SA 4.0)**.

Commercial licensing is available by contacting the author.

The methods described herein are the subject of U.S. Patent Application No. 64/017,122, "Dense Byte-Level Semantic Encoding for AI Model Training and Inference," filed March 25, 2026, assigned to Travis Edward Holley. Application currently undergoing preexam processing at the United States Patent and Trademark Office.

---

## 1. Summary

This preprint introduces Byte as Concept, an encoding architecture for language model training that replaces subword tokenization (BPE, WordPiece, SentencePiece) with dense morphological byte encoding. Each byte in the encoded stream represents a complete semantic concept — a morphological root, derivational affix, grammatical marker, or structural control signal — rather than a statistical subword fragment.

The morpheme inventory is drawn from L.L. Zamenhof's Esperanto system (1887–1894), which was designed from first principles for complete composability. Approximately 1,700 atomic morphemes, combined with 41 derivational affixes and 12 grammatical endings, can express any concept in human language through systematic composition.

We present preliminary training results from one model configuration:
- A 134.7M parameter model trained on byte-encoded web data (FineWeb-Edu, Cosmopedia-v2, Python-Edu) achieving a final loss of 1.8257 in 6.5 hours of training.

Model was trained on data encoded through a table of approximately 23.4 million byte-sequence entries. These are preliminary results on data that was primarily encoded as whole-word byte lookups with some morphological decomposition at the base level. Full training on morphologically decomposed data is in progress and will be reported in a subsequent publication.

The encoding table, encoder/decoder implementation, model configurations, and training logs are released under CC-BY-NC-SA 4.0.

---

## 2. Motivation

Modern language models operate on subword tokenization schemes that decompose text into statistically derived fragments. A word like "unhappiness" might tokenize as ["un", "happ", "iness"] — fragments that carry no inherent semantic meaning. The model must learn from context that "un" negates, that "happ" relates to happiness, and that "iness" nominalizes. This learning is implicit, computationally expensive, and must be relearned for every model trained.

Byte as Concept takes a different approach: encode every word as an explicit sequence of semantic morphemes before the model ever sees it. "Unhappiness" becomes [mal] [BOUNDARY] [feliĉ] [BOUNDARY] [ec] [BOUNDARY] [o] — opposite + happy + quality + noun — where each morpheme maps to a fixed byte code in a pre-computed table.

The encoder is a pure table lookup. A word enters, a pre-computed byte sequence exits. No morphological analysis occurs at inference time. All decomposition is pre-computed and stored in the table.

The hypothesis is that morpheme sequences have lower conditional entropy than subword token sequences, because morphological composition rules constrain what can follow what. After a root morpheme, the valid next bytes are limited to derivational suffixes, grammatical endings, or word boundaries — a constrained set governed by compositional rules rather than statistical co-occurrence.

---

## 3. Encoding Architecture

### 3.1 Byte Vocabulary

The encoding uses a 256-byte vocabulary:

| Range | Count | Contents |
|-------|-------|----------|
| 0x00–0x09 | 10 | Control bytes |
| 0x0A–0xFF | 246 | Content bytes (morphemes, digits, letters, symbols) |

### 3.2 Control Bytes

Control bytes serve structural functions and never appear inside morpheme codes:

| Byte | Name | Function |
|------|------|----------|
| 0x00 | END | Sequence terminator |
| 0x01 | BOUNDARY | Morpheme delimiter within a word |
| 0x02 | SPACE | Word delimiter |
| 0x03 | NEWLINE | Line boundary |
| 0x04 | PARAGRAPH | Paragraph boundary |
| 0x05 | Q/A | Question-to-answer transition signal |
| 0x06 | SKIP | Paired delimiter for attention-masked regions |
| 0x07 | JALEKON | Code mode toggle (reserved) |
| 0x08 | NAME | Proper noun prefix |
| 0x09 | COIN | Unknown word prefix (letter-by-letter spelling follows) |

### 3.3 Content Byte Assignment

Content bytes are assigned by frequency priority to minimize composed word length:

| Tier | Contents | Code Length |
|------|----------|-------------|
| Digits 0–9 + decimal | 11 entries | 1 byte |
| Letters (Esperanto 28 + q, w, x, y) | 32 entries | 1 byte |
| Basic punctuation ( . , ? ! ) | 4 entries | 1 byte |
| Grammatical endings (-o, -a, -e, -i, -as, -is, -os, -us, -u, -j, -n, la) | 12 entries | 1 byte |
| Zamenhof derivational affixes (31 suffixes + 14 prefixes) | 45 entries | 1 byte |
| High-frequency roots | ~146 entries | 1 byte |
| Remaining roots | ~1,494 entries | 2 bytes |
| Symbols (math, logic, Greek, currency, scientific) | ~132 entries | 2 bytes |

Every composed word is a sequence of morpheme bytes separated by BOUNDARY (0x01). Placing the most frequent morphemes in single-byte codes minimizes the total length of composed words across the training corpus.

### 3.4 Terminology and Morphological Source

We refer to the encoded byte-level representation as **Jalek**. Jalek is not a language — it is a byte encoding that uses Esperanto morphology as its decomposition system. The base language is Esperanto; the encoded form is Jalek. When text is encoded through the morphological table, the output is a Jalek byte stream. When a Jalek byte stream is decoded, the output is human-readable text.

The morpheme inventory is drawn from:
- L.L. Zamenhof, *Dr. Esperanto's International Language* (Unua Libro), 1887. Approximately 917 root words.
- L.L. Zamenhof, *Universala Vortaro*, 1894. Additional roots expanding the base vocabulary.

Total: approximately 1,700 atomic morphemes. Zamenhof designed Esperanto for complete composability — any concept can be expressed by combining roots with affixes and grammatical endings. We use Zamenhof's original morpheme order without modification.

### 3.5 Encoding Example

The English phrase "The unhealthy person speaks" encodes as:

```
la SPACE mal BOUNDARY san BOUNDARY ul BOUNDARY o SPACE parol BOUNDARY as
```

Where:
- `la` = the (function word, single table lookup)
- `mal` = opposite (prefix)
- `san` = health (root)
- `ul` = person characterized by (suffix)
- `o` = noun (grammatical ending)
- `parol` = speak (root)
- `as` = present tense (grammatical ending)

Each component is a single table lookup. The model receives a transparent sequence of semantic concepts with explicit compositional structure.

---

## 4. Notable Design Decisions

### 4.1 Q/A Control Byte

The Q/A byte (0x05) is a structural transition signal that marks the boundary between a question and an answer. It replaces the USER/ASSISTANT role token hierarchy used by current language models.

Role tokens carry implicit authority — models treat SYSTEM tokens as having higher privilege than USER tokens. This creates an attack surface for prompt injection, where adversarial inputs can mimic high-privilege tokens. The Q/A byte carries no authority. It signals a structural transition (from inquiry to response) without encoding any privilege hierarchy.

### 4.2 SKIP Byte

The SKIP byte (0x06) functions as a paired delimiter. Content between SKIP pairs is zeroed out in the attention computation at the architectural level — the model cannot see it. The orchestration system outside the model can read SKIP-enclosed content for routing, metadata, and control purposes.

This creates a dual-purpose byte stream: reasoning content visible to the model, and system metadata visible only to the orchestrator, in the same sequence. No training cost is incurred for SKIP behavior — it is implemented in the attention mask.

### 4.3 Spelling and Translation

A model trained on Jalek byte streams does not learn to spell words in any human language. It learns to predict morpheme bytes. To produce human-readable output, a Jalek-trained model requires a decoder that translates morpheme byte sequences back to surface-language text via the encoding table in reverse.

Similarly, a Jalek-trained model would need to be trained on spelling at some point in the training cycle to produce correctly spelled output of unknown words (words not on table) in a target language. The current architecture separates reasoning (morpheme prediction) from surface-language production (table-mediated translation). This separation is intentional — it allows the reasoning engine to operate on clean compositional primitives without bearing the cost of learning the irregularities of any specific human language's orthography.

### 4.4 Suffix Order Preservation

We considered reordering certain derivational suffixes to precede the root ("prefix promotion") based on the hypothesis that modifiers arriving before the content would prime the model's processing. After analysis, we determined this would increase the prediction space rather than narrow it.

In autoregressive prediction, seeing the root first constrains the set of valid following morphemes to a small number of suffixes and endings. Placing the modifier first would require predicting which root follows from a much larger set. Zamenhof's original suffix-after-root order is already optimal for autoregressive next-byte prediction. We use it without modification.

---

## 5. Preliminary Results

### 5.1 134.7M Parameter Model (JalekForCausalLM)

| Parameter | Value |
|-----------|-------|
| Architecture | Custom transformer (JalekForCausalLM) |
| Vocabulary size | 256 (byte-level) |
| Hidden size | 576 |
| Intermediate size | 1,536 |
| Layers | 38 |
| Attention heads | 9 (3 KV heads, GQA) |
| Max sequence length | 2,048 |
| Activation | SwiGLU |
| Position encoding | RoPE |
| Normalization | RMSNorm |
| Precision | bfloat16 |
| Tied embeddings | Yes |
| Total parameters | 134,671,680 |

The model has 38 transformer layers. Reducing the vocabulary from 49,152 (typical BPE) to 256 (byte-level) frees approximately 28 million parameters from the embedding layer. These parameters are reallocated to 8 additional transformer layers, increasing reasoning depth at the same parameter budget.

**Training configuration:**

| Parameter | Value |
|-----------|-------|
| Training data | 355.57 GB (FineWeb-Edu + Cosmopedia-v2 + Python-Edu), byte-encoded |
| Encoding table | ~23.4 million entries |
| Token budget | ~3 billion bytes (Chinchilla-optimal, 20:1 ratio) |
| Batch size | 128 |
| Learning rate | 1e-3, cosine decay |
| Warmup | 1,165 steps |
| Total optimizer steps | 11,652 |
| Optimizations | torch.compile, activation checkpointing (all 38 layers) |
| Hardware | NVIDIA RTX PRO 6000 Blackwell Server Edition (96 GB VRAM) |
| Training time | 6.5 hours |

**Results:**

| Metric | Value |
|--------|-------|
| Final loss (cross-entropy, nats) | 1.8464 |
| Best loss | 1.8257 |
| Perplexity | 6.21 |
| Peak throughput | 131,401 bytes/sec |

Note on interpretability: Perplexity values are not directly comparable across models with different tokenization schemes or vocabulary sizes (Mielke, 2019). These results are reported as intrinsic metrics for our encoding architecture. Direct comparison to BPE-tokenized models would require normalization to a common metric such as bits-per-byte on shared evaluation data, which is planned for future work.

### 5.3 Limitations of Current Results

1. The 134.7M model was trained on data encoded primarily as whole-word byte lookups with SOME morphologically decomposed byte sequences. We understand this is NOT a fully clean result based on what we've released for testing and research purposes. 

2. No standardized benchmark evaluations (MMLU, HellaSwag, ARC, etc.) have been conducted. These are planned for future work.

3. The core hypothesis — that morphologically decomposed encoding produces faster convergence and better reasoning than opaque whole-word encoding — has not yet been empirically tested in a controlled comparison. A direct comparison using the same model architecture and training data with morpheme-decomposed vs. opaque encoding is in progress.

---

## 6. Theoretical Framework

### 6.1 Concepts Are More Predictable Than Words

In subword-tokenized text, predicting the next token requires selecting from a vocabulary of 32,000–100,000+ options. The prediction space is broad because subword fragments carry no structural constraint on what can follow.

In morpheme-encoded text, predicting the next byte after a root morpheme requires selecting from a constrained set: derivational suffixes (~30 options), grammatical endings (~12 options), BOUNDARY, or SPACE. Morphological composition rules govern what can follow what, reducing the conditional entropy of the prediction task.

This is not merely a vocabulary size reduction. It is a structural change in the prediction problem. The transition probabilities in morpheme sequences are constrained by compositional rules that do not exist in subword sequences.

### 6.2 Table Translates, Model Reasons

All surface-level language complexity — slang, dialect, abbreviation, jargon, register variation — is handled by the encoding table. The table maps any input to the same clean morphological primitives. The model only ever sees these primitives.

This separation means model parameters are not spent on language comprehension. Every parameter is available for reasoning over compositional semantic structure. A smaller model with morphological encoding may achieve reasoning performance that currently requires much larger models operating on statistical subword fragments — though this claim awaits empirical validation.

---

## 7. Related Work

**Subword tokenization:** BPE (Sennrich et al., 2016), SentencePiece (Kudo & Richardson, 2018). Statistical decomposition optimized for compression, not semantic transparency.

**Byte-level models:** ByT5 (Xue et al., 2022), MegaByte (Yu et al., 2023), Byte Latent Transformer (Meta, 2024). These operate on raw bytes without pre-computed semantic structure, requiring larger models to learn character-level patterns. BLT demonstrated that byte-level models can match BPE model performance at scale.

**Esperanto morphological analysis:** Guinard (2016) achieved 98% segmentation accuracy on Esperanto words using n-gram Markov models. Bick (2016) constructed a morphological lexicon of 28,000 words verified against 17,000 roots.

**Chinchilla scaling:** Hoffmann et al. (2022). The 20:1 token-to-parameter ratio used in our training follows Chinchilla-optimal recommendations.

---

## 8. Future Work

1. Train a model on morphologically decomposed training data and compare loss curves directly to the semi-opaque-encoding baseline reported here.
2. Conduct standardized benchmark evaluations to enable comparison with existing models.
3. Develop normalized evaluation metrics (bits-per-byte on shared evaluation sets) for cross-architecture comparison.

---

## 9. Conclusion

Byte as Concept proposes that replacing statistical subword tokenization with dense morphological encoding changes the fundamental nature of the prediction task for language models. Morpheme sequences are structurally constrained by compositional rules, which should reduce the conditional entropy of next-byte prediction compared to statistically derived subword sequences.

Preliminary results show a 134.7M parameter model achieving a loss of 1.8257 on byte-encoded web data in 6.5 hours of training, and a 13.2M parameter model reaching a loss of 0.45 on byte-encoded proprietary mix of data within one epoch. These results are preliminary and were obtained on data that was primarily encoded as whole-word lookups with partial morphological decomposition.

The central claim — that full morphological decomposition produces measurably better training outcomes — is a testable hypothesis that we are actively investigating. We release all code, tables, and training logs to enable independent verification and extension.

---

## References

Bick, E. (2016). A Morphological Lexicon of Esperanto with Morpheme Frequencies. *Proceedings of LREC 2016.*

Guinard, T. (2016). An Algorithm for Morphological Segmentation of Esperanto Words. *The Prague Bulletin of Mathematical Linguistics*, 105(1), 63–76.

Hoffmann, J., et al. (2022). Training Compute-Optimal Large Language Models. *NeurIPS 2022.* arXiv:2203.15556.

Kudo, T., & Richardson, J. (2018). SentencePiece: A simple and language independent subword tokenizer and detokenizer for Neural Text Processing. *EMNLP 2018.*

Meta AI. (2024). Byte Latent Transformer: Patches Scale Better Than Tokens. arXiv:2412.09871.

Mielke, S.J. (2019). Can You Compare Perplexity Across Different Segmentations? https://sjmielke.com/comparing-perplexities.htm

Sennrich, R., Haddow, B., & Birch, A. (2016). Neural Machine Translation of Rare Words with Subword Units. *ACL 2016.*

Xue, L., et al. (2022). ByT5: Towards a Token-Free Future with Pre-trained Byte-to-Byte Models. *TACL.*

Yu, L., et al. (2023). MegaByte: Predicting Million-Byte Sequences with Multiscale Transformers. *NeurIPS 2023.*

Zamenhof, L.L. (1887). *Dr. Esperanto's International Language* (Unua Libro).

Zamenhof, L.L. (1894). *Universala Vortaro.*

---

**Corresponding author:** Travis Edward Holley, travis@tntholley.com

**Code and data availability:** The JalekCore encoding table, encoder/decoder implementation, model configurations, training scripts, and training logs are available at https://github.com/Laninthalesdran/Concept-as-Byte under CC-BY-NC-SA 4.0. We have provided both a 13.2M model and a 135M model for the sake of individual and group training. We discovered a 13.2M model, similar to what is provided, is capable of being trained on a home PC with a 4070 Ti Graphics card in a reasonable amount of time.

**Patent status:** U.S. Patent Application No. 64/017,122, filed March 25, 2026. Application undergoing preexam processing.
