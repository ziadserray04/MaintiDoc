# Évaluation du RAG texte sur le jeu de référence

Exécutée le 2026-11-03 - embeddings : `hashing` - 70 scénarios (`data/evaluation/text_reference.jsonl`, graine 2026).

Ces scénarios sont **synthétiques**, générés depuis les mêmes faits que le corpus avec des formulations différentes de celles utilisées pour régler le système. Le backend `hashing` n'est pas sémantique : ces chiffres ne représentent PAS la qualité d'un vrai modèle (BGE-M3).

La première exécution (avant correctifs) est conservée dans `docs/eval_text_reference_first_run.md` : 53/70. Les correctifs qui ont suivi ont été décidés après lecture des échecs de ce même jeu : il n'est donc plus indépendant et ne doit pas être présenté comme une mesure à l'aveugle.

## Recherche (questions avec réponse, 46 scénarios)

| Métrique | Valeur |
|---|---|
| Recall@5 | 0.783 |
| nDCG@5 | 0.657 |
| MRR@10 | 0.644 |
| Réponses avec bonne citation (document attendu et valeur) | 43/43 |

## Comportement (statut attendu et valeur attendue)

| Catégorie | Réussis |
|---|---|
| code_erreur | 10/10 |
| compatibilité | 3/3 |
| contradiction | 4/5 |
| droits | 8/10 |
| obsolète | 4/5 |
| sans_source | 9/10 |
| valeur | 19/21 |
| voyant | 6/6 |
| **Total** | **63/70** |

## Échecs

- T030 (valeur) « Quel fusible protège la sortie AC du HN-S3 ? » -> abstained : Je n'ai pas de source accessible et suffisante pour répondre à cette question.
- T031 (valeur) « Quel fusible protège la sortie AC du HN-S10 ? » -> abstained : Je n'ai pas de source accessible et suffisante pour répondre à cette question.
- T049 (sans_source) « Comment installer un climatiseur ? » -> needs_clarification : Les codes et seuils diffèrent d'un modèle à l'autre ; le modèle exact est nécessaire.
- T052 (contradiction) « Quel est le seuil de derating du HN-S8 ? » -> answered : Seuil de limitation de puissance : 63 °C
- T058 (obsolète) « À partir de combien de degrés le HN-S5 bride-t-il sa production ? » -> abstained : Je n'ai pas de source accessible et suffisante pour répondre à cette question.
- T061 (droits) « Quelle est la limite interne de test confidentielle ? » -> needs_clarification : Les codes et seuils diffèrent d'un modèle à l'autre ; le modèle exact est nécessaire.
- T065 (droits) « Limite interne de test confidentielle du HN-B30 ? » -> answered : Action : Vérifier la limite de courant configurée dans l'onduleur.
