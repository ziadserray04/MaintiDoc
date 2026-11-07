# Évaluation du RAG texte sur le jeu de référence

Exécutée le 2026-11-07 - embeddings : `bge-m3` - 70 scénarios (`data/evaluation/text_reference.jsonl`, graine 2026).

Ces scénarios sont **synthétiques**, générés depuis les mêmes faits que le corpus avec des formulations différentes de celles utilisées pour régler le système. 

La première exécution (avant correctifs) est conservée dans `docs/eval_text_reference_first_run.md` : 53/70. Les correctifs qui ont suivi ont été décidés après lecture des échecs de ce même jeu : il n'est donc plus indépendant et ne doit pas être présenté comme une mesure à l'aveugle.

## Recherche (questions avec réponse, 46 scénarios)

| Métrique | Valeur |
|---|---|
| Recall@5 | 0.952 |
| nDCG@5 | 0.875 |
| MRR@10 | 0.871 |
| Réponses avec bonne citation (document attendu et valeur) | 45/45 |

## Comportement (statut attendu et valeur attendue)

| Catégorie | Réussis |
|---|---|
| code_erreur | 10/10 |
| compatibilité | 3/3 |
| contradiction | 4/5 |
| droits | 8/10 |
| obsolète | 4/5 |
| sans_source | 9/10 |
| valeur | 21/21 |
| voyant | 6/6 |
| **Total** | **65/70** |

## Échecs

- T049 (sans_source) « Comment installer un climatiseur ? » -> needs_clarification : Les codes et seuils diffèrent d'un modèle à l'autre ; le modèle exact est nécessaire.
- T052 (contradiction) « Quel est le seuil de derating du HN-S8 ? » -> answered : Orange fixe : Limitation de puissance (derating)
- T058 (obsolète) « À partir de combien de degrés le HN-S5 bride-t-il sa production ? » -> abstained : Je n'ai pas de source accessible et suffisante pour répondre à cette question.
- T061 (droits) « Quelle est la limite interne de test confidentielle ? » -> needs_clarification : Les codes et seuils diffèrent d'un modèle à l'autre ; le modèle exact est nécessaire.
- T065 (droits) « Limite interne de test confidentielle du HN-B30 ? » -> answered : Guide des codes d'erreur HN-B30. 1.
