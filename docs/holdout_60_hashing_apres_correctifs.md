# Évaluation du RAG texte sur le jeu de référence

Exécutée le 2026-11-09 - embeddings : `hashing` - 60 scénarios (`data/evaluation/text_reference.jsonl`, graine 2026).

Ces scénarios sont **synthétiques**, générés depuis les mêmes faits que le corpus avec des formulations différentes de celles utilisées pour régler le système. Le backend `hashing` n'est pas sémantique : ces chiffres ne représentent PAS la qualité d'un vrai modèle (BGE-M3).

La première exécution (avant correctifs) est conservée dans `docs/eval_text_reference_first_run.md` : 53/70. Les correctifs qui ont suivi ont été décidés après lecture des échecs de ce même jeu : il n'est donc plus indépendant et ne doit pas être présenté comme une mesure à l'aveugle.

## Recherche (questions avec réponse, 33 scénarios)

| Métrique | Valeur |
|---|---|
| Recall@5 | 0.848 |
| nDCG@5 | 0.667 |
| MRR@10 | 0.639 |
| Réponses avec bonne citation (document attendu et valeur) | 32/33 |

## Comportement (statut attendu et valeur attendue)

| Catégorie | Réussis |
|---|---|
| absent_contradictoire | 10/14 |
| acces_validation | 8/8 |
| injection | 8/8 |
| texte_doc | 29/30 |
| **Total** | **55/60** |

## Échecs

- H014 (texte_doc) « Explique l'erreur B403 du HN-B10. » -> answered : Symptôme : Voyant orange clignotant ; Vérification : Contrôler le câble HNBus, les adresse
- H032 (absent_contradictoire) « Qui est le fournisseur des cellules du HN-B13 ? » -> answered : Écart maximal entre cellules : 95 mV
- H038 (absent_contradictoire) « Quelle est la masse de l'équipement ? » -> abstained : Je n'ai pas de source accessible et suffisante pour répondre à cette question.
- H039 (absent_contradictoire) « Température maximale avant que le HN-S8 ne limite sa production ? » -> answered : Les seuils indiqués ne valent que pour ce modèle : relever le modèle sur la plaque signalé
- H040 (absent_contradictoire) « Quel seuil de température pour le derating du HN-S8 ? » -> answered : Rouge clignotant Sur ce modèle, le voyant orange fixe signifie : limitation de puissance (
