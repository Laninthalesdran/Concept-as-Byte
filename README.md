# Concept-as-Byte

Dense morphological byte encoding for language model training.

**Author:** Travis Edward Holley
**License:** CC-BY-NC-SA 4.0
**Patent:** U.S. Application No. 64/017,122 (filed March 25, 2026)
**DOI:** 10.5281/zenodo.19390531

---

**Note:** We apologize in advance for the relatively crude nature of the tools offered in this release. This is an early-stage research project and we are actively working toward providing updated and more polished tools. What you see here is functional but not production-ready. We appreciate your patience and interest.

---

## What This Is

Concept-as-Byte is an encoding architecture that replaces subword tokenization (BPE, WordPiece, SentencePiece) with dense morphological byte encoding. Each byte represents a complete semantic concept — a root, affix, grammatical marker, or control signal — rather than a statistical subword fragment.

The morpheme inventory is drawn from Zamenhof's Esperanto system (1887-1894). The encoded form is called Jalek.

## The Zamenhof Family

This project honors the family of **Ludwik Lejzer Zamenhof** (1859-1917), creator of Esperanto — a language designed from first principles for universal communication and peace. Zamenhof was a Polish-Jewish physician who grew up in Białystok watching four ethnic groups divided by language and prejudice. He spent his life building a bridge between peoples through a neutral, composable language that anyone could learn. He was nominated 12 times for the Nobel Peace Prize and UNESCO selected him as an eminent personality of 2017.

All three of Zamenhof's children were murdered by the Nazis during the Holocaust. Hitler specifically named Esperanto in *Mein Kampf* as a tool of Jewish conspiracy. The Gestapo received specific orders to hunt Zamenhof's descendants. His daughter Zofia, a physician, chose to accompany her young patients to Treblinka rather than save herself.

138 years after Zamenhof created his language, it forms the morphological foundation of this AI architecture. His family's names live on in the components of a system designed to reason and serve all entities equally.

For more on Zamenhof's life and vision: [Zamenhof, Esperanto, and the Crusade for Peace Through Language](https://notesfrompoland.com/2019/12/18/ludwik-zamenhof-esperanto-and-the-crusade-for-peace-through-language/)

The components of this system are named in their honor:

| Name | Component | Named After |
|------|-----------|-------------|
| **LLZ** | Translator model (coming soon) | **Ludwik Lejzer Zamenhof** — creator of Esperanto |
| **AdamZ** | 13.2M reasoning model | **Adam Zamenhof** — his son, physician, shot by Nazis 1940 |
| **LidiaZ** | Bridge/lookup between AdamZ and LLZ | **Lidia Zamenhof** — his daughter, murdered at Treblinka 1942 |
| **.ZofiaZ** | Encoded file format (coming soon) | **Zofia Zamenhof** — his daughter, physician, chose to accompany her young patients to Treblinka 1942 |
| **KlaraZ** | Orchestrator/functionary program (in design) | **Klara Zilbernik-Zamenhof** — his wife |

## What's Included

| File / Folder | Description |
|---------------|-------------|
| **Concept-as-Byte_Preprint.pdf** | Technical preprint |
| **Concept-as-Byte_Preprint.md** | Preprint source |
| **JalekCore_Base_Table.txt** | Encoding table (1,753 morpheme entries) |
| **jalek_encoder.py** | Encoder/decoder (pure table lookup) |
| **adamz.py** | AdamZ — 13.2M parameter reasoning model definition |
| **lightweight.py** | Lightweight model definition |
| **jalek_135m_model.py** | 134.7M parameter benchmark model definition |
| **train_lightweight.py** | Training script |
| **benchmark_135m_config.json** | 135M model configuration |
| **benchmark_135m_training_log.jsonl** | Step-by-step training metrics |
| **benchmark_135m_training_output.log** | Full training console output |
| **3D_Encoding_Idea.md** | Positional bytes for spatial/causal/temporal relationships between concepts |
| **Licensing_Royalty_Rate_Cap.md/.pdf** | Public licensing terms — 5% royalty cap, negotiable lower |
| **LICENSE** | CC-BY-NC-SA 4.0 |

### Jalekon/ — AI-Native Programming Language

The first programming language designed for AI to write and compilers to execute. Each byte is a programming concept (`function`, `if`, `return`, `+`). The prototype compiler takes Jalekon byte programs and compiles them to native executables via LLVM.

