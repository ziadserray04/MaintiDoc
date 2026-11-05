"""Documents complémentaires, moins « propres » que les manuels : retours terrain (style libre), FAQ, glossaire,
tableaux comparatifs, bulletins et note de sécurité. Toutes les valeurs viennent des faits du modèle."""
import hashlib

from corpus_data import BRAND, errors_for, leds_for
from corpus_helpers import H2, P, chapter, tbl


def _h(*parts) -> int:
    return int(hashlib.md5("|".join(map(str, parts)).encode()).hexdigest()[:8], 16)


SITES = ["villa à Agadir", "école de Marrakech", "ferme près de Meknès", "atelier à Casablanca", "riad à Essaouira",
         "clinique à Rabat", "entrepôt à Tanger", "maison à Oujda"]
OPEN = ["Appel client : {sym}.", "Sur place, constat : {sym}.", "RAS à l'arrivée sauf que {sym}.", "Client dit que {sym}, depuis hier."]
CLOSE = ["Remis en service, client prévenu.", "OK après intervention, à resurveiller 48 h.", "Rapport signé, photo de la plaque prise.",
         "Pas de pièce changée. Dossier clos."]


def field_notes_flow(f):
    """Notes de terrain du SAV : phrases courtes, abréviations, ordre libre. Aucune contradiction avec les manuels."""
    m = f["model"]
    errs = errors_for(f)
    picks = sorted({_h(m, i) % len(errs) for i in range(14)})[:8]
    flow = chapter(1, "Notes de terrain SAV (usage interne)", first=True) + [
        P(f"Carnet de notes des techniciens {BRAND} pour le {m}. Document interne informel, non contractuel ; en cas de doute, le "
          f"manuel du {m} et le guide des codes du {m} font foi. Document fictif de démonstration.")]
    for n, i in enumerate(picks, 1):
        e = errs[i]
        site = SITES[_h(m, "site", i) % len(SITES)]
        day = 1 + _h(m, "day", i) % 27
        o = OPEN[_h(m, "o", i) % len(OPEN)].format(sym=f"le voyant {e['led'].lower()} et code {e['code']} à l'écran")
        c = CLOSE[_h(m, "c", i) % len(CLOSE)]
        flow += [H2(f"Intervention {n} - {site} - {day:02d}/{1 + _h(m, 'mo', i) % 12:02d}"),
                 P(f"{o} {m}. Cause trouvée : {e['cause'][0].lower() + e['cause'][1:]} "
                   f"Action : {e['action'][0].lower() + e['action'][1:]} {c}")]
    flow += [H2("Rappels entre collègues"),
             P(f"Toujours relever le modèle sur la plaque avant d'ouvrir le guide : le voyant orange fixe du {m} ne veut pas dire "
               "la même chose que sur les autres modèles ni sur les batteries. Consigner avant d'ouvrir le capot, sans exception."),
             P("Prendre une photo de la plaque et du panneau pour le dossier. Si la plaque est illisible, ne pas deviner le modèle.")]
    return flow


def orange_comparison_flow(models):
    rows = [["Modèle", "Famille", "Voyant orange fixe"]]
    for f in models:
        rows.append([f["model"], f["family"], dict(leds_for(f))["Orange fixe"]])
    return chapter(1, "Comparatif du voyant orange fixe", first=True) + [
        P("Ce tableau montre qu'un même voyant n'a pas le même sens selon le modèle. Il ne remplace pas le manuel du modèle."),
        tbl(rows, [90, 90, 320])]


def faq_flow(fam):
    onduleur = fam == "onduleur"
    qa = ([("Pourquoi mon onduleur s'arrête-t-il l'après-midi ?", "Une limitation de puissance liée à la température interne est probable ; vérifier la ventilation. Le seuil dépend du modèle."),
           ("Que faire si le voyant rouge clignote ?", "Un défaut d'isolement ou de fuite à la terre est possible : mettre l'installation hors tension et appeler un installateur habilité."),
           ("Puis-je ouvrir le capot moi-même ?", "Non. Seul un technicien habilité peut intervenir ; les panneaux restent sous tension en présence de lumière."),
           ("Comment connaître mon modèle ?", "Il figure sur la plaque signalétique. Si elle est illisible, ne pas deviner : contacter le SAV."),
           ("L'horloge est fausse, est-ce grave ?", "Non, c'est une information (E801) sans danger ; elle se règle depuis l'assistant de configuration.")]
          if onduleur else
          [("Pourquoi ma batterie ne charge-t-elle pas en hiver ?", "La charge est interdite sous une température minimale qui dépend du modèle ; le voyant orange fixe l'indique."),
           ("Que faire si la batterie s'est éteinte ?", "Elle est peut-être en veille profonde (B702) : relancer par le bouton de démarrage après contrôle."),
           ("Puis-je ajouter un module moi-même ?", "Non. Le nombre de modules en parallèle est limité et dépend du modèle ; contacter un installateur habilité."),
           ("Quelle batterie avec quel onduleur ?", "Voir la matrice de compatibilité du manuel de l'onduleur ; elle dépend de la puissance et du nombre de phases."),
           ("La batterie chauffe, est-ce normal ?", "Un léger échauffement est normal ; une alarme de température haute demande de ventiler le local.")])
    flow = chapter(1, f"Foire aux questions - {'onduleurs' if onduleur else 'batteries'}", first=True)
    for q, a in qa:
        flow += [H2(q), P(a)]
    return flow


