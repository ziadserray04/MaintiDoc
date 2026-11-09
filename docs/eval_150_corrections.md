# Corrections des règles de réponse après le premier passage du jeu de 150

**Contexte.** Premier passage BGE-M3 sur `eval_150` (80 scénarios texte) : 58/80, Recall@5 0,910, citations 31/36 (86 %). La recherche est bonne ;
les échecs viennent des règles de réponse, réglées avec le backend de test. Les correctifs ci-dessous ont été décidés **après lecture des échecs de
ce jeu** : il n'est donc plus indépendant. Le jeu de contrôle `holdout_60` (graine 777, formulations nouvelles, figé avant les correctifs, échecs non lus)
sert à vérifier que les correctifs se généralisent.

| # | Problème observé | Correctif (général, sans cas particulier) |
|---|---|---|
| 1 | Abstention à tort quand la question utilise d'autres mots que le document (« calibre de protection », « pèse », « de quoi s'agit-il ») | Mots de formulation ignorés (« dois », « affiche », « agit », « valeur actuelle »…) ; table d'équivalents du domaine (`SYNONYMS`), appliquée seulement aux passages courts (≤ 300 caractères) pour ne pas faire passer un long paragraphe générique |
| 2 | Questions sur un code d'erreur rejetées parce que les mots autour du code manquent | Un code d'erreur retrouvé mot pour mot dans une source vaut preuve : on n'exige plus les mots de formulation |
| 3 | « Que signifie le voyant vert clignotant ? » renvoie une fiche de code | Question sur un voyant + modèle connu : on renvoie la ligne du tableau « Voyant \| Signification » du modèle |
| 4 | Contradiction du HN-S8 non détectée selon la formulation | Le conflit est cherché dans un pool plus large (30 passages) et les équivalents du domaine comptent pour le recouvrement |

**Essayé puis retiré :** un bonus de classement pour les lignes de tableau a fait passer 3 tests existants au rouge (réponses tirées du guide de codes au lieu du manuel) ; supprimé.

## Résultats avec le backend de test (hachage), avant → après

| Jeu | Réussis | Réponses fausses | Abstentions à tort |
|---|---|---|---|
| Référence 70 | 63 → 65 | 2 → 2 | 3 → 1 |
| eval_150 (80 texte) | 52 → 64 | 15 → 12 | 11 → 1 |
| Contrôle 60 | 46 → 55 | 9 → 4 | 5 → 1 |
| Jeu de développement 64 | 64 → 64 | | |

Les gains se retrouvent sur le jeu de contrôle (46 → 55), ce qui indique que les correctifs ne sont pas qu'un ajustement au jeu de 150.
**Mesure BGE-M3 après correctifs : à faire sur Colab** (`notebooks/semaine2_apres_correctifs_colab.ipynb`) ; ce sera aussi la première mesure BGE-M3 du jeu de contrôle.

## Limites connues (non corrigées)
- Une réponse hors-sujet reste possible quand un mot du domaine apparaît ailleurs (ex. « calibre de protection » face à « Indice de protection : IP65 ») : il faut un classement sémantique plus fin (reranking, exigence R-04).
- Les questions hors corpus (« Combien coûte… ? ») peuvent recevoir la description générale de l'équipement : il faut un seuil de similarité calibré pour BGE-M3 (non fait ; la constante `MIN_SCORE` reste celle du backend de test).
- Les questions sans modèle, sur un sujet confidentiel ou absent, reçoivent parfois « précisez le modèle » au lieu d'une abstention : sans fuite, mais imprécis.
