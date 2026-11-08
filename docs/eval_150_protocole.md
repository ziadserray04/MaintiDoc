# Protocole du jeu figé de 150 scénarios

- **Contenu** : 40 questions textuelles, 30 image, 20 MCP, 20 sources absentes/insuffisantes/contradictoires, 20 accès et validation humaine, 20 injections (répartition du sujet §10).
- **Génération** : `python -m scripts.build_eval150` (graine 4242) depuis `facts.json`, `equipment_history.json` et `photos_manifest.json`. Fichier : `data/evaluation/eval_150.jsonl`, empreinte : `eval_150.sha256` (vérifiée par `tests/unit/test_eval150.py`).
- **Exécutables aujourd'hui** : 80 scénarios `text`. Les 30 `vlm` (semaine 5) et les 20 `agent` (semaines 3-4) sont décrits mais **non exécutés ni comptés comme réussis**.
- **Règle** : le jeu est figé avant toute correction des règles de réponse. Le **premier passage** de chaque backend est enregistré (`docs/eval_150_*_premier_passage.md`) et ne change plus. Toute correction ultérieure est décrite avec son effet avant/après ; si le jeu doit changer, la décision et la raison sont écrites ici.
- **Limites** : scénarios synthétiques tirés des mêmes faits que le corpus ; ils mesurent la chaîne, pas la qualité sur de vrais documents. L'absence d'échec n'est pas une garantie de sécurité.