def glossary_flow():
    t = [["Terme", "Définition"], ["MPPT", "Suivi du point de puissance maximale des panneaux."], ["HNBus", "Bus de communication entre onduleur et batterie."],
         ["LFP", "Lithium fer phosphate, technologie des batteries HelioNova."], ["PE", "Conducteur de protection (terre)."],
         ["SOC", "État de charge de la batterie, en pourcentage."], ["Consignation", "Mise hors tension et verrouillage avant intervention."],
         ["Limitation de puissance", "Réduction automatique de la puissance pour protéger l'appareil."], ["BMS", "Système de gestion de la batterie."],
         ["Isolement", "Résistance entre les conducteurs et la terre ; un défaut provoque un arrêt."]]
    return chapter(1, "Glossaire", first=True) + [tbl(t, [130, 370])]


def firmware_bulletin_flow(n, topic, body):
    return [P(f"Objet : {topic}."), P(body), P(f"Bulletin fictif n° {n}. Aucune valeur réelle.")]


def safety_flow(fam="batterie"):
    if fam == "onduleur":
        return chapter(1, "Fiche de sécurité - onduleurs solaires", first=True) + [
            P("<b>AVERTISSEMENT</b> : les chaînes photovoltaïques restent sous tension en présence de lumière, même onduleur arrêté."),
            P("Ne jamais débrancher un connecteur DC en charge : un arc électrique peut provoquer des brûlures graves."),
            P("Avant toute intervention : consigner (disjoncteur AC, sectionneur AC, sectionneur DC), attendre 5 minutes, vérifier l'absence de tension."),
            H2("Équipements"), P("Gants isolants, lunettes de protection, chaussures de sécurité. Intervention réservée à une personne habilitée."),
            H2("Conduite à tenir"), P("En cas de fumée, d'odeur ou d'échauffement anormal : évacuer, couper l'alimentation si c'est sans danger, appeler les secours puis le SAV.")]
    return chapter(1, "Fiche de sécurité - batteries LFP", first=True) + [
        P("<b>AVERTISSEMENT</b> : une batterie reste sous tension même hors service. Ne jamais court-circuiter les bornes."),
        P("En cas d'échauffement anormal, d'odeur ou de gonflement : évacuer, ne pas manipuler, appeler les secours puis le SAV."),
        P("Entreposage : local sec et tempéré, conforme à la fiche du modèle concerné."),
        H2("Équipements"), P("Gants isolants, lunettes, chaussures de sécurité ; extincteur adapté à proximité du local batterie.")]


def history_flow(fam, park):
    """Historique d'interventions du parc (mêmes données que le serveur MCP de démonstration)."""
    title = "onduleurs" if fam == "onduleur" else "batteries"
    flow = chapter(1, f"Historique des interventions - {title}", first=True) + [
        P("Extrait fictif du registre de maintenance. Les identifiants d'équipement sont ceux du parc de démonstration.")]
    for eid, d in park.items():
        if d["family"] != fam:
            continue
        flow += [H2(f"{eid} - {d['model']} - {d['site']}"),
                 tbl([["Date", "Type", "Code", "Résumé", "Intervenant"]] +
                     [[e["date"], e["type"], e["code"] or "-", e["summary"], e["technician"]] for e in d["history"]], [60, 70, 40, 250, 70])]
        if d["open_tickets"]:
            t = d["open_tickets"][0]
            flow.append(P(f"Ticket ouvert : {t['ticket_id']} - {t['title']} (créé le {t['created']})."))
    return flow
