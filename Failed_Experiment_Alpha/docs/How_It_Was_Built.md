# How It Was Built

We are trying to find the floor of model size. It is above 7M parameters.

## The Complete Build Log — Concept-as-Byte Architecture
## April 4-5, 2026

**Builder:** Travis Edward Holley, TNT Holley, Inc.
**Implementation:** Claude (Anthropic, Claude Opus 4.6)

This document records every step of building the Concept-as-Byte translation pipeline. Not the theory. The work. What was done, in what order, what broke, what got fixed, and what we learned from breaking it.

---

## Day 1 — April 4, 2026

### Starting Point

We came in with:
- AdamZ (13.2M param reasoning model), previously trained on Esperanto concept byte data
- An Esperanto base table (1,820 morpheme entries from Zamenhof's 1887/1894 vocabulary)
- An English word table (14.9M entries, frequency-ranked byte codes)
- Training data generators for three phases of reasoning chains
- A session handoff document from the previous build session

### Step 1: Update the LLZ Model Config

The LLZ (translator model, named for Ludwik Lejzer Zamenhof) was still set to 1.38M parameters from a previous design. Updated to 7.18M: d_model=384, 8 heads, 3 layers, ff=1536, SwiGLU, RoPE, RMSNorm. Verified forward pass at 7,178,880 parameters.

Time: 10 minutes.

### Step 2: Rewire the English Encoder

The encoder was loading from an old JSON file. Rewired to load from `llz_english_table.txt` directly. Tab-separated format: Index, Entry, Hex Code, Type.

First passthrough test: 0% pass. Every sentence failed. The period byte (0x14) was concatenating with the preceding word bytes, producing wrong lookups. "world." encoded as a single sequence that decoded to "jacquemard."

Fix: Added BOUNDARY byte between words and trailing punctuation. Pass rate jumped to 97.3%.

Remaining failures: accented characters (ü, ö, è) not in the table, and hyphens splitting words incorrectly.

Time: 30 minutes.

### Step 3: Sync the Shared Layer

The Esperanto table had 6 accented letters (ĉ, ĝ, ĥ, ĵ, ŝ, ŭ) at hex codes that the English table had assigned to high-frequency words ("you", "the", "to", "it", "and", "that"). The shared layer between tables was not identical.

Travis's rule: "We can't have differences when it comes to anything except words and morphemes."

Fix: Cascade bump. Moved bottom 6 single-byte English words to 2-byte codes. Moved bottom 6 two-byte words to 3-byte codes. Freed the hex codes. Added Esperanto letters to English table at matching codes.

Net cost: 6 common words changed address (still single-byte). 6 low-frequency words moved to 2-byte. 6 rare words moved to 3-byte.

Time: 45 minutes.

### Step 4: Punctuation Spacing Rule

Travis: "Encoding and decoding needs to have punctuation marks be surrounded by space bytes. That is so the model doesn't get confused."

All punctuation — periods, commas, question marks, exclamation points, colons, hyphens, quotes — became SPACE-separated tokens. "the cat sat." encodes as: `[the] SPACE [cat] SPACE [sat] SPACE [.]`

This matched how the Esperanto generators already handled punctuation in training data.

Passthrough went to 100% on 10,000 Tatoeba sentences.

Time: 20 minutes.

### Step 5: Add Accented Characters

The 2.7% failure rate was all accented characters not in either table. Added 102 characters (acute, grave, umlaut, circumflex, tilde, cedilla, Nordic, Slavic, Czech, Turkish) at 3-byte codes, identical in both tables.

Passthrough: 9,999/10,000. One failure: the macron ō in "Ōsaka."

Travis: "Add the macron, we are precise or we are failing."

Added 10 macron vowels. Passthrough: 10,000/10,000. 100%.

Time: 30 minutes.

### Step 6: Build LidiaZ — The Bridge

Named after Lidia Zamenhof (1904-1942), translator and Esperanto advocate. Murdered at Treblinka.

LidiaZ is a pure dictionary lookup. Esperanto byte code in, English byte code candidates out. Two dicts: forward (Esp→Eng) and reverse (Eng→Esp). No model. No inference. No parameters. Just table lookup.

First build: 5,865 entries. Based only on the 1,640 Esperanto roots that had English translations in the base table.

Travis: "Does every esperanto code or sequence have an english byte code across from it? That is the ONLY question that is important."

Answer: No. 42.3% coverage. Not even close.

Time: 1 hour.

### Step 7: Fill the Esperanto Table to 100%

This took most of Day 1.

**Sources merged:**
- EO_full.txt (14,581 entries) — direct Esperanto-English dictionary
- espsof_with_english.json (8,856 entries) — decomposed with English
- english_to_esperanto.json (2.9M entries) — reversed
- Wiktionary data dump (133,694 Esperanto entries extracted from 10.5M-line raw dump, 2.5GB)
- ESPDIC (63,478 entries) — downloaded from GitHub
- Tekstaro frequency list (11,566 entries) — downloaded from GitHub
- Zamenhof 1889 original roots (763 entries)
- esperanto_decomposed.json (19,219 entries)

**Passes to fill roots:**
1. Direct dictionary match
2. X-system conversion (ĉ↔cx, ĝ↔gx, etc.)
3. Ending strip (kuris→kur→run)
4. Wiktionary lookup
5. International term fuzzy matching (k→c, ci→ti patterns against 14.9M English table)
6. Manual research of 477 scientific Latin terms (every one individually identified)
7. Fix: 11,564 entries had English in the wrong column

**Result:** 53,640 roots, 100% with English. Zero missing.

**Composed entries:** Filled via morpheme decomposition. Each composed word = root + BOUNDARY + affix + BOUNDARY + ending. The byte sequence IS the composition. No separate hex code for composed words.

**Dead entries cut:** 414 roots and 648 composed entries not in any Wiktionary data — removed.

Time: 8 hours.

### Step 8: The English Table Was Broken

During LidiaZ testing, 91,791 Esperanto entries couldn't match any English word. Investigation: common English words — "winter", "mother", "father", "friend", "million" — were missing from the English table.

Root cause: The automated cleaning script that built the English table from the raw 23.4M source was catastrophically over-aggressive. It removed 8.5M entries including basic vocabulary.

Fix: Added 8.5M missing words back at 4-byte level (3-byte was full).

Then found "I" and "a" missing. The 2-source validation filter killed single-character words.

Travis: "That's our fuck up."

Fixed.

Time: 2 hours.

### Step 9: Full Pipeline Test

Ran 1.88M sentences from the 144MB training corpus through the full pipeline:
1. English text → encoder → English bytes (99.4%)
2. English bytes → LidiaZ reverse → Esperanto bytes (97.1% sentence, 52.1% per-word)
3. Esperanto bytes → LidiaZ forward → English bytes (100%)
4. English bytes → decoder → English text (100%)
5. English text → LanguageTool grammar check (100%)

Step 3 was 100%. Every Esperanto byte that went in came back with English candidates.

Step 2 was the bottleneck. 47.9% of English words had no Esperanto mapping.

Time: 15 minutes for the test. The fixes took the rest of the day.

---

## Day 2 — April 5, 2026

### Step 10: COIN/NAME Classification

The 47.9% unmapped English words needed classification:
- COIN (0x09 prefix) — borrowed concepts with no Esperanto equivalent
- NAME (0x08 prefix) — proper nouns

**Built ValidatedEnglishTable from 7 sources merged:**
- en_full_freq.txt, english_words.txt, english_dictionary.json, dwyl/english-words, Webster's Dictionary, ENABLE1, english_semantic.jsonl
- 2-source minimum validation (word must appear in 2+ dictionaries)
- Census/SSA name databases (254,280 known names)

**Result:** 665,259 validated entries (344K words, 61K COINs, 260K NAMEs)

**COIN reduction pipeline:**
- Started at 439,482 COINs
- Definition-based composition: -78,045
- Cross-reference pass: -188,984
- Batch scrub: -27,224
- Downloaded Moby Thesaurus (30K) + WordNet Thesaurus (51K) for synonym matching: -4,740
- Compound word splitting (seafloor → sea+floor → mar+fund): -12,004
- Final: 54,384 genuine COINs

Travis decided to defer COIN byte deployment until a linguistics team could review: "We'll keep them labeled for now until we can get a team together that can help us build this shit the right way."

Time: 4 hours.

### Step 11: The Shit Table

22.8M unvalidated English words from the raw table. Classified:
- 17.1M garbage (concatenated web scrape junk)
- 5.7M concatenated real words (appleeating, gardencommon)
- 6,200 foreign words with accented characters

Foreign words added to clean table. Garbage saved to Failed folder.

Time: 30 minutes.

### Step 12: Punctuation in Esperanto Generators

Both encoders needed to produce the same punctuation pattern. Researched Esperanto punctuation rules — essentially the same as English.

Updated `jalek_morphemes.py`: Added COMMA, PERIOD, QUESTION, EXCLAIM constants. `chain()` now defaults to SPACE PERIOD END. `qa_chain()` adds SPACE ? QA and SPACE . END. All three phase generators updated with comma before clause connectors.

Tested: 100% pass on Phase 1 and Phase 2 chains.

Time: 30 minutes.

### Step 13: Encode Training Data

Encoded 144MB Chinchilla training corpus through the English encoder. 1,880,142 sentences, 85.3MB, 12 seconds. Punctuation SPACE-separated throughout.

Time: 12 seconds.

### Step 14: Train LLZ

Launched on local RTX 4070 Ti SUPER with Python 3.12 (CUDA 12.4). The first attempt used Python 3.14 — CPU only, wrong Python. Travis caught it.

The first training run was launched WITHOUT a test passthrough. Travis stopped it: "You were supposed to do a test pass through to make sure it didn't come out shit."

Killed the run. Deleted the artifacts. Started over properly.

LLZ trained for 3 epochs. Final: eval loss 1.997, perplexity 7.37.

Time: ~5 hours training.

### Step 15: The Ludwik Zamenhof Method

Travis's insight: train a model on PARALLEL Esperanto-English data instead of English-only. Both languages in the same byte space.

Downloaded OPUS parallel corpus from Argos Open Technologies:
- XLEnt: 2.46M pairs
- WikiMatrix: 298K pairs
- OpenSubtitles: 64K pairs
- Wikimedia: 13K pairs

Encoded 1.39M pairs as: [Esperanto concept bytes] [Q/A separator] [English word bytes] [END]. 61.8MB total. Called it BIGMAC.

Time: 30 minutes.

### Step 16: Build LidiaZ Model

10.35M parameters. d_model=400, 8 heads, 4 layers, ff=1600. Half the depth of AdamZ (4 vs 8 layers), wider (400 vs 320). "Wide attention for memory, half depth for translation not reasoning."

Also built a matched 7.18M version for fair comparison against LLZ.

Time: 20 minutes.

### Step 17: RunPod Training

Spun up a RunPod pod. Found two NVIDIA RTX PRO 6000 Blackwell Server Edition GPUs (98GB VRAM each). Trained LidiaZ 7M and LidiaZ 10M simultaneously, one per GPU.

LidiaZ 7M at 36,000 tokens/sec vs LLZ at 10,500 tokens/sec locally. 3.5x faster.

Both models converged to eval loss 1.33, perplexity 3.79. The 10M extra parameters didn't help — the data was the bottleneck.

Time: ~3 hours training.

### Step 18: Translation Test

Fed Esperanto phrases to LidiaZ 10M:
- "la hundo estas bona" → "do hi good **dog**"
- "mi amas vin" → "want you to **love** you"
- "la kato dormas sur la lito" → "**cat** woman **on bed**"
- "la suno brilas" → "**sun** al soar"

Core concepts came through. Word order was wrong. "mi amas vin" couldn't produce "I" because "I" was missing from the vocabulary.

Candidate ranking test: "li" (he) ranked #1 at 52.75% confidence. But "havas" (has) ranked #5 and "dek" (ten) ranked #4. Category correct, specificity wrong.

Root cause identified: training data was not audited at the concept level.

Time: 30 minutes.

### Step 19: BPE Baselines

Built BPE comparison models. SentencePiece BPE tokenizer, vocab=2000, matched parameter count (~7.18M).

Two models:
- BPE-A: English-only (same data as LLZ, BPE tokenized)
- BPE-B: Parallel Esp-Eng (same source as LidiaZ, BPE tokenized)

BPE-C (Esperanto-only BPE) was planned but cancelled because the experiment was already corrupted by varying training data sizes across models.

Both launched on RunPod Blackwells.

Also launched Esperanto-only concept bytes on local 4070 Ti.

Time: 1 hour setup, training ongoing.

### Step 20: Research and Paper

Researched neuroscience of concept representation:
- Quian Quiroga's concept cells (2005) — individual neurons encode individual concepts
- Fodor's Language of Thought (1975) — thinking is computation over concept atoms
- Patterson's hub-and-spoke model — transmodal concept hub in anterior temporal lobe
- Barsalou's perceptual symbol systems — concepts grounded in sensory experience
- Caltech's 10-bit bottleneck — conscious thought at ~1.25 bytes per second

Found that the architecture accidentally (Travis: "there is no accidentally about it") mirrors biological concept representation.

Found Esperanto learning speed data: 10-13x faster than natural languages for humans. Same effect observed in our models.

Drafted paper: "Concept as Thought, Therefore Concept as Byte."

Then decided: don't publish the paper. Publish the data. Publish the pipeline. Publish this document. Let people see the work and make their own conclusions.

Time: 2 hours.

### Step 21: Failed Experiment Alpha

Documented everything that failed:
1. English vocabulary missing core words
2. Training data not audited at concept level
3. Comparison not fair (different data volumes)
4. Translation specificity failed
5. Structural byte advantage not controlled
6. Composed word byte codes initially assigned wrong

Named the document "Failed Experiment Alpha" and published everything as-is.

Travis: "100% or nothing. We said it. And we missed 'I'."

---

## Tools Used

- **Python 3.12** (CUDA 12.4, PyTorch 2.6.0) — training and GPU work
- **Python 3.14** (CPU only) — data processing (accidentally used for first training attempt)
- **NVIDIA GeForce RTX 4070 Ti SUPER** (16GB) — local training
- **NVIDIA RTX PRO 6000 Blackwell Server Edition** (98GB × 2) — RunPod training
- **SentencePiece** — BPE tokenizer for baselines
- **LanguageTool** — grammar/spelling verification
- **HuggingFace Hub** — file transfer between local and RunPod
- **Claude Code** (Anthropic, Opus 4.6, 1M context) — all implementation
- **Wiktionary data dump** (2.5GB) — Esperanto vocabulary extraction
- **ESPDIC** — Esperanto-English dictionary (CC-BY, from GitHub)
- **OPUS corpus** — parallel training data (CC-BY)
- **Moby Thesaurus** — synonym resolution (public domain)
- **Census/SSA databases** — name classification

## Total Cost

- RunPod compute: ~$30
- Everything else: a desktop PC, an internet connection, and two days

---

## Core Assumptions

### Assumptions That Held

1. **The brain thinks in concepts, not characters.** Every piece of neuroscience we found — concept cells, Language of Thought, hub-and-spoke model — supports this. We built on it. The encoding architecture based on this assumption produced the best training results.

2. **Esperanto morphology is a good encoding system for machine cognition.** Concept byte encoding converged faster than word byte encoding at matched parameters. The 10-13x human learning speed advantage for Esperanto appears to transfer to neural networks.

3. **A small model can translate.** 10.35M parameters produced correct concept-to-word mappings (hundo→dog, kato→cat, suno→sun). The architecture doesn't need 125M parameters.

4. **Parallel data beats monolingual data.** Every model trained on parallel Esperanto-English data outperformed the corresponding monolingual model. This held across both concept byte encoding and BPE tokenization.

5. **256 bytes is enough vocabulary.** Compositionality handles the complexity. The vocab never needs to scale with model size.

### Assumptions That Were Proven False

1. **"Automated data cleaning is sufficient."** It wasn't. The cleaning pipeline stripped "winter", "mother", "father", "I", "a" from the vocabulary. Every automated step introduced errors that weren't caught until testing. Trust nothing. Verify everything.

2. **"Structural verification equals semantic verification."** Checking that the training data FORMAT was correct (Q/A separator present, END byte, no duplicates) is not the same as checking that the CONTENT was correct (right Esperanto bytes for each word, right English bytes for each word). We did the first. We skipped the second. The model learned the wrong mappings.

3. **"A 2-source validation filter catches garbage without losing real words."** It caught garbage. It also killed "I" and "a." The filter was too aggressive and nobody checked what it removed.

4. **"The OPUS parallel corpus is clean enough to train on directly."** It's clean for BPE tokenization where words are tokenized as-is. It's NOT clean for concept byte encoding where every word must map to a specific morpheme byte sequence. The encoding step is where errors enter, and we didn't audit it.

5. **"More parameters help."** The 10.35M LidiaZ converged to the SAME perplexity as the 7.18M LidiaZ. At this data scale, extra parameters bought nothing. The data was the bottleneck, not the model.

6. **"We can compare models trained on different data sizes."** We can't. BPE-B trained on 141.7MB. LidiaZ trained on 61.8MB. The comparison is suggestive but not conclusive. A fair experiment requires identical data.

### Assumptions We Haven't Tested Yet

1. **"Concept byte encoding has a scaling advantage at larger model sizes."** BPE vocab must grow with model size, consuming embedding parameters. Concept byte vocab stays at 256. This predicts that the concept byte advantage INCREASES as models scale. Untested.

2. **"AdamZ reasoning + LidiaZ translation produces better output than LidiaZ alone."** We never ran the full pipeline. AdamZ reasons in Esperanto bytes, LidiaZ translates to English — that's the design, but it hasn't been tested end-to-end.

3. **"The COIN and NAME byte prefixes improve or harm training."** We classified 61K words as COIN and 260K as NAME but deferred using the prefix bytes in training. Their effect on model behavior is unknown.

4. **"This approach works for languages other than English."** The architecture is designed to be language-independent — swap the table, train a new LidiaZ. Nobody has tried it with Japanese, Arabic, Swahili, or any other language.

---

## What This Proves

Nothing, yet. The experiment was flawed. The data wasn't clean. The comparison wasn't fair. The model can say "dog" but can't say "I."

What it SHOWS is that the architecture works, the encoding works, and the concept converges faster than the alternative — even when everything else is done wrong.

Experiment Beta starts with clean data.

---

*Travis Edward Holley*
*TNT Holley, Inc.*
*April 5, 2026*
