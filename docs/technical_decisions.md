# Décisions techniques

Format : contexte → décision → conséquences. Les versions seront figées (`uv.lock`/`requirements.lock`) en phase 2.

## Audit de l'environnement (mesuré le 2026-10-26)

| Élément | Constat |
|---|---|
| CPU / RAM | 2 vCPU, 7,8 Gio, pas de swap |
| GPU | **aucun** (`nvidia-smi` absent) |
| Disque | 31 Gio libres sur le volume de travail |
| Python / Node / Git | 3.13.17 / 22.23.4 / 2.43.0 |
| Docker | CLI 29.9.2 présente, **daemon inaccessible** (pas de socket) |
| Réseau | PyPI accessible ; **Hugging Face inaccessible** (code HTTP 000) ; la machine a une liste d'autorisation |
| Paquets déjà présents | `pydantic 2.13`, `mcp 2.3`, Tesseract 5 (langues : `eng`, `osd` seulement — **pas de `fra`**) |
| Installables (dry-run OK) | fastapi 0.162, langgraph 1.2.17, qdrant-client 1.20, pymupdf 2.0 |

## D1 — Qwen2.5-VL-7B impossible dans cet environnement
- **Contexte** : 7 B paramètres ≈ 15 Go en bf16, ≈ 5–6 Go en 4 bits ; pas de GPU, 7,8 Gio de RAM, pas d'accès aux poids.
- **Décision** : code écrit contre l'interface `VisionLanguageModel` ; backends `qwen_transformers`, `qwen_vllm` (cibles) et `fake` (tests). Qwen2.5-VL-7B reste le modèle cible du profil `gpu-demo` (24 Go, quantification, 1 requête à la fois comme dans le PDF §11).
- **Conséquence** : l'analyse d'image réelle, la latence p95 et les métriques multimodales **ne pourront être mesurées qu'en `gpu-demo`**. Aucune de ces valeurs ne sera annoncée avant mesure.

## D2 — Embeddings et reranker
- **Cible** : BGE-M3 (multilingue, licence MIT) ; reranker `bge-reranker-v2-m3` comme reranker initial.
- **Ici** : backend `hashing` déterministe (n-grammes) pour tester la plomberie. Il **ne sert pas** à publier des métriques de qualité de recherche.
- **Conséquence** : Recall@5/nDCG@5/MRR@10 « réels » exigent l'accès aux modèles (poids HF).

## D3 — Recherche visuelle
- **Cible** : CLIP multilingue (ex. `sentence-transformers/clip-ViT-B-32-multilingual-v1` + encodeur image associé), à valider en licence/qualité.
- **Mise en garde** : une similarité visuelle n'est jamais une preuve ; les résultats visuels sont étiquetés `visual_similarity` et ne peuvent pas, seuls, soutenir une affirmation.

## D4 — OCR
- Tesseract local. **Constat** : seule la langue `eng` est installée ; le français exige `tesseract-ocr-fra` (à installer via apt si possible, sinon fournir `fra.traineddata` ; sinon alternative RapidOCR/PaddleOCR via pip). Test de qualité OCR sur PDF scanné synthétique avant d'accepter.

## D5 — Stockage
- **Cible** : PostgreSQL + MinIO + Qdrant (Compose). **Dev** : SQLite (via SQLAlchemy, mêmes modèles), dossier local derrière une interface `ObjectStore`, Qdrant local embarqué (`QdrantClient(path=...)`).
- **Conséquence** : les tests d'intégration réels PostgreSQL/MinIO/Qdrant serveur sont marqués `@pytest.mark.docker` et restent **non exécutés** ici ; le rapport de validation les listera comme « non exécutés ».

## D6 — Orchestration
- LangGraph pour l'état, les arêtes conditionnelles, `interrupt` et le checkpointer (SQLite en dev, PostgreSQL en cible). LangChain limité aux utilitaires (chargement de prompts, parseurs) afin de rester conforme au PDF sans dépendance excessive.

## D7 — MCP
- SDK `mcp` (déjà présent, 2.3). Serveur de démonstration avec données **fictives**, transport stdio (tests) et streamable HTTP (Compose). Toute vérification d'autorisation et d'idempotence est faite **dans le serveur**.

## D8 — Authentification
- JWT signés (secret via variable d'environnement) pour utilisateurs fictifs ; droits relus en base à chaque requête (un utilisateur révoqué perd l'accès immédiatement). Le rôle n'est jamais lu depuis le client.

## D9 — Vérification du support des citations
- Deux niveaux : (1) contrôle déterministe (la citation correspond à un élément réellement récupéré et autorisé) ; (2) contrôle sémantique du support (LLM-juge via `evidence_check_v1`, plus recouvrement lexical/numérique pour valeurs et unités). Le niveau 2 réel dépend du VLM/LLM ; en dev il est simulé et marqué comme tel.

## D10 — Ordre de réalisation (feuille de route)
RAG textuel mesurable **avant** le multimodal ; pas d'entraînement du reranker avant jeu de données validé et RAG de base mesuré.

## Décisions en attente de l'utilisateur
Voir la fin du message de livraison de la phase d'audit (matériel cible, source du corpus, installation de langues OCR).
