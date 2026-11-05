# MAINTiDOC — Livrable 1 (SERRAY)

Assistant agentique multimodal de documentation de maintenance — domaine : **solaire (onduleurs + batteries de stockage)**,
marque fictive HelioNova. Équipe individuelle : SERRAY. Encadrante : Mme Mariam CHERRABI (EMSI-2026).

## Contenu de l'archive
| Élément | Description |
|---|---|
| `L1_MaintiDoc_SERRAY_Rapport.pdf` | Rapport (12 pages) : cadrage, corpus, architecture, flux et accès, risques, planning |
| `L1_MaintiDoc_SERRAY_LienGitHub.txt` | URL du dépôt GitHub (une ligne) |
| `L1_MaintiDoc_SERRAY_Corpus/inventaire.csv` | Inventaire : 50 lignes, 20 colonnes |
| `L1_MaintiDoc_SERRAY_Corpus/prompts_corpus.md` | Prompts d'IA et analyse critique des erreurs |
| `L1_MaintiDoc_SERRAY_Corpus/documents/famille_1` | 22 PDF — onduleurs |
| `L1_MaintiDoc_SERRAY_Corpus/documents/famille_2` | 21 PDF — batteries |
| `L1_MaintiDoc_SERRAY_Corpus/images/` | 7 photos de panneaux (comptées dans les 50 documents) |

## Corpus en bref
50 documents (43 PDF + 7 photos), 100 % synthétiques, aucune licence tierce. Contient 2 PDF scannés, 2 situations
contradictoires (bulletin vs manuel ; versions obsolètes), 1 document avec injection, 3 groupes d'accès
(`grp_installateurs`, `grp_sav`, `grp_engineering`), 43 documents à éléments visuels. 15 autres photos de test existent
dans le dépôt (`eval_images/`), hors corpus.

## Reproduire
Le corpus est généré par `scripts/generate_corpus.py` du dépôt (`python -m scripts.generate_corpus`), puis validé par
`corpus_inventory.check_inventory`. Pas de secret dans l'archive ; `.env` est ignoré par git.

## Limites
- Le prototype de recherche utilise des embeddings de test (sans GPU) ; BGE-M3, Qwen2.5-VL, Docker et les services réels
  seront validés sur Google Colab (PC : 16 Go RAM, pas de GPU NVIDIA).
- Les images sont dessinées par code. La relecture humaine du corpus (`verifie_par`) reste à compléter.
