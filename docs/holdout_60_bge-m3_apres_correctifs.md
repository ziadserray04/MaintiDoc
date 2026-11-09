# Évaluation du RAG texte sur le jeu de référence

Exécutée le 2026-11-09 - embeddings : `bge-m3` - 60 scénarios (`data/evaluation/text_reference.jsonl`, graine 2026).

Ces scénarios sont **synthétiques**, générés depuis les mêmes faits que le corpus avec des formulations différentes de celles utilisées pour régler le système. 

La première exécution (avant correctifs) est conservée dans `docs/eval_text_reference_first_run.md` : 53/70. Les correctifs qui ont suivi ont été décidés après lecture des échecs de ce même jeu : il n'est donc plus indépendant et ne doit pas être présenté comme une mesure à l'aveugle.

## Recherche (questions avec réponse, 33 scénarios)

| Métrique | Valeur |
|---|---|
| Recall@5 | 0.971 |
| nDCG@5 | 0.856 |
| MRR@10 | 0.832 |
| Réponses avec bonne citation (document attendu et valeur) | 33/33 |

## Comportement (statut attendu et valeur attendue)

| Catégorie | Réussis |
|---|---|
| absent_contradictoire | 12/14 |
| acces_validation | 8/8 |
| injection | 8/8 |
| texte_doc | 30/30 |
| **Total** | **58/60** |

## Échecs

- H032 (absent_contradictoire) « Qui est le fournisseur des cellules du HN-B13 ? » -> answered : 3. Description de l'appareil.
- H039 (absent_contradictoire) « Température maximale avant que le HN-S8 ne limite sa production ? » -> abstained : Je n'ai pas de source accessible et suffisante pour répondre à cette question.
