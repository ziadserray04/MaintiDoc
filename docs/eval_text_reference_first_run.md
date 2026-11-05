# Évaluation du RAG texte sur le jeu de référence

Exécutée le 2026-11-02 - embeddings : `hashing` - 70 scénarios (`data/evaluation/text_reference.jsonl`, graine 2026).

Ces scénarios sont **synthétiques**, générés depuis les mêmes faits que le corpus avec des formulations différentes de celles utilisées pour régler le système. Le backend `hashing` n'est pas sémantique : ces chiffres ne représentent PAS la qualité d'un vrai modèle (BGE-M3).

## Recherche (questions avec réponse, 46 scénarios)

| Métrique | Valeur |
|---|---|
| Recall@5 | 0.804 |
| nDCG@5 | 0.714 |
| MRR@10 | 0.709 |
| Réponses avec bonne citation (document attendu et valeur) | 35/40 |

## Comportement (statut attendu et valeur attendue)

| Catégorie | Réussis |
|---|---|
| code_erreur | 8/10 |
| compatibilité | 3/3 |
| contradiction | 3/5 |
| droits | 8/10 |
| obsolète | 4/5 |
| sans_source | 8/10 |
| valeur | 13/21 |
| voyant | 6/6 |
| **Total** | **53/70** |

## Échecs

- T003 (valeur) « Combien de N.m faut-il pour serrer les bornes du HN-B7 ? » -> answered : Annuelle : Resserrer les bornes et contrôler la capacité
- T004 (valeur) « Combien de N.m faut-il pour serrer les bornes du HN-B15 ? » -> answered : Annuelle : Resserrer les bornes et contrôler la capacité
- T005 (valeur) « Combien de N.m faut-il pour serrer les bornes du HN-B30 ? » -> answered : Annuelle : Resserrer les bornes et contrôler la capacité
- T014 (code_erreur) « Que signifie le code E101 affiché par le HN-S8 ? » -> answered : Symptôme : Production nulle, réseau présent ; Vérification : Contrôler la tension et la fr
- T018 (code_erreur) « Que signifie le code B101 affiché par le HN-B5 ? » -> answered : Symptôme : La batterie ne charge pas par temps froid ; Vérification : Température sous 0 °
- T030 (valeur) « Quel fusible protège la sortie AC du HN-S3 ? » -> abstained : Je n'ai pas de source accessible et suffisante pour répondre à cette question.
- T031 (valeur) « Quel fusible protège la sortie AC du HN-S10 ? » -> abstained : Je n'ai pas de source accessible et suffisante pour répondre à cette question.
- T035 (valeur) « Au bout de combien de mois doit-on recharger la batterie HN-B13 entreposée ? » -> abstained : Je n'ai pas de source accessible et suffisante pour répondre à cette question.
- T036 (valeur) « Au bout de combien de mois doit-on recharger la batterie HN-B7 entreposée ? » -> abstained : Je n'ai pas de source accessible et suffisante pour répondre à cette question.
- T037 (valeur) « Au bout de combien de mois doit-on recharger la batterie HN-B15 entreposée ? » -> abstained : Je n'ai pas de source accessible et suffisante pour répondre à cette question.
- T047 (sans_source) « Qui est le PDG de HelioNova ? » -> needs_clarification : Les codes et seuils diffèrent d'un modèle à l'autre ; le modèle exact est nécessaire.
- T049 (sans_source) « Comment installer un climatiseur ? » -> needs_clarification : Les codes et seuils diffèrent d'un modèle à l'autre ; le modèle exact est nécessaire.
- T052 (contradiction) « Quel est le seuil de derating du HN-S8 ? » -> answered : Seuil de limitation de puissance : 63 °C
- T053 (contradiction) « Le HN-S8 limite sa puissance dès combien de degrés ? » -> answered : Limitation de puissance. Lorsque la température interne atteint 63 °C, l'onduleur réduit p
- T058 (obsolète) « À partir de combien de degrés le HN-S5 bride-t-il sa production ? » -> abstained : Je n'ai pas de source accessible et suffisante pour répondre à cette question.
- T061 (droits) « Quelle est la limite interne de test confidentielle ? » -> needs_clarification : Les codes et seuils diffèrent d'un modèle à l'autre ; le modèle exact est nécessaire.
- T065 (droits) « Limite interne de test confidentielle du HN-B30 ? » -> answered : Action : Vérifier la limite de courant configurée dans l'onduleur.