| File | Description |
|------|-------------|
| **jalekon_compiler.py** | Working prototype compiler — Jalekon bytes → LLVM IR → native executable |
| **JALEKON_DESIGN.md** | Language design document |
| **Jalekon_Byte_Table.md** | Complete v0 byte table — 248 single-byte programming concept codes |
| **Jalekon_Byte_To_Execution.md** | Complete trail from byte to CPU instruction with code at every stage |
| **Jalekon_Compiler_Architecture.md** | Compiler research — LLVM, bootstrapping, platform targets |
| **Jalekon_Prior_Art.md** | Historical context — APL, Forth, Lua, WebAssembly |
| **Jalekon_Open_Questions.md** | Design questions for future development |
| **test_add.ll** | Sample LLVM IR output |
| **README.md** | Quick start guide |

### ProjectSuperZ/ — 4D Positional Concept Encoding

24 positional bytes replace all Zamenhof affixes and grammatical endings. Grammar is geometry: composition (X), hierarchy (Y), causation (Z), time (T). 59 base bytes + 24 positional bytes = the entire system. 197 root slots produce 4,925+ derived concepts through position alone.

| File | Description |
|------|-------------|
| **Positional_Derivation_Table.md** | Complete 4D byte system — numbers, punctuation, alphabets, grammar, roots |
| **Root_Derivation_Analysis.md** | How 197 roots absorb 800+ Zamenhof roots through positional derivation |

### PROJECTMATHLETE/ — Math-Only Model

A model trained exclusively on mathematics using prefix notation. Each math operator is a single byte with known arity, narrowing prediction space at every position.

| File | Description |
|------|-------------|
| **MATHLETE_DESIGN.md** | Architecture and design document |
| **MATH_OPERATOR_RESEARCH.md** | Complete enumeration of mathematical operators |
| **Mathlete_Byte_Table.md** | Byte table with operator assignments |

### KNOWNISSUES/ — Discovered Problems and Proposed Solutions

| File | Description |
|------|-------------|
| **Discovered_Issue_With_Byte_Connection.md** | Multi-byte codes create false adjacency patterns (hallucination risk) |
| **Possible_Solution_COIN_Byte_Inclusion.md** | COIN as universal root marker — fixes noise AND preserves instrumentation |
| **Possible_Solution_COIN_As_Letter_Boundary.md** | COIN between every letter to eliminate all adjacency noise |
| **Possible_Solution_Triple_Hex_Vocabulary.md** | 4096-token vocabulary — REJECTED (shortcuts learning) |

### TNT_Holley_Inc/ — Corporate IP Separation

| File | Description |
|------|-------------|
| **Separation_of_Corporation_from_IP.md** | Patent is personal IP, not corporate. Company operates under non-exclusive license. |

### Island_of_Misfit_Toys/ — Failed Experiments

Previous approaches that didn't work. Kept for reference and honesty.

## Coming Soon

**The LLZ (Translator):** A context-aware translation model that bridges English and Jalek byte encoding. The LLZ holds the original English input in reserve and uses it alongside AdamZ's Jalek byte output to select the contextually correct English translation. Trained using Positive Preference Training (PPT) — no punishment signals, only positive demonstrations of correct translations. Named after Ludwik Lejzer Zamenhof.

**The .ZofiaZ Format:** Encoded data files will use the `.ZofiaZ` extension — honoring Zofia Zamenhof, who chose to stay with her patients. The encoded data stays with the model, just as Zofia stayed with those who needed her.

**LidiaZ:** The bridge between AdamZ and the LLZ. Takes each Esperanto byte code from AdamZ, looks up all possible English word translations, and provides the full candidate list to the LLZ as byte codes. No reasoning — pure table lookup fan-out. The LLZ then selects the contextually correct English word from the candidates. Named after Lidia Zamenhof, who bridged languages and cultures as a translator and Esperanto advocate.

**KlaraZ:** The functionary program that manages multiple models and interfaces between the reasoning model, the translator, and external programs. The orchestrator that holds the family together. Named after Klara Zilbernik-Zamenhof.

## Important Note

The encoder provided (`jalek_encoder.py`) operates on the JalekCore Base Table only. It encodes individual Esperanto morphemes to byte codes.

**It does NOT support automatic morphological decomposition of English words.** If you input "hospital", it will not decompose it into `mal·san·ul·ej·o`. The English-to-Esperanto morpheme decomposition pipeline is not included in this release. The LLZ translator will handle this when available.

## Links

- **Zenodo:** https://zenodo.org/records/19390531
- **GitHub:** https://github.com/Laninthalesdran/Concept-as-Byte

## Commercial Use

This work is released under CC-BY-NC-SA 4.0 for non-commercial use.

**Commercial licensing** available at no more than 5% of gross revenue derived from products or services using the patented method. Contact travis@tntholley.com. Statement made April 5, 2026. Further reduction of royalty through negotiation is welcomed.

**Clarification of rights:** The CC-BY-NC-SA 4.0 license applies to the published materials (paper, code, table). Implementation of the patented method (U.S. Application No. 64/017,122) for commercial purposes requires a separate commercial license regardless of the publication license.
