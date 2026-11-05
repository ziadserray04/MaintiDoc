"""Parc d'équipements fictif et historiques d'interventions, reproductibles (aucun aléa).
Les mêmes données alimentent : les PDF d'historique du corpus, l'inventaire (equipement_id) et le futur serveur MCP."""
import hashlib

from corpus_data import BATTERIES, INVERTERS, battery_facts, errors_for, inverter_facts

SITES = ["Villa Agadir", "École Marrakech", "Ferme Meknès", "Atelier Casablanca", "Riad Essaouira",
         "Clinique Rabat", "Entrepôt Tanger", "Maison Oujda", "Hôtel Ouarzazate", "Coopérative Taroudant",
         "Lycée Fès", "Usine Kénitra", "Mosquée Safi", "Ferme Berkane"]
TYPES = ["Alarme", "Intervention", "Contrôle annuel", "Intervention"]


def _h(*parts) -> int:
    return int(hashlib.md5("|".join(map(str, parts)).encode()).hexdigest()[:8], 16)


def equipment_id(model: str) -> str:
    return f"{model}-01"


def build_park() -> dict:
    """{equipment_id: {model, family, site, history: [...], open_tickets: [...]}}"""
    all_f = [inverter_facts(i, s) for i, s in enumerate(INVERTERS)] + [battery_facts(i, s) for i, s in enumerate(BATTERIES)]
    park = {}
    for n, f in enumerate(all_f):
        eid, errs = equipment_id(f["model"]), errors_for(f)
        events = []
        for k in range(5):
            e = errs[_h(eid, "e", k) % len(errs)]
            kind = TYPES[_h(eid, "t", k) % len(TYPES)]
            month, day = 1 + _h(eid, "m", k) % 12, 1 + _h(eid, "d", k) % 28
            year = 2025 if k < 3 else 2026
            if year == 2026 and month > 9:
                month = 9
            events.append(dict(
                date=f"{year}-{month:02d}-{day:02d}", type=kind, code=e["code"] if kind != "Contrôle annuel" else None,
                summary=(f"{e['title']} ({e['code']}) : {e['action']}" if kind != "Contrôle annuel"
                         else "Contrôle visuel, serrage des bornes, contrôle des voyants : conforme."),
                technician=f"Technicien {1 + _h(eid, 'x', k) % 4}"))
        events.sort(key=lambda e: e["date"])
        tickets = []
        if n % 3 == 0:  # un équipement sur trois a un ticket ouvert
            last = next((e for e in reversed(events) if e["code"]), None)
            if last:
                tickets.append(dict(ticket_id=f"TCK-{1000 + n}", title=f"Suivi {last['code']} sur {eid}", status="ouvert",
                                    created=last["date"]))
        park[eid] = dict(model=f["model"], family=f["family"], site=SITES[n % len(SITES)], history=events, open_tickets=tickets)
    return park
