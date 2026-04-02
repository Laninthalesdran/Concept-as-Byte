# Concept-as-Byte

Dense morphological byte encoding for language model training.

**Author:** Travis Edward Holley
**License:** CC-BY-NC-SA 4.0
**Patent:** U.S. Application No. 64/017,122 (filed March 25, 2026)
**DOI:** 10.5281/zenodo.19390531

## What This Is

Concept-as-Byte is an encoding architecture that replaces subword tokenization (BPE, WordPiece, SentencePiece) with dense morphological byte encoding. Each byte represents a complete semantic concept — a root, affix, grammatical marker, or control signal — rather than a statistical subword fragment.

The morpheme inventory is drawn from Zamenhof's Esperanto system (1887-1894). The encoded form is called Jalek.

## What's Included

| File | Description |
|------|-------------|
| Concept-as-Byte_Preprint.pdf | Technical preprint |
| Concept-as-Byte_Preprint.md | Preprint source |
| JalekCore_Base_Table.txt | Encoding table (1,753 morpheme entries) |
| jalek_encoder.py | Encoder/decoder (pure table lookup) |
| lightweight.py | 13.2M parameter Lightweight model definition |
| jalek_135m_model.py | 134.7M parameter model definition |
| train_lightweight.py | Training script |
| benchmark_135m_config.json | 135M model configuration |
| benchmark_135m_training_log.jsonl | Step-by-step training metrics |
| benchmark_135m_training_output.log | Full training console output |
| LICENSE | CC-BY-NC-SA 4.0 |

## Important Note

The encoder provided (`jalek_encoder.py`) operates on the JalekCore Base Table only. It encodes individual Esperanto morphemes to byte codes.

**It does NOT support automatic morphological decomposition of English words.** If you input "hospital", it will not decompose it into `mal·san·ul·ej·o`. The English-to-Esperanto morpheme decomposition pipeline is not included in this release.

## Links

- **Zenodo:** https://zenodo.org/records/19390531
- **GitHub:** https://github.com/Laninthalesdran/Concept-as-Byte

## Commercial Use

This work is released under CC-BY-NC-SA 4.0 for non-commercial use. Commercial licensing is available by contacting: travis@tntholley.com
