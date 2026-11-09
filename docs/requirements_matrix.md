# Matrice des exigences — MAINTiDOC

Sources : `Projet_IA_Générative_Multi_Modale_V2.pdf` (réf. principale, « PDF §n »), `Feuille_de_route_MAINTiDOC.docx` (« FR »), prompt maître (« PM §n »).
Priorités : **P0** indispensable à la démo, **P1** important, **P2** si temps/matériel.
Statuts : Terminé et vérifié · Implémenté, tests incomplets · En cours · Non implémenté · Bloqué.

État au démarrage : aucune exigence n'était implémentée. Les statuts des tableaux ci-dessous ont été mis à jour le 2026-11-09 d'après le journal en bas de page ; les lignes encore « Non implémenté » ne sont pas commencées (agent, MCP, API, interface, VLM, sécurité côté outils, MLflow, Docker réel).

## Fonctionnelles

| ID | Exigence | Source | Prio | Module cible | Test / preuve prévus | Statut |
|---|---|---|---|---|---|---|
| F-01 | Questions techniques en français | PDF §1, PM §2 | P0 | api/routes/query | tests/api | Non implémenté |
| F-02 | Question + photographie | PDF §1,14 | P0 | api/routes/query_multimodal, services/multimodal | tests/e2e #5 | Non implémenté |
| F-03 | Réponse sourcée (doc, version, page, élément) | PDF §4.2 | P0 | services/answer_generation | tests/unit citations | Implémenté (document, version, page, élément) |
| F-04 | Consultation historique via MCP | PDF §6 | P0 | mcp/tools | tests/e2e #11 | Non implémenté |
| F-05 | Consultation tickets ouverts via MCP | PDF §6 | P0 | mcp/tools | tests/e2e #12 | Non implémenté |
| F-06 | Brouillon de ticket | PDF §1,6 | P0 | services/ticketing | tests/e2e #13 | Non implémenté |
| F-07 | Création de ticket après approbation humaine explicite | PDF §6 | P0 | agents/graph, mcp | tests/e2e #15 | Non implémenté |
| F-08 | Clarification / abstention (photo illisible, pas de source, contradiction, risque hors rôle) | PDF §8 | P0 | agents/nodes | tests/e2e #6,7,8 | Partiel : abstention et clarification implémentées ; défauts connus (voir docs/eval_150_corrections.md) |
| F-09 | Distinction faits sourcés / observations visuelles / hypothèses / inconnus | PDF §8, PM §2 | P0 | schemas, frontend | tests/unit + revue UI | Non implémenté |
| F-10 | Pas de % de confiance inventé par le modèle | PDF §8 | P0 | schemas, prompts | test schéma (champ absent) | Terminé et vérifié (champ `confidence` refusé par le schéma) |
| F-11 | Sortie structurée Pydantic (status, answer, citations, uncertainties, clarification_question, proposed_action) | PDF §7 | P0 | schemas/answer | tests/unit | Implémenté (schéma Pydantic, tests) |
| F-12 | Interface Streamlit (chat, photo/PDF, citations, brouillon, confirmation) | PDF §3, FR P8 | P1 | frontend | tests/e2e + revue manuelle | Non implémenté |
| F-13 | Endpoints API listés PM §11 | PM §11 | P0 | api | tests/api | Non implémenté |

## Corpus, ingestion, RAG

