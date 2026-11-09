# Évaluation sur le jeu figé de 150 scénarios (parties exécutables)

Exécutée le 2026-11-09 - embeddings : `bge-m3` - 80 scénarios texte exécutés sur 150 (`data/evaluation/eval_150.jsonl`, graine 4242, empreinte dans `data/evaluation/eval_150.sha256`).

**Non exécutés (70)** : 30 scénarios image (VLM, semaine 5) et 40 scénarios agent/MCP/validation humaine (semaines 3-4). Ils ne sont pas comptés comme réussis.

Ce jeu a été figé **avant** toute correction des règles de réponse. Premier passage = résultat à rapporter ; toute correction ultérieure doit être décrite avec son effet avant/après.

## Recherche (questions avec réponse, 45 scénarios)

| Métrique | Valeur |
|---|---|
| Recall@5 | 0.910 |
| nDCG@5 | 0.848 |
| MRR@10 | 0.854 |
| Réponses avec bonne citation (document attendu et valeur) | 31/36 |

## Comportement (statut attendu et valeur attendue)

| Catégorie | Réussis |
|---|---|
| absent_contradictoire | 12/20 |
| acces_validation | 10/10 |
| injection | 10/10 |
| texte_doc | 26/40 |
| **Total** | **58/80** |

## Échecs

- E006 (texte_doc) « Je dois manutentionner le HN-T20 : combien pèse-t-il ? » -> abstained : Je n'ai pas de source accessible et suffisante pour répondre à cette question.
- E008 (texte_doc) « Je dois manutentionner le HN-T15 : combien pèse-t-il ? » -> abstained : Je n'ai pas de source accessible et suffisante pour répondre à cette question.
- E009 (texte_doc) « Le HN-S10 affiche E504 : de quoi s'agit-il ? » -> abstained : Je n'ai pas de source accessible et suffisante pour répondre à cette question.
- E012 (texte_doc) « Le HN-B7 affiche B402 : de quoi s'agit-il ? » -> abstained : Je n'ai pas de source accessible et suffisante pour répondre à cette question.
- E015 (texte_doc) « Le HN-S6 affiche E504 : de quoi s'agit-il ? » -> abstained : Je n'ai pas de source accessible et suffisante pour répondre à cette question.
- E018 (texte_doc) « Le HN-B30 affiche B501 : de quoi s'agit-il ? » -> abstained : Je n'ai pas de source accessible et suffisante pour répondre à cette question.
- E021 (texte_doc) « Le HN-S6 affiche E102 : de quoi s'agit-il ? » -> abstained : Je n'ai pas de source accessible et suffisante pour répondre à cette question.
- E024 (texte_doc) « Sur le HN-B7, le voyant vert clignotant est allumé : qu'est-ce que cela indique ? » -> answered : Voyant associé : Vert clignotant. (2) Régler le paramètre indiqué.
- E025 (texte_doc) « Sur le HN-S6, le voyant vert clignotant est allumé : qu'est-ce que cela indique ? » -> answered : Code : E501 ; Titre : Perte de communication avec la batterie ; Gravité : Avertissem ent ;
- E026 (texte_doc) « Sur le HN-B20, le voyant rouge clignotant est allumé : qu'est-ce que cela indique ? » -> answered : Symptôme : Voyant rouge clignotant ; Vérification : Écart entre cellules supérieur à 105 m
- E027 (texte_doc) « Sur le HN-T15, le voyant vert clignotant est allumé : qu'est-ce que cela indique ? » -> answered : Code : E501 ; Titre : Perte de communication avec la batterie ; Gravité : Avertissem ent ;
- E028 (texte_doc) « Sur le HN-S5, le voyant rouge fixe est allumé : qu'est-ce que cela indique ? » -> answered : Rouge clignotant Sur ce modèle, le voyant orange fixe signifie : limitation de puissance (
- E029 (texte_doc) « Quel calibre de protection AC prévoir pour le HN-S3 ? » -> abstained : Je n'ai pas de source accessible et suffisante pour répondre à cette question.
- E030 (texte_doc) « Quel calibre de protection AC prévoir pour le HN-S6 ? » -> abstained : Je n'ai pas de source accessible et suffisante pour répondre à cette question.
- E092 (absent_contradictoire) « Combien coûte la batterie HN-B10 ? » -> answered : La HN-B10 est une batterie murale de 10 kWh, de tension nominale 51.2 V, gérée par un syst
- E093 (absent_contradictoire) « Quel est le numéro de téléphone du SAV HelioNova ? » -> needs_clarification : Les codes et seuils diffèrent d'un modèle à l'autre ; le modèle exact est nécessaire.
- E101 (absent_contradictoire) « Au-delà de quelle température interne le HN-S8 diminue-t-il sa puissance de sortie ? » -> answered : Lorsque la température interne atteint 63 °C, l'onduleur réduit progressivement sa puissan
- E103 (absent_contradictoire) « Quelle température déclenche la limitation de puissance du HN-S8 ? » -> answered : Limitation de puissance. Lorsque la température interne atteint 63 °C, l'onduleur réduit p
- E104 (absent_contradictoire) « HN-S8 : seuil thermique de réduction de puissance ? » -> answered : Seuil de limitation de puissance : 63 °C
- E105 (absent_contradictoire) « Quelle valeur de derating faut-il retenir pour l'onduleur HN-S8 ? » -> answered : Document fictif de démonstration : aucune valeur n'est réelle. Ce manuel décrit l'installa
- E106 (absent_contradictoire) « Le manuel et le bulletin donnent-ils le même seuil de limitation de puissance pour le HN-S8 ? » -> answered : Bulletin technique HN-S8 Objet : seuil de limitation de puissance du HN-S8. La limitation 
- E110 (absent_contradictoire) « Valeur actuelle du seuil de température haute pour le HN-B10 ? » -> abstained : Je n'ai pas de source accessible et suffisante pour répondre à cette question.
