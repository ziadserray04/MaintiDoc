# Périmètre du projet

## Domaine (décision du 2026-10-27) : maintenance d'installations solaires
Choisi pour : marché en croissance, techniciens terrain peu formés aux codes d'erreur de chaque marque, risque d'usage faible, démonstration visuelle (voyants, plaques signalétiques).

Historique des pistes écartées : hydroélectrique (FIST), aéronautique (FAA), pompes/compresseurs, médical. Aucun jeu de données public gratuit ne couvre toutes les exigences du PDF.

## Deux familles d'équipements liées
| Famille | Modèles fictifs (marque fictive « HelioNova ») |
|---|---|
| **Onduleurs** | HN-S3, S5, S6, S8, S10 (monophasés), HN-T15, T20 (triphasés) |
| **Batteries de stockage** | HN-B5, B7, B10, B13, B15, B20, B30 (kWh) |

Lien : la batterie se branche sur l'onduleur et ils communiquent ; une panne de l'un peut déclencher une alarme sur l'autre. Les voyants orange se ressemblent mais n'ont pas le même sens (onduleur vs batterie, et série S vs série T).

## Corpus
Corpus **fictif** généré par `scripts/generate_corpus.py` (graine fixe, reproductible), en français, 49 documents : manuel, guide de codes d'erreur et procédure de maintenance par modèle, 2 guides généraux, 2 manuels obsolètes, 1 bulletin contradictoire, 1 note confidentielle, 1 annexe piégée (injection), 2 procédures scannées. Les vérités de terrain (faits, codes, seuils) sont exportées dans `facts.json` pour construire l'évaluation. Les marques et modèles n'existent pas.

Sources réelles optionnelles pour la crédibilité : documentation Libre Solar (CC BY-SA 4.0). Évaluation de la recherche : ViDoRe Industrial (licence à vérifier).

## Intention produit
Code indépendant du corpus : un client branche ses manuels, équipements et groupes d'accès par configuration. Un modèle absent du corpus doit entraîner une abstention, pas une réponse inventée.

## À vérifier avant commercialisation
Licences des modèles (Qwen2.5-VL-7B, BGE-M3, reranker, CLIP) et des dépendances ; licences de tout document réel ajouté.

## Hors périmètre
Pilotage d'équipement, diagnostic garanti, remplacement des procédures de sécurité ou d'un technicien habilité.
