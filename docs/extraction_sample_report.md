# Vérification de l'extraction sur un échantillon

Exécutée le 2026-11-01, graine 7, OCR : Tesseract `fra`.

| Contrôle | Échantillon | Conformes | Taux |
|---|---|---|---|
| Lignes de tableau des codes d'erreur (titre, cause et action comparés à `facts.json`) | 60 | 60 | 100% |
| Légendes de figures retrouvées sur la bonne page | 30 | 30 | 100% |
| Pages OCR : ressemblance avec le texte d'origine (moyenne) | 16 pages | - | 89.9% |

Page OCR la moins bonne : `procedure_hns3_v1` page 6, ressemblance 83.7%.

Limites : l'échantillon vient du corpus synthétique ; la ressemblance OCR mesure la lecture de scans simulés, pas celle de vrais documents numérisés. Le texte de référence contient le pied de page, que l'ingestion retire volontairement : la ressemblance est donc légèrement sous-estimée.
