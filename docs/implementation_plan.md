# Plan de réalisation

Règle (feuille de route) : en fin de phase → tests exécutés, preuves enregistrées, doc à jour, commit Git. Une phase n'est « terminée » que si ses critères de sortie sont démontrés.

| Phase | Contenu | Critères de sortie | Dépendances matérielles |
|---|---|---|---|
| **1 — Périmètre** *(audit fait)* | requirements_matrix ✔, architecture ✔, decisions ✔, risks ✔, plan ✔ ; reste `project_scope.md`, `acceptance_criteria.md`, choix des 2 familles d'équipements | chaque exigence a ID, priorité, moyen de vérification | aucune |
| **2 — Dépôt & environnement** | `pyproject.toml`, `.env.example`, `.gitignore`, config Pydantic-settings, logging, `Makefile`, `docker-compose.yml` + health checks, versions figées | `pytest` vide passe ; secrets absents ; Compose **écrit** (validé seulement là où Docker tourne) | Docker pour valider Compose |
| **3 — Corpus & ingestion** | générateur de corpus synthétique (2 familles, 30–50 PDF avec versions, groupes d'accès, quelques scans, tableaux, figures, contradictions et un doc obsolète), pipeline PyMuPDF + OCR, métadonnées, hash, reprise | extraction vérifiée sur échantillon ; accès filtré | OCR `fra` |
| **4 — RAG textuel** | chunking structurel (procédure + avertissements ensemble), embeddings, Qdrant, filtre d'accès, citations, abstention | questions de référence de bout en bout ; cas sans réponse refusés | modèles d'embeddings pour métriques réelles |
| **5 — Multimodal** | figures indexées, recherche visuelle, RRF, analyse d'image avec incertitudes, demande de photo | scénarios image testés, citations page/figure | VLM/CLIP pour métriques réelles |
| **6 — LangGraph + MCP** | graphe, serveur MCP, brouillon, approbation HMAC, checkpoints, idempotence, budgets | 0 ticket sans approbation ; reprise testée | aucune (CPU) |
| **7 — Sécurité & traçabilité** | RBAC, matrice de permissions, `ClaimEvidence/AnswerTrace`, contradictions, injections, logs minimisés | tests accès + injection verts ; audit par affirmation | aucune |
| **8 — API & UI** | FastAPI (endpoints PM §11), Streamlit, erreurs propres, démo reproductible | parcours complet sans modifier le code | aucune |
| **9 — Évaluation & reranker** | jeu de ~150 scénarios (décompte réel documenté), métriques, comparaison sans/initial/adapté, MLflow | rapport reproductible, aucune métrique inventée | GPU/modèles pour valeurs réelles |
| **10 — E2E & livraison** | 20 scénarios E2E, `validate_project.py` + rapport, diagrammes issus du code, fiche de limites, guide de démo, rollback, CI | installation reproductible, rapport honnête | Docker + GPU pour la démo finale |

## Ce qui peut être construit et testé **ici** (CPU, sans HF, sans Docker)
Phases 1, 2 (hors Compose validé), 3 (avec OCR anglais/RapidOCR), 4–8 avec backends fake/local, et la majeure partie des tests de sécurité, MCP, approbation, idempotence, reprise.

## Ce qui exige **votre** matériel ou accès
Qwen2.5-VL réel, BGE-M3/reranker/CLIP réels, métriques de recherche et de réponse réelles, latence p95, fine-tuning du reranker, validation Docker Compose, parcours E2E avec services réels.

## Commandes de référence (prévues)
```bash
make install      # dépendances
make test         # tests rapides CPU
make test-docker  # tests nécessitant les services
make validate     # python scripts/validate_project.py
```
