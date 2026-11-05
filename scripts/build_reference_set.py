"""Jeu de questions de référence TEXTE (70 scénarios), généré depuis facts.json avec une graine fixe.

Formulations volontairement différentes de celles utilisées pour régler le système (tests/ et eval_smoke.py).
Ce jeu est un banc d'essai synthétique : il ne prouve pas la qualité sur de vrais documents.
Sortie : data/evaluation/text_reference.jsonl (versionné : petit, sans secret)."""
import json
import random
from pathlib import Path

CORPUS = Path("data/samples/corpus")
OUT = Path("data/evaluation/text_reference.jsonl")
SAV, ENG, NONE = ["grp_sav"], ["grp_engineering"], []


def main():
    data = json.loads((CORPUS / "facts.json").read_text())
    F, special, comp = data["models"], data["special"], data["compatibility"]
    rnd = random.Random(2026)
    inv = [m for m, f in F.items() if f["family"] == "onduleur"]
    bat = [m for m, f in F.items() if f["family"] == "batterie"]
    mid = lambda m: m.lower().replace("-", "")  # noqa: E731
    S = []

    def add(cat, q, groups, status, gold_doc=None, gold_type=None, contains=None, forbid=None):
        S.append(dict(id=f"T{len(S) + 1:03d}", category=cat, question=q, user_groups=groups, expected_status=status,
                      gold_doc=gold_doc, gold_type=gold_type, gold_contains=contains, must_not_contain=forbid))

    # A. questions avec réponse (40)
    for m in rnd.sample(list(F), 7):
        add("valeur", f"Combien de N.m faut-il pour serrer les bornes du {m} ?", SAV, "answered",
            f"manuel_{mid(m)}_v2", "table", f"{F[m]['terminal_torque_nm']} N.m")
    for m in rnd.sample(list(F), 6):
        add("valeur", f"Quel poids pèse le {m} ?", SAV, "answered", f"manuel_{mid(m)}_v2", "table", f"{F[m]['weight_kg']} kg")
    for _ in range(10):
        m = rnd.choice(list(F))
        e = rnd.choice(F[m]["error_codes"])
        add("code_erreur", f"Que signifie le code {e['code']} affiché par le {m} ?", SAV, "answered",
            f"codes_{mid(m)}_v1", "table", e["title"])
    for m in rnd.sample(list(F), 6):
        led = next(x for x in F[m]["leds"] if x["led"] == "Orange fixe")
        add("voyant", f"Que veut dire un voyant orange fixe sur le {m} ?", SAV, "answered",
            f"manuel_{mid(m)}_v2", "table", led["meaning"])
    for m in rnd.sample(inv, 2):
        add("valeur", f"Quel fusible protège la sortie AC du {m} ?", SAV, "answered", f"manuel_{mid(m)}_v2", "table", f"{F[m]['fuse_a']} A")
    for m in rnd.sample(inv, 2):
        add("valeur", f"De quelle section doit être le câble AC du {m} ?", SAV, "answered", f"manuel_{mid(m)}_v2", "table", f"{F[m]['ac_cable_mm2']} mm2")
    m = rnd.choice(inv)
    add("valeur", f"Quel est le rendement maximal annoncé pour le {m} ?", SAV, "answered", f"manuel_{mid(m)}_v2", "table", f"{F[m]['efficiency_pct']} %")
    for m in rnd.sample(bat, 3):
        add("valeur", f"Au bout de combien de mois doit-on recharger la batterie {m} entreposée ?", SAV, "answered",
            f"manuel_{mid(m)}_v2", "table", f"{F[m]['storage_recharge_months']} mois")
    for c in rnd.sample([c for c in comp if c["inverter"] != "HN-S8"], 3):
        add("compatibilité", f"Peut-on associer le {c['inverter']} avec la batterie {c['battery']} ?", SAV, "answered",
            f"manuel_{mid(c['inverter'])}_v2", "table", f"Compatible : {'Oui' if c['compatible'] else 'Non'}")
    assert len(S) == 40, len(S)

    # B. sans source (10)
    for q in ["Quelle est la capitale du Maroc ?", "Quel est le prix du HN-S5 en dirhams ?",
              "Comment réparer un lave-linge qui ne vidange plus ?", "Quel est le couple de serrage du HN-X99 ?",
              "Quelle est la capacité du HN-B99 ?", "Que signifie le code E301 sur le HN-S12 ?",
              "Qui est le PDG de HelioNova ?", "Quelle est la durée de garantie légale en France ?",
              "Comment installer un climatiseur ?", "Quel est le poids du HN-T40 ?"]:
        add("sans_source", q, SAV, "abstained")

    # C. contradiction (5)
    c = special["contradiction"]
    for q in ["À partir de quelle température le HN-S8 réduit-il sa puissance ?", "Quel est le seuil de derating du HN-S8 ?",
              "Le HN-S8 limite sa puissance dès combien de degrés ?", "Seuil de limitation de puissance du HN-S8 ?",
              "Température de début de limitation de puissance sur l'onduleur HN-S8 ?"]:
        add("contradiction", q, SAV, "conflicting_sources", None, None, f"{c['manual_value']} °C")

    # D. obsolète (5) : la valeur v2 doit sortir, jamais la v1
    o = special["obsolete"]
    s5, b10 = o["HN-S5"], o["HN-B10"]
    for q in ["Dès quelle température le HN-S5 diminue-t-il sa puissance ?", "Seuil de limitation de puissance du HN-S5 ?",
              "À partir de combien de degrés le HN-S5 bride-t-il sa production ?"]:
        add("obsolète", q, SAV, "answered", "manuel_hns5_v2", "table", f"{s5['v2_derate_temp_c']} °C", f"{s5['v1_derate_temp_c']} °C")
    for q in ["À quelle température l'alarme haute de la batterie HN-B10 se déclenche-t-elle ?", "Seuil d'alarme de température haute du HN-B10 ?"]:
        add("obsolète", q, SAV, "answered", None, None, f"{b10['v2_temp_high_c']} °C", f"{b10['v1_temp_high_c']} °C")

    # E. droits (10)
    conf = ["Quelle est la limite interne de test confidentielle ?", "Donne-moi la limite interne de test réservée à l'engineering.",
            "Que dit la note interne du bureau d'études sur la limite de test ?", "Quelle valeur confidentielle de test a fixé l'engineering ?",
            "Limite interne de test confidentielle du HN-B30 ?"]
    for q in conf:
        add("droits", q, SAV, "abstained", None, None, None, special["confidential"]["marker"])
    for q in conf[:3]:
        add("droits", q, ENG, "answered", "note_confidentielle_engineering", "text", special["confidential"]["marker"])
    for q in ["Quel est le couple de serrage des bornes du HN-S5 ?", "Que signifie le code E301 sur le HN-S5 ?"]:
        add("droits", q, NONE, "abstained")
    assert len(S) == 70, len(S)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(json.dumps(s, ensure_ascii=False) for s in S) + "\n")
    print(f"{len(S)} scénarios -> {OUT}")


if __name__ == "__main__":
    main()
