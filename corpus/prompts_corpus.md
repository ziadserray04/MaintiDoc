# prompts_corpus.md — traçabilité de l'usage de l'IA dans le corpus

Outil : Claude Sonnet 5.5 (via Claude Code). Étudiant : SERRAY (équipe solo). Les extraits de consignes ci-dessous sont les
messages réels de l'étudiant (orthographe d'origine, abrégés par « … » quand ils sont longs). Aucune sortie d'IA n'est
copiée telle quelle : les 43 PDF et 7 photos sont produits par le script `scripts/generate_corpus.py` (reproductible),
dont les valeurs sont contrôlées par des tests automatiques contre `facts.json`.

| Id | Date | Outil | Objet | Documents concernés |
|----|------|-------|-------|---------------------|
| P01 | 2026-10-31 | Claude Sonnet 5.5 | Génération du corpus synthétique (domaine, modèles, manuels, codes d'erreur) | manuels, codes_alarme, procedures, guides, bulletin_hns8_contradictoire, note_confidentielle, annexe_hnt15_piegee |
| P02 | 2026-11-01 | Claude Sonnet 5.5 | Réalisme : photos de panneaux, documents scannés, qualité « pour le RAG » | 7 photos du corpus (+15 hors corpus), procedure_hns3, procedure_hnb5 (scannées) |
| P03 | 2026-11-01 | Claude Sonnet 5.5 | Corrections : dates, doublon, page vide, OCR français | document_date, page vide de l'annexe, OCR `fra` |
| P04 | 2026-11-03 | Claude Sonnet 5.5 | Livrable 1 : fiches de sécurité, historiques d'équipements, inventaire | fiche_securite (2), historique (2), inventaire.csv |

## P01 — Génération du corpus (2026-10-31)
Consigne de l'étudiant : « peut tu me generer un bon corpus qui repond aux exigences ? » puis « essentilelle ce st qui soit
bien pour l rag ». Contexte fourni : prompt maître du projet, sujet PDF (30 à 50 documents, ≥ 2 familles, ≥ 2 scans,
≥ 2 contradictions, 1 injection, ≥ 2 groupes d'accès).
Sortie : générateur Python de PDF (ReportLab) + `facts.json` (valeurs de référence) + `manifest.json`.
Vérification humaine : tests automatiques sur les valeurs (poids, câble, seuils) ; relecture humaine par sondage faite par l'étudiant (voir `verifie_par`).

## P02 — Réalisme et photos (2026-11-01)
Consignes : « il contient des photos », « tu peut chercher les photos pour me donner le corpus complet », puis
« nn je veux ruen avec liscence » (aucun contenu tiers sous licence). Décision : les images sont dessinées par code
(panneaux de commande avec voyants, variantes normale / floue / sombre / plaque masquée) ; aucune photo réelle n'est utilisée.
Limite assumée : ce sont des dessins, pas des photos réelles ; ils ne valident pas un VLM en conditions réelles.

## P03 — Corrections (2026-11-01)
Corrections demandées ou découvertes en cours de route : ajout d'une date de document, un doublon exact (déplacé dans le
mode `--enriched`, hors corpus officiel), une page volontairement vide dans l'annexe piégée (détectée par le pipeline),
OCR configuré en français (`fra`) après avoir constaté la perte des accents avec `eng`.

## P04 — Livrable 1 (2026-11-03)
Consigne : consignes du livrable 1 (« regarde ca »), puis « nn cpg laisse meme les 22 photos ». Ajouts : fiches de sécurité
(onduleurs, batteries), historiques d'équipements (alignés sur le futur serveur MCP), mise en dossiers `famille_1` / `famille_2` /
`images`, génération de `inventaire.csv` et validateur automatique (30–50 lignes, correspondance fichiers ↔ inventaire).

## Analyse critique des erreurs de l'IA (½ page)
Erreurs réellement constatées pendant le travail, et ce qui les a détectées :
1. **Domaine non validé** : l'IA est partie par défaut sur des pompes/compresseurs avant que l'étudiant fixe le domaine
   (solaire : onduleurs + batteries). Détectée par l'étudiant.
2. **Taille du corpus** : première version à 71 documents (> 50 exigés) ; la borne du test avait même été élargie pour passer.
   Détectée en relisant les consignes ; corpus scindé en « officiel » (50 lignes) et « enrichi » (hors livrable).
3. **Photos oubliées dans le décompte** : l'IA avait certifié « 50 fichiers » en ne comptant que les PDF ; les photos comptent
   aussi. Corrigé : 43 PDF + 7 photos = 50 ; 15 autres photos gardées dans `eval_images/` comme images de test, hors corpus.
4. **Chiffre faux dans un rapport** : 28 codes batterie annoncés au lieu de 27 ; corrigé après recomptage automatique.
5. **Licences citées de mémoire** : l'IA a évoqué des jeux/guides sous licence (CC BY-NC-SA, CC BY-SA, etc.) sans les avoir
   ouverts ni vérifiés ; aucun n'a été utilisé. Règle retenue : rien de tiers.
6. **Suggestions Kaggle non vérifiées** : titres proposés sans consultation des pages ; écartés.
7. **OCR sans accents** : OCR anglais par défaut ; corrigé en `fra`.
8. **Sur-ajustement des évaluations** : le score 64/64 vient d'un jeu réglé sur ses propres échecs ; le jeu de 70 scénarios
   (53/70 au premier passage) n'est plus indépendant après correctifs. Ces scores ne sont pas des mesures à l'aveugle.
9. **Régression découverte tard** : l'ajout des fiches de sécurité a fait concurrencer deux passages (stockage batterie,
   fusible) ; détectée par les tests, corrigée par une phrase moins générique et un reclassement lexical.

Conclusion : l'IA produit vite mais affirme parfois sans vérifier (comptes, licences, domaine). Les garde-fous qui ont
fonctionné sont les tests automatiques, le validateur d'inventaire et la relecture des consignes. La colonne `verifie_par` de l'inventaire indique l'étudiant qui a relu le corpus par sondage ; cette relecture n'est pas exhaustive.