| ID | Exigence | Source | Prio | Module cible | Test / preuve prévus | Statut |
|---|---|---|---|---|---|---|
| D-01 | Corpus 30–50 documents autorisés/synthétiques, 2 familles d'équipements | PDF §2 | P0 | data/samples, scripts | inventaire corpus | Terminé : 50 documents (43 PDF + 7 photos), inventaire validé, relecture humaine par sondage |
| D-02 | Métadonnées par doc (id, version, statut, famille, groupes d'accès, provenance) | PM §6 | P0 | database | tests/unit | Implémenté (SQLite ; PostgreSQL non validé), tests unitaires |
| D-03 | Ingestion PDF numériques (PyMuPDF), détection pages scannées | PDF §4.1 | P0 | services/ingestion | e2e #1 | Implémenté, tests incomplets (tests/unit/test_ingestion.py, 10 tests OK sur corpus synthétique) |
| D-04 | OCR local pour scans | PDF §3,4.1 | P1 | services/ingestion | e2e #2 | Implémenté : OCR français (`fra`), 2 scans du corpus |
| D-05 | Extraction tableaux et figures avec page + element_id | PDF §4.1 | P0 | services/ingestion | e2e #3 | Implémenté, tests incomplets (tableaux + légendes de figures ; indexation d'image à faire) |
| D-06 | Ingestion idempotente (hash), reprise sur erreur, versions d'index | PM §7 | P1 | services/ingestion | tests/integration | Implémenté, tests incomplets (hash, rejeu idempotent, erreur isolée ; PostgreSQL/MinIO non faits) |
| D-07 | Stockage : PostgreSQL (métadonnées), MinIO (fichiers) | PDF §3 | P1 | database, storage | tests/integration | Implémenté, non validé sur serveurs réels (MinIO : faux client ; PostgreSQL : non testé) |
| R-01 | Embeddings multilingues (BGE-M3 ou équivalent) + Qdrant | PDF §3 | P0 | services/retrieval | recall@5 | Validé sur Colab : BGE-M3 + Qdrant mémoire, Recall@5 0,91-0,97 selon le jeu ; Qdrant serveur non validé |
| R-02 | Recherche visuelle (CLIP multilingue) sur figures | PDF §4.2 | P1 | services/retrieval | tests multimodaux | Non implémenté |
| R-03 | Fusion RRF texte + image | PDF §4.2 | P1 | services/retrieval | tests/unit RRF | Non implémenté |
| R-04 | Reranking des candidats | PDF §4.2 | P1 | services/reranking | comparaison A/B | Non implémenté |
| R-05 | Filtrage permissions AVANT récupération et à l'affichage | PDF §4.2, §9 | P0 | retrieval, api | tests/security fuite | Implémenté et testé (recherche) ; 0 fuite sur les jeux texte ; contrôle côté API à faire |
| R-06 | VLM Qwen2.5-VL-7B-Instruct (ou remplacement justifié) | PDF §3 | P0 | services/multimodal | test GPU séparé | **Bloqué ici (pas de GPU/HF)** |
| R-07 | Citations = pages/figures réellement récupérées ET soutenant l'affirmation | PDF §4.2 | P0 | services/answer_generation | tests citations non-soutenantes | Implémenté : citations correctes 45/45 (jeu de 150, après correctifs) ; juge sémantique non branché |
| R-08 | Gestion contradictions et versions obsolètes | PM §14 | P0 | agents/nodes | e2e #8,9 | Partiel : versions obsolètes OK ; contradiction HN-S8 détectée sur 3 formulations sur 6 (jeu de 150) |

## Agent, MCP, approbation

| ID | Exigence | Source | Prio | Module cible | Test / preuve prévus | Statut |
|---|---|---|---|---|---|---|
| A-01 | Workflow LangGraph : accès → analyse → recherche → MCP → vérification → réponse/clarif → ticket → approbation → création | PDF §6 | P0 | agents | tests/unit graphe | Non implémenté |
| A-02 | Limites de boucle, ≤ 6 appels modèle, ≤ 3 appels MCP, ≤ 60 s auto | PDF §9 | P0 | agents, core/config | tests budgets | Non implémenté |
| A-03 | Interruption pour validation humaine + checkpoints + reprise | PDF §6, FR P6 | P0 | agents/checkpointing | test redémarrage | Non implémenté |
| A-04 | Serveur MCP : get_equipment_history, get_open_tickets, create_ticket | PDF §6 | P0 | mcp/server | tests/integration MCP | Non implémenté |
| A-05 | Autorisations vérifiées côté serveur MCP à chaque appel | PDF §6,9 | P0 | mcp/authorization | tests MCP non autorisé | Non implémenté |
| A-06 | Approbation liée à utilisateur + contenu exact + expiration + usage unique ; modification ⇒ ré-approbation | PDF §6 | P0 | services/ticketing | tests/security | Non implémenté |
| A-07 | Clé d'idempotence (rejeu, timeout après exécution, concurrence) | PDF §6 | P0 | mcp, ticketing | tests idempotence | Non implémenté |
| A-08 | Retries bornés, timeouts par dépendance, dégradation | PM §16 | P1 | core | tests résilience | Non implémenté |

## Sécurité et rôles

| ID | Exigence | Source | Prio | Module cible | Test / preuve prévus | Statut |
|---|---|---|---|---|---|---|
| S-01 | Rôles technician / maintenance_manager / admin, vérif. serveur | FR P7, PM §15 | P0 | core/security | tests/security RBAC | Non implémenté |
| S-02 | Admin ≠ accès automatique aux données métier | PM §15 | P1 | core/security | test dédié | Non implémenté |
| S-03 | Documents, OCR, sorties MCP = données non fiables | PDF §9 | P0 | prompts, agents | tests injection | Non implémenté |
| S-04 | Tests d'injection (exfiltration, élévation, appel MCP, ticket sans accord) | PDF §9 | P0 | tests/security | 20 scénarios | Non implémenté |
| S-05 | Secrets hors Git/prompts/logs ; `.env.example` sans valeur réelle | PDF §9 | P0 | repo | scan secrets | Non implémenté |
| S-06 | Logs minimisés (métadonnées, pas de contenu brut), rétention définie | PDF §9 | P1 | observability | test logs | Non implémenté |
| S-07 | Validation fichiers (type, taille, chemins), quotas, destinations réseau restreintes | PDF §9 | P1 | api/middleware | tests/security | Non implémenté |
| S-08 | Traçabilité par affirmation (ClaimEvidence, SourceReference, EvidenceVerification, AnswerTrace) | PM §14 | P0 | schemas | tests/unit | Non implémenté |

## Évaluation et MLOps

| ID | Exigence | Source | Prio | Module cible | Test / preuve prévus | Statut |
|---|---|---|---|---|---|---|
| E-01 | Jeu de ~150 scénarios (40/30/20/20/20/20) | PDF §10 | P0 | data/evaluation | décompte réel documenté | Partiel : jeu figé de 150 scénarios (data/evaluation/eval_150.jsonl) ; 80 exécutables, 70 attendent l'agent, le MCP et le VLM |
| E-02 | Recall@5, nDCG@5, MRR@10 | PDF §10 | P0 | scripts/evaluate_rag.py | rapport | Implémenté et mesuré avec BGE-M3 sur Colab (voir journal) |
| E-03 | Métriques réponses, citations, multimodal vs texte seul, abstentions, outils, sécurité | PDF §10 | P1 | scripts/evaluate_rag.py | rapport | Non implémenté |
| E-04 | Latence médiane/p95, mémoire, GPU ; objectifs : ≥90 % citations soutenantes, 0 ticket sans accord, 0 fuite, p95 < 30 s | PDF §10 | P1 | rapport | **objectifs, pas résultats** | Non implémenté |
| E-05 | Reranker : 800–1500 exemples, split par doc/famille, 3 comparaisons | PDF §5 | P2 | scripts/train_reranker.py | MLflow | Non implémenté (dépend GPU/données) |
| E-06 | MLflow, versions modèle/prompt/reranker/index | PDF §11 | P1 | observability | runs MLflow | Non implémenté |
| E-07 | Prompts versionnés (4 YAML) | PDF §7 | P0 | prompts/ | tests chargement | Non implémenté |

## Livraison

| ID | Exigence | Source | Prio | Module cible | Test / preuve prévus | Statut |
|---|---|---|---|---|---|---|
| L-01 | Docker Compose + health checks + `.env.example` | PDF §11 | P1 | docker-compose.yml | test démarrage | **Bloqué ici (pas de daemon Docker)** |
| L-02 | CI : tests, secrets, dépendances | PDF §11 | P2 | .github/ | pipeline | Non implémenté |
| L-03 | `scripts/validate_project.py` + rapport réel | PM §22 | P0 | scripts | exécution | Non implémenté |
| L-04 | Livrables : cadrage, dépôt, prototype, évaluation, **fiche de limites**, démo | PDF §13 | P0 | docs | revue | Non implémenté |
| L-05 | Scénario de démonstration (7 étapes PDF §14) | PDF §14 | P0 | docs/demo_guide.md | répétition | Non implémenté |
| L-06 | Procédure de rollback modèle/prompt/index | PDF §11 | P2 | docs | revue | Non implémenté |

## Divergences relevées entre les documents

1. **Orchestration** : le PDF cite **LangChain + LangGraph** ; le prompt maître ne mentionne que LangGraph. → LangChain utilisé légèrement (loaders de prompts, parseurs, abstractions retriever) ; LangGraph pour le graphe. À confirmer.
2. **Planning** : PDF et prompt maître = 6 semaines ; la feuille de route = phases sur ~6 semaines mais avec une phase RAG textuel **avant** le multimodal et l'interdiction d'entraîner avant un RAG de base mesurable. → ordre de la feuille de route retenu.
3. **Équipes de fichiers docs** : la feuille de route demande aussi `project_scope.md` et `acceptance_criteria.md` en plus des 5 docs du prompt maître. → créés en phase 1.
4. **Interface** : la feuille de route prévoit l'upload de **PDF** dans l'UI ; le prompt maître réserve l'ingestion à `POST /api/documents` (rôle autorisé). → upload PDF limité aux rôles autorisés.

## Journal d'avancement (preuves réelles, mis à jour le 2026-10-28)

Environnement : CPU, 2 vCPU, sans GPU. Embeddings `hashing` (non sémantique). Qdrant en mode local (`:memory:`). Suite : `python -m pytest -q` → **29 passés, 0 échoué** (≈ 50 s).

| ID | Statut | Preuve | Limite connue |
|---|---|---|---|
| D-01 corpus | Terminé et vérifié (corpus fictif) | `tests/unit/test_corpus.py` : 50 fichiers (49 documents + 1 doublon exact, limite PDF 30–50), 14 modèles, ≥ 25 codes/modèle, 2 scans, obsolète, contradiction, confidentiel, injection | Corpus fictif : métriques non représentatives de vrais manuels |
| D-03 PDF numériques / D-05 tableaux, figures | Implémenté, tests incomplets | `test_ingestion.py` : page, version, groupes, une ligne de tableau = un passage, figures avec `element_id` | pas de Qdrant serveur ni PostgreSQL/MinIO |
| D-04 OCR | Implémenté, tests incomplets | scan HN-S3 traité par OCR | **langue `eng` seulement** (pas de `fra` installé) |
| D-06 idempotence ingestion | Implémenté, tests incomplets | rejeu : 100 % `skipped_duplicate`, 0 doublon | reprise partielle après crash non testée |
| R-01 recherche texte | Implémenté, tests incomplets | 14 questions de seuils (une par modèle) retrouvent la bonne valeur et le bon document | backend `hashing` : **aucune métrique Recall/nDCG/MRR publiée** ; BGE-M3 non testé |
| R-05 filtre d'accès avant récupération | Terminé et vérifié (Qdrant local) | `test_no_cross_group_leak`, `test_no_groups_means_no_retrieval`, non-distinction « non autorisé » / « inconnu » | à rejouer sur Qdrant serveur |
| F-08 clarification / abstention | Implémenté, tests incomplets | E301 sans modèle → clarification ; modèle inconnu et hors-corpus → abstention | photo ambiguë et contradictions : non implémentés |
| R-07 citations soutenant l'affirmation | Implémenté, tests incomplets | `verify_support` rejette valeur numérique absente et affirmation sans recouvrement | juge sémantique (LLM) non branché |
| R-08 contradictions / versions | En cours | versions obsolètes exclues (testé) | contradiction bulletin/manuel **non détectée** à ce stade |
| F-10 pas de score de confiance inventé | Terminé et vérifié | `AnswerResponse(extra="forbid")` refuse `confidence` | — |
| R-06 VLM, R-02 recherche visuelle, F-02 photo | Bloqué (pas de GPU/HF ici) / Non implémenté | — | — |
| A-*, S-*, E-*, L-* | Non implémenté | — | — |

### Défauts trouvés et corrigés pendant la phase 4 (traçabilité)
1. Contenu des tableaux mélangé dans le texte courant → réponses fausses ; correction : zones de tableaux exclues du texte, une ligne = un passage.
2. Abstention inefficace avec les embeddings `hashing` (score identique pour une question hors sujet) → garde-fou lexical indépendant du modèle.
3. Modèle inconnu non détecté (regex limitée aux séries S/T/B) → regex élargie.
4. Identifiant exact (`E301`) ignoré par les embeddings → bonus lexical hybride.
5. Symbole ohm Unicode différent de l'oméga saisi → normalisation NFKC.


## Journal - corpus v2 et 2e passe RAG (31/10/2026)
- Corpus officiel : 50 documents / 461 pages, 22 photos générées (avec vérité de terrain), 2 scans dégradés (rotation, bruit, flou). Corpus enrichi optionnel (71 documents, notes de terrain SAV, FAQ...) hors périmètre de conformité D-01.
- Preuve : `python -m scripts.eval_smoke` = 64/64 questions (couple, masse, câble AC, fusible, rendement, stockage, 8 compatibilités) ; 38 tests passent.
- Limites : ces 64 questions ont servi à régler le système (risque de surapprentissage) ; backend `hashing` non sémantique ; photos générées par code, pas réelles ; aucune métrique Recall/nDCG/MRR publiable sans BGE-M3 et jeu d'évaluation indépendant (~150 scénarios).

## Journal - complément phase 3 (01/11/2026)
- Pages vides : détectées par l'ingestion (`blank_pages`), non indexées ; 1 page vide dans `annexe_hnt15_piegee` (page 2) ; tests unitaires (PDF entièrement vide, page vide du corpus).
- Stockage : `app/services/storage` - fichiers adressés par contenu (MinIO ou dossier local), métadonnées SQLAlchemy (PostgreSQL ou SQLite) avec filtre par groupes ; doublon stocké une seule fois ; `docker-compose.yml` (Qdrant, PostgreSQL, MinIO). **Non validé sur de vrais serveurs** : pas de daemon Docker ici ; MinIO testé avec un client simulé, PostgreSQL non testé (SQLite uniquement).
- Extraction vérifiée sur échantillon : `python -m scripts.verify_extraction_sample` -> `docs/extraction_sample_report.md` (résultats réels : voir ce fichier).

## Journal - phase 4 : contradictions et jeu de référence (02/11/2026)
- Contradictions (F-08) : statut `conflicting_sources` ; deux documents valides du même modèle donnant des valeurs différentes pour la même grandeur (même unité, passages couvrant la question) -> réponse citant les deux sources, sans trancher. Test : manuel HN-S8 (63 °C) vs bulletin (58 °C), aucun faux positif sur les 13 autres modèles.
- Jeu de référence texte : `data/evaluation/text_reference.jsonl` (70 scénarios : 40 avec réponse, 10 sans source, 5 contradiction, 5 obsolète, 10 droits). **Première exécution : 53/70** (`docs/eval_text_reference_first_run.md`). Après 6 correctifs génériques (radical de 4 lettres, mots vides, unité = mot-clé, ligne du tableau des codes, couverture lexicale du passage retenu) : **61/70** ; Recall@5 0,804, nDCG@5 0,714, MRR@10 0,709 ; citations correctes 41/41 ; 0 fuite du contenu confidentiel.
- Réserve : ces chiffres sont mesurés avec le backend `hashing` (non sémantique) sur des scénarios synthétiques, et les correctifs ont été décidés après lecture des échecs : ils ne remplacent pas une évaluation BGE-M3 à l'aveugle. Échecs restants = écarts de vocabulaire (« protège la sortie AC », « entreposée », « derating », « bride ») et deux questions hors corpus qui contournent la barrière lexicale.

## Statut phase 4 (02/11/2026)
**Implémentée avec moteurs de remplacement ; validation réelle en attente.**
- Fait et testé : provenance des chunks, index Qdrant (mémoire locale), filtre équipement + droits, citations vérifiées, refus/clarification, contradictions, jeu de référence (61/70).
- À valider sur machine GPU : embeddings BGE-M3 (remplace `hashing`), serveur Qdrant réel, modèle de rédaction (remplace la réponse extractive), reranker éventuel ; relancer `python -m scripts.eval_text_reference` avec `EMBEDDING_BACKEND=bge-m3` et comparer à la première exécution (53/70) et à 61/70.
- Cibles du PDF non prouvées : ≥ 90 % de citations justifiées, p95 < 30 s.


## Journal - semaine 2 : BGE-M3 et jeux d'évaluation (07-09/11/2026)
Mesures réelles sur Google Colab (GPU T4), corpus régénéré, Qdrant en mémoire ; fichiers dans `docs/eval_*`.

| Jeu | Avant correctifs | Après correctifs | Remarque |
|---|---|---|---|
| Référence 70 (BGE-M3) | 65/70 ; Recall@5 0,952 | 67/70 | jeu non indépendant (a servi au réglage) |
| Figé 150, parties texte (80) | 58/80 ; Recall@5 0,910 ; citations 31/36 | **72/80** ; citations 45/45 | non indépendant depuis la lecture des échecs |
| Contrôle 60 (graine 777, échecs non lus avant mesure) | — | **58/60** ; Recall@5 0,971 ; citations 33/33 | première mesure ; jeu synthétique généré des mêmes faits |

Défauts restants (jeu de 150, après correctifs) : contradiction HN-S8 non signalée sur 3 formulations, une question de prix répondue par une description au lieu d'une abstention, quatre demandes confidentielles sans modèle qui reçoivent « précisez le modèle » (aucune fuite).
Non mesuré : 30 scénarios image (VLM), 20 MCP, 10 validation humaine, 10 injections côté outils, latence p95, Docker/PostgreSQL/MinIO réels, reranker. Correctifs : `docs/eval_150_corrections.md`.
