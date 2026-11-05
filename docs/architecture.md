# Architecture — MAINTiDOC (cible et variante de développement)

## Principe directeur

Toute dépendance lourde ou externe est derrière une **interface** (`Protocol`) avec deux implémentations :
- **`real`** : technologie du cahier des charges (Qwen2.5-VL, BGE-M3, Qdrant, PostgreSQL, MinIO…) ;
- **`local`/`fake`** : implémentation légère exécutable sur CPU sans réseau (embeddings déterministes, Qdrant en mode `:memory:`/local, SQLite, stockage disque, VLM simulé).

Les tests rapides utilisent `local`/`fake` et sont **étiquetés comme tels**. Les résultats obtenus avec un VLM simulé ne sont jamais présentés comme des performances du vrai modèle.

## Vue d'ensemble

```
Streamlit ──► FastAPI (authN/authZ, validation Pydantic, quotas, corrélation)
                 │
                 ▼
          Workflow LangGraph (état structuré, checkpoints, budgets)
   ┌─────────┬──────────┬───────────┬────────────┐
   ▼         ▼          ▼           ▼            ▼
 Retrieval  VLM      Client MCP   Evidence     Ticketing
 (texte +  (images)  (≤3 appels)  verifier     (brouillon,
  visuel,                         (support     approbation)
  RRF,                            réel des
  rerank)                         citations)
   │                    │                          │
Qdrant              Serveur MCP ◄─────────── approval_token + idempotency_key
PostgreSQL          (historique, tickets)
MinIO
```

## Flux de requête (ordre imposé du graphe)

1. `authenticate` — identité + permissions (serveur uniquement) ; sinon arrêt.
2. `validate_input` — taille/format question et image.
3. `classify_request` — question simple, ticket demandé, hors périmètre/risque.
4. `analyze_image` (si image) — observations uniquement, incertitudes explicites.
5. `retrieve` — **filtre d'accès appliqué dans la requête Qdrant**, texte + visuel, RRF.
6. `rerank`.
7. `call_mcp` (si nécessaire et autorisé, ≤ 3).
8. `verify_evidence` — chaque affirmation ↔ source ; contradictions ; versions obsolètes.
9. `decide` — **answer / clarify / abstain**.
10. `generate_answer` — sortie Pydantic validée (≤ 2 réparations).
11. `draft_ticket` (si demandé) → `interrupt` pour approbation humaine.
12. `verify_approval` → `create_ticket` (MCP, clé d'idempotence) → `audit`.

Aucun chemin n'atteint `create_ticket` sans passer par `verify_approval`. Test unitaire du graphe : l'arête est inexistante.

## Modèle de permissions (résumé, détail dans docs/permissions_matrix.md en phase 7)

| Action | technician | maintenance_manager | admin |
|---|---|---|---|
| Interroger documents de ses groupes | ✔ | ✔ | ✘ par défaut |
| Photo + question | ✔ | ✔ | ✘ |
| Historique / tickets de ses équipements | ✔ | ✔ | ✘ |
| Brouillon de ticket | ✔ | ✔ | ✘ |
| Approuver un ticket | ✘ | ✔ (≠ créateur du brouillon) | ✘ |
| Ingérer des documents | ✘ | ✘ | ✔ |
| Gérer rôles/groupes, consulter l'audit | ✘ | ✘ | ✔ |

## Approbation de ticket

`approval = HMAC(secret_serveur, user_id ‖ ticket_id ‖ SHA-256(equipment_id,title,description) ‖ expires_at ‖ nonce)`, état `pending → approved → consumed|expired|revoked`. Usage unique, vérifié à l'approbation **et** à l'exécution, par le serveur MCP (qui ne fait pas confiance au client LangGraph). Le modèle ne reçoit jamais le secret ni ne produit de jeton.

## Données

- **PostgreSQL** (SQLite en dev) : `users`, `groups`, `documents`, `document_versions`, `chunks`, `visual_elements`, `equipments`, `tickets`, `approvals`, `audit_log`, `ingestion_runs`.
- **Qdrant** : collections versionnées `chunks_text_v{n}`, `figures_clip_v{n}` ; payload = `document_id, version, page, element_id, element_type, equipment_family, equipment_model, access_groups, validity_status`.
- **MinIO** (dossier local en dev) : PDF originaux, pages rendues, figures.

## Environnements

| Profil | Cible | Contenu |
|---|---|---|
| `dev-cpu` (ici) | CPU, 8 Go, sans réseau modèle | backends fake/local, tests rapides |
| `gpu-demo` | GPU ≥ 24 Go, Docker | Qwen2.5-VL quantifié, BGE-M3, Qdrant, PG, MinIO, MLflow |

Les diagrammes détaillés (workflow réel, pipeline RAG, schéma de données) seront générés **depuis le code** en phase 10 pour rester conformes.
