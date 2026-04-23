# Concept-as-Byte

Dense morphological byte encoding for language model training.

**Author:** Travis Edward Holley
**License:** CC-BY-NC-SA 4.0
**Patent:** U.S. Application No. 64/017,122 (filed March 25, 2026)
**DOI:** 10.5281/zenodo.19390531

---

**Note on the author:** Travis Edward Holley is an independent researcher and U.S. Navy veteran, not an academic. He holds no PhD and has no university affiliation. This work was conducted independently using personal hardware, a RunPod GPU rental, and Claude (Anthropic) as a collaborative partner. The methods, formatting, and experimental style reflect that background — they are functional and honest, not polished to academic convention. The results are reproducible, the code is public, and the limitations are documented. If something looks rough, it probably is. If something looks wrong, open an issue.

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

---

## Commercial Use

This work is released under CC-BY-NC-SA 4.0 for non-commercial use.

### Licensing Royalty Rate Cap

**Date:** April 5, 2026
**Patent Holder:** Travis Edward Holley
**Contact:** travis@tntholley.com

Commercial licensing for implementation of the patented Concept-as-Byte method is available at **no more than 5% of gross revenue** derived from products or services using the patented method.

Further reduction of royalty through negotiation is welcomed.

### Intent

This royalty cap is set deliberately low. The purpose of this patent is to prevent the method from being locked behind proprietary walls — not to extract maximum revenue from its use.

Organizations and individuals operating in non-commercial, educational, humanitarian, or research contexts may use the published materials freely under the CC-BY-NC-SA 4.0 license without any royalty obligation.

For commercial use, the 5% cap represents a ceiling, not a floor. The patent holder welcomes negotiation toward lower rates, particularly for:

- Small businesses and independent developers
- Organizations serving underserved or developing communities
- Open-source projects that make their implementations publicly available
- Applications in healthcare, education, infrastructure, or public safety

### Non-Commercial Use

All published materials — including the preprint, source code, encoding tables, and model architectures — are released under **CC-BY-NC-SA 4.0** for non-commercial use. No royalty or license is required for non-commercial applications.

**Clarification of rights:** The CC-BY-NC-SA 4.0 license applies to the published materials (paper, code, table). Implementation of the patented method (U.S. Application No. 64/017,122) for commercial purposes requires a separate commercial license regardless of the publication license.

*This document constitutes a public, binding statement of licensing terms by the patent holder.*

*Travis Edward Holley*
*April 5, 2026*
