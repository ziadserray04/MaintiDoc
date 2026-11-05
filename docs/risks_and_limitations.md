# Risques et limites

| # | Risque | Probabilité | Impact | Mitigation | Résiduel / limite |
|---|---|---|---|---|---|
| 1 | VLM 7 B non exécutable sans GPU ≥ 24 Go (poids HF inaccessibles ici) | Certaine (ici) | Fort | Interface `VisionLanguageModel`, backends fake/real, profil `gpu-demo` | Aucune métrique multimodale réelle avant exécution sur le matériel cible |
| 2 | Métriques de recherche non représentatives avec embeddings « hashing » | Certaine (ici) | Moyen | Ne publier aucune métrique issue des fakes ; étiqueter les runs | Recall/nDCG/MRR réels à mesurer avec BGE-M3 |
| 3 | Corpus synthétique ≠ corpus industriel réel | Certaine | Moyen | Le dire dans toute doc et UI de démo ; scénarios incluant contradictions, scans, tableaux | Généralisation non démontrée |
| 4 | OCR français indisponible (Tesseract : `eng` seul) | Haute | Moyen | Installer `fra` ou OCR alternatif ; test de qualité | Qualité OCR sur schémas/plaques limitée |
| 5 | Docker daemon absent ici | Certaine (ici) | Moyen | Compose écrit + `make test-docker` ; tests services marqués | Compose non validé tant qu'il n'est pas lancé chez vous |
| 6 | Injection de prompt via PDF/OCR/image/MCP | Haute | Fort | Données non fiables, séparation instructions/données, contrôles hors LLM (permissions, approbation côté serveur), 20 scénarios | Pas de garantie générale ; analyse manuelle des cas difficiles |
| 7 | Citation présente mais ne soutenant pas l'affirmation | Haute | Fort | Vérification déterministe + sémantique ; tests dédiés | Le juge sémantique est lui-même un modèle faillible |
| 8 | Hallucination visuelle (voyant, plaque, pièce) | Moyenne | Fort | Observations séparées des faits, clarification si illisible, aucune certitude diagnostique | Dépend de la qualité de la photo et du modèle |
| 9 | Confusion entre équipements similaires/versions | Haute | Fort | Filtre par modèle exact et `validity_status`, contradictions signalées, jamais de choix arbitraire | Métadonnées incorrectes ⇒ erreurs |
| 10 | Création de ticket en double / sans accord | Moyenne | Fort | HMAC lié au contenu, usage unique, idempotence côté serveur MCP, tests de concurrence | Garanti seulement dans le périmètre testé |
| 11 | Fuite entre groupes d'accès | Moyenne | Fort | Filtre dans la requête vectorielle, vérif. à l'affichage, aucun contenu non autorisé dans logs/erreurs | Une absence d'échec en test n'est pas une preuve générale |
| 12 | Latence p95 > 30 s / budget 60 s | Moyenne | Moyen | Budgets appliqués par le code, timeouts, quantification, contexte borné | À mesurer sur le matériel cible |
| 13 | Dépassement des budgets (6 appels modèle, 3 MCP) | Moyenne | Faible | Compteurs dans l'état du graphe, arrêt contrôlé | — |
| 14 | Dérive de versions de dépendances (écosystème rapide) | Moyenne | Moyen | Verrouillage, CI | — |
| 15 | Données personnelles dans photos/documents | Faible (données fictives) | Moyen | Anonymisation, rétention, pas d'images brutes dans les logs | — |

## Limites d'usage (base de la fiche de limites)
- Aide documentaire uniquement : **ne pilote aucun équipement**, ne garantit aucun diagnostic, ne remplace ni les procédures de sécurité ni un technicien habilité.
- Périmètre : deux familles d'équipements du corpus de démonstration.
- Utilisateurs, tickets et historique : **fictifs**.
- Tout chiffre de performance ne sera donné qu'avec le matériel, la date et la version de modèle utilisés.

## OCR français (mis à jour le 01/11/2026)
`tesseract-ocr-fra` installé via apt dans l'environnement de développement : les accents sont conservés (« Étape », « côté »), test dédié. Sur une autre machine : `apt install tesseract-ocr-fra` ; sans ce modèle le pipeline retombe sur `eng` (accents perdus).
