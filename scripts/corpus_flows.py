"""Contenu long des documents du corpus fictif (manuels, guides de codes, procédures).
Toutes les valeurs viennent des « faits » du modèle : elles sont identiques dans tous les documents."""
from reportlab.platypus import Spacer

from corpus_data import BRAND, BATTERIES, INVERTERS, battery_facts, compat, errors_for, inverter_facts, leds_for, specs_rows
from corpus_helpers import H2, P, chapter, nameplate_drawing, panel_drawing, steps, tbl

_ALL_INV = [inverter_facts(i, s) for i, s in enumerate(INVERTERS)]
_ALL_BAT = [battery_facts(i, s) for i, s in enumerate(BATTERIES)]

SYMBOLS = [["Symbole", "Signification"], ["AVERTISSEMENT", "Risque de blessure grave ou mortelle si la consigne n'est pas respectée."],
           ["ATTENTION", "Risque de dommage matériel."], ["Information", "Conseil d'utilisation sans conséquence sur la sécurité."]]
SAFETY_LOCKOUT = [
    "Prévenir les occupants et signaler l'intervention.",
    "Ouvrir le disjoncteur AC de l'installation puis le sectionneur AC de l'appareil.",
    "Ouvrir le sectionneur DC (côté panneaux ou batterie) et le verrouiller.",
    "Attendre 5 minutes que les condensateurs se déchargent.",
    "Vérifier l'absence de tension avec un appareil de mesure adapté.",
    "Poser une étiquette de consignation nominative.",
]


def _ctx(f):
    return dict(model=f["model"], kind="l'onduleur" if f["family"] == "onduleur" else "la batterie")


# ===================================================================== ONDULEUR : MANUEL
def inverter_manual(s, version):
    m, leds = s["model"], leds_for(s)
    rev = [["Version", "Modification"], ["1.0", "Première édition du manuel."],
           ["2.0", "Seuils de limitation de puissance et d'isolement mis à jour ; matrice de compatibilité ajoutée."]]
    f = (chapter(1, "Introduction", first=True) + [
        P(f"Version {version}. Document fictif de démonstration : aucune valeur n'est réelle."),
        P(f"Ce manuel décrit l'installation, la mise en service, l'exploitation et la maintenance de premier niveau de "
          f"l'onduleur solaire {BRAND} {m}, d'une puissance de {s['power_kw']} kW. Il s'adresse aux installateurs et aux "
          "techniciens de service après-vente habilités."),
        P(f"Documents associés : « Guide des codes d'erreur {m} » et « Procédure de maintenance {m} ». Les codes d'erreur et "
          "les seuils diffèrent d'un modèle à l'autre : ne jamais utiliser le guide d'un autre modèle."),
        H2("Symboles utilisés"), tbl(SYMBOLS, [120, 380])])
    f += chapter(2, "Sécurité") + [
        P("<b>AVERTISSEMENT</b> : les chaînes photovoltaïques restent sous tension en présence de lumière, même lorsque "
          "l'onduleur est arrêté. Seule une personne habilitée peut intervenir sur l'appareil."),
        P("Équipements de protection individuelle : gants isolants, lunettes de protection, chaussures de sécurité."),
        H2("Consignation avant intervention")] + steps(SAFETY_LOCKOUT) + [
        P("<b>AVERTISSEMENT</b> : ne jamais débrancher un connecteur DC en charge. Un arc électrique peut provoquer des brûlures graves."),
        P("Ce document ne remplace ni la formation, ni les procédures de sécurité de l'entreprise, ni un technicien habilité.")]
    f += chapter(3, "Description de l'appareil") + [
        P(f"Le {m} est un onduleur {'monophasé' if s['phases'] == 1 else 'triphasé'} à {s['mppt']} entrée(s) MPPT. Il convertit "
          "le courant continu des panneaux en courant alternatif injecté sur le réseau, et pilote une batterie de stockage "
          "par le bus de communication HNBus."),
        H2("Raccordements"),
        tbl([["Repère", "Fonction", "Remarque"], ["DC+ / DC-", "Entrées des chaînes photovoltaïques", f"{s['mppt']} entrée(s), {s['vdc_max']} V maximum"],
             ["AC L / N / PE" if s["phases"] == 1 else "AC L1 L2 L3 N PE", "Sortie vers le réseau", f"Câble {s['ac_cable_mm2']} mm2"],
             ["BAT", "Bus de communication vers la batterie", "Câble blindé, adresse à régler"],
             ["RS485", "Compteur d'énergie", "Optionnel"], ["USB", "Service et mise à jour du firmware", "Réservé au SAV"]], [90, 220, 190]),
        Spacer(1, 8), panel_drawing(m, leds, "Figure 3.1"), Spacer(1, 8), nameplate_drawing(s, "Figure 3.2"),
        P("Le modèle exact figure sur la plaque signalétique, sur le côté droit du boîtier. Le relever avant toute consultation du guide des codes.")]
    f += chapter(4, "Caractéristiques techniques") + [tbl([["Caractéristique", "Valeur"]] + [
        ["Puissance nominale", f"{s['power_kw']} kW"], ["Nombre de phases", str(s["phases"])], ["Entrées MPPT", str(s["mppt"])],
        ["Tension DC maximale", f"{s['vdc_max']} V"], ["Courant maximal par chaîne", f"{s['dc_string_a_max']} A"],
        ["Courant AC nominal", f"{s['ac_current_a']} A"], ["Rendement maximal", f"{s['efficiency_pct']} %"],
        ["Indice de protection", f"IP{s['ip']}"], ["Température ambiante", f"{s['ambient_min_c']} à {s['ambient_max_c']} °C"],
        ["Limitation de puissance à partir de", f"{s['derate_temp_c']} °C"], ["Seuil de défaut d'isolement", f"{s['iso_kohm']} kΩ"],
        ["Couple de serrage des bornes", f"{s['terminal_torque_nm']} N.m"], ["Calibre du fusible AC", f"{s['fuse_a']} A"],
        ["Masse (poids)", f"{s['weight_kg']} kg"], ["Section de câble AC", f"{s['ac_cable_mm2']} mm2"], ["Communication", "HNBus (batterie), RS485 (compteur), USB (service)"]], [260, 240]),
        P("Les valeurs ci-dessus sont propres au modèle " + m + ".")]
    f += chapter(5, "Installation") + [
        H2("Choix de l'emplacement"),
        P("Installer l'onduleur à l'abri du rayonnement direct, sur un mur vertical porteur, à hauteur d'homme. Laisser 30 cm libres "
          "de chaque côté et 50 cm sous l'appareil pour la ventilation. Ne pas installer dans un local fermé non ventilé."),
        P(f"La limitation de puissance débute à {s['derate_temp_c']} °C de température interne : un emplacement mal ventilé réduit la production."),
        H2("Raccordement AC"),
        P(f"<b>AVERTISSEMENT</b> : mettre hors tension (voir chapitre 2) avant d'ouvrir le capot. Utiliser un câble de {s['ac_cable_mm2']} mm2 "
          f"protégé par un fusible ou disjoncteur de {s['fuse_a']} A. Serrer les bornes au couple de {s['terminal_torque_nm']} N.m.")] + steps([
        "Passer le câble dans le presse-étoupe sans dépasser la longueur dénudée de 12 mm.",
        f"Raccorder la terre (PE) en premier, puis {'le neutre et la phase' if s['phases'] == 1 else 'le neutre et les trois phases'}.",
        f"Serrer chaque borne à {s['terminal_torque_nm']} N.m et tirer légèrement sur le câble pour vérifier le serrage.",
        "Refermer le capot et serrer les vis de fermeture."]) + [
        H2("Raccordement DC"),
        P(f"Ne pas dépasser {s['vdc_max']} V en circuit ouvert sur une entrée (code E201) ni {s['dc_string_a_max']} A par chaîne. "
          "Respecter la polarité : une inversion provoque le code E203 et peut endommager l'appareil."),
        H2("Mise à la terre"),
        P("Relier la borne de terre de l'onduleur à la prise de terre de l'installation. Une terre absente provoque le code E303.")]
    f += chapter(6, "Mise en service") + [
        P("À la première mise sous tension, l'assistant de configuration guide l'installateur. Tant que l'horloge et le profil de pays "
          "ne sont pas réglés, les informations E801 et E802 s'affichent.")] + steps([
        "Fermer le sectionneur DC puis le sectionneur AC.", "Choisir la langue de l'interface.",
        "Régler la date et l'heure (supprime l'information E801).", "Sélectionner le profil de pays (supprime l'information E802).",
        "Régler l'adresse HNBus de l'onduleur si une batterie est raccordée.", "Lancer la détection de la batterie.",
        "Vérifier que le voyant vert clignote pendant le démarrage puis reste fixe en production.",
        "Relever la résistance d'isolement affichée : elle doit rester supérieure à " + f"{s['iso_kohm']} kΩ."]) + [
        H2("Paramètres par défaut"),
        tbl([["Paramètre", "Valeur par défaut"], ["Seuil de limitation de puissance", f"{s['derate_temp_c']} °C"],
             ["Seuil d'isolement", f"{s['iso_kohm']} kΩ"], ["Adresse HNBus", "1"], ["Mode d'injection", "Injection totale"]], [260, 240])]
    f += chapter(7, "Exploitation") + [
        P("L'écran affiche la puissance instantanée, l'énergie produite, l'état de la batterie et les éventuels codes d'erreur."),
        H2("Voyants du panneau"), tbl([["Voyant", "Signification"]] + [[a, b] for a, b in leds], [150, 350]), Spacer(1, 6),
        panel_drawing(m, leds, "Figure 7.1"),
        P(f"Sur ce modèle, le voyant orange fixe signifie : {s['orange_fixed']}. Sur une batterie, le même voyant orange fixe "
          "signifie une température hors plage de charge : ne pas confondre les deux appareils."),
        H2("Limitation de puissance"),
        P(f"Lorsque la température interne atteint {s['derate_temp_c']} °C, l'onduleur réduit progressivement sa puissance pour se "
          "protéger (code E401). La puissance se rétablit d'elle-même après refroidissement.")]
    f += chapter(8, "Association avec une batterie") + [
        P("L'onduleur et la batterie échangent leur état par le bus HNBus. Une perte de communication provoque le code E501 sur "
          "l'onduleur et le code B401 sur la batterie, avec un voyant orange clignotant sur les deux appareils."),
        P(f"Règle de compatibilité : la capacité de la batterie ne doit pas dépasser {s['power_kw'] * 2:g} kWh pour le {m}"
          + " ; les batteries de plus de 15 kWh sont réservées aux onduleurs triphasés."),
        H2("Matrice de compatibilité"),
        tbl([["Batterie", "Capacité", "Compatible", "Remarque"]] + [
            [b["model"], f"{b['capacity_kwh']:g} kWh", "Oui" if compat(s, b)[0] else "Non", compat(s, b)[1]] for b in _ALL_BAT],
            [100, 90, 90, 220])]
    f += chapter(9, "Dépannage de premier niveau") + [
        P("Le tableau suivant donne les premières vérifications. Pour tout code d'erreur, consulter le guide des codes du modèle."),
        tbl([["Symptôme", "Vérification", "Code associé"],
             ["Aucune production en plein jour", "Contrôler les sectionneurs DC et AC et la tension DC", "E202, E104"],
             ["Production réduite par forte chaleur", f"Contrôler la ventilation ; limitation dès {s['derate_temp_c']} °C", "E401"],
             ["Voyant rouge clignotant", f"Mesurer l'isolement : seuil {s['iso_kohm']} kΩ", "E301, E302"],
             ["Voyant orange clignotant", "Contrôler le câble HNBus et les adresses", "E501, E503"],
             ["Écran éteint", "Contrôler le fusible AC et l'alimentation", "E604"],
             ["Production nulle, réseau présent", "Contrôler la tension et la fréquence du réseau", "E101, E102, E103"]], [170, 230, 100])]
    f += chapter(10, "Maintenance") + [
        P(f"La maintenance préventive est décrite dans la « Procédure de maintenance {m} ». Les bornes se resserrent au couple de "
          f"{s['terminal_torque_nm']} N.m. Ne jamais ouvrir l'appareil au-delà du compartiment de raccordement."),
        tbl([["Fréquence", "Action"], ["Mensuelle", "Vérifier les voyants et l'absence de code actif"],
             ["Trimestrielle", "Nettoyer les grilles de ventilation"], ["Annuelle", "Resserrer les bornes et mesurer l'isolement"]], [140, 360])]
    f += chapter(11, "Mise hors service et recyclage") + [
        P("Consigner l'appareil (chapitre 2), débrancher les câbles dans l'ordre inverse du raccordement, puis démonter. L'appareil est "
          "un déchet d'équipement électrique : le remettre à une filière de recyclage agréée.")]
    f += chapter(12, "Annexes") + [
        H2("Glossaire"), tbl([["Terme", "Définition"], ["MPPT", "Suivi du point de puissance maximale des panneaux"],
                              ["Isolement", "Résistance entre les conducteurs et la terre"], ["HNBus", "Bus de communication onduleur - batterie"],
                              ["Derating", "Limitation de puissance pour protéger l'appareil"]], [120, 380]),
        H2("Historique des révisions"), tbl(rev, [80, 420])]
    return f


# ===================================================================== BATTERIE : MANUEL
def battery_manual(s, version):
    m, leds = s["model"], leds_for(s)
    f = (chapter(1, "Introduction", first=True) + [
        P(f"Version {version}. Document fictif de démonstration : aucune valeur n'est réelle."),
        P(f"Ce manuel décrit l'installation, la mise en service, l'exploitation et la maintenance de premier niveau de la batterie "
          f"de stockage {BRAND} {m} (LFP, {s['capacity_kwh']:g} kWh utiles). Il s'adresse aux installateurs et aux techniciens habilités."),
        P(f"Documents associés : « Guide des codes d'erreur {m} » et « Procédure de maintenance {m} »."), H2("Symboles utilisés"),
        tbl(SYMBOLS, [120, 380])])
    f += chapter(2, "Sécurité") + [
        P("<b>AVERTISSEMENT</b> : une batterie lithium contient une énergie élevée. Un court-circuit, une surchauffe ou une décharge "
          "profonde peuvent provoquer un incendie. Ne jamais ouvrir le boîtier."),
        P("Équipements de protection : gants isolants, lunettes, outils isolés."), H2("Consignation")] + steps([
        "Arrêter l'onduleur associé.", "Ouvrir le sectionneur DC de la batterie et le verrouiller.",
        "Débrancher le câble de communication HNBus.", "Attendre 5 minutes.", "Vérifier l'absence de tension aux bornes.",
        "Poser une étiquette de consignation nominative."]) + [
        P("<b>AVERTISSEMENT</b> : ne jamais forcer la charge à basse température "
          f"(charge interdite sous {s['temp_charge_min_c']} °C) : risque de dommage irréversible des cellules.")]
    f += chapter(3, "Description de l'appareil") + [
        P(f"La {m} est une batterie murale de {s['capacity_kwh']:g} kWh, de tension nominale {s['voltage_v']} V, gérée par un système de "
          "gestion de batterie (BMS) qui surveille la tension, le courant et la température de chaque cellule."),
        Spacer(1, 4), panel_drawing(m, leds, "Figure 3.1"), Spacer(1, 8), nameplate_drawing(s, "Figure 3.2"),
        P("Le modèle exact figure sur la plaque signalétique, sur la face avant. Le relever avant toute consultation du guide des codes.")]
    f += chapter(4, "Caractéristiques techniques") + [tbl([["Caractéristique", "Valeur"]] + [
        ["Capacité utile", f"{s['capacity_kwh']:g} kWh"], ["Tension nominale", f"{s['voltage_v']} V"],
        ["Technologie", "LFP (lithium fer phosphate)"], ["Courant de charge maximal", f"{s['max_charge_a']} A"],
        ["Alarme de température haute", f"{s['temp_high_c']} °C"], ["Charge interdite sous", f"{s['temp_charge_min_c']} °C"],
        ["Cycles garantis", str(s["cycles"])], ["Écart maximal entre cellules", f"{s['cell_delta_mv']} mV"],
        ["Réserve minimale de charge", f"{s['soc_reserve_pct']} %"], ["Consommation en veille", f"{s['standby_w']} W"],
        ["Couple de serrage des bornes", f"{s['terminal_torque_nm']} N.m"], ["Section des câbles DC", f"{s['dc_cable_mm2']} mm2"],
        ["Modules en parallèle (maximum)", str(s["modules_parallel_max"])], ["Masse (poids)", f"{s['weight_kg']} kg"],
        ["Recharge si stockage prolongé", f"tous les {s['storage_recharge_months']} mois"],
        ["Indice de protection", f"IP{s['ip']}"]], [260, 240]), P("Les valeurs ci-dessus sont propres au modèle " + m + ".")]
    f += chapter(5, "Installation") + [
        P(f"Installer la batterie dans un local tempéré et ventilé, à l'abri de la pluie, sur un mur capable de supporter {s['weight_kg']} kg. "
          f"L'alarme de température haute se déclenche à {s['temp_high_c']} °C : éviter les locaux exposés au soleil."),
        P(f"<b>AVERTISSEMENT</b> : la batterie pèse {s['weight_kg']} kg ; la manutention se fait à deux personnes avec un équipement de levage adapté.")]
    f += chapter(6, "Raccordement et mise en service") + [
        P(f"Utiliser des câbles DC de {s['dc_cable_mm2']} mm2. Serrer les bornes au couple de {s['terminal_torque_nm']} N.m. "
          "Respecter la polarité : une inversion provoque un court-circuit (code B503).")] + steps([
        "Vérifier que le sectionneur DC est ouvert.", f"Raccorder les câbles DC et serrer à {s['terminal_torque_nm']} N.m.",
        "Raccorder le câble de communication HNBus à l'onduleur.", "Régler l'adresse de la batterie (jamais deux batteries à la même adresse : B403).",
        "Fermer le sectionneur DC.", "Appuyer sur le bouton de démarrage : le voyant vert clignote puis reste fixe.",
        "Régler l'horloge depuis l'onduleur (sinon information B701)."]) + [
        P(f"Mise en parallèle : jusqu'à {s['modules_parallel_max']} modules du même modèle. Ne pas mélanger des modèles différents.")]
    f += chapter(7, "Exploitation") + [
        P(f"La batterie se décharge jusqu'à la réserve de {s['soc_reserve_pct']} % ; en dessous, le voyant orange clignote (code B201)."),
        H2("Voyants du panneau"), tbl([["Voyant", "Signification"]] + [[a, b] for a, b in leds], [150, 350]), Spacer(1, 6),
        panel_drawing(m, leds, "Figure 7.1"),
        P("Sur une batterie, le voyant orange fixe signifie une température hors plage de charge. Sur un onduleur de série S, le "
          "même voyant signifie une limitation de puissance : ne pas confondre les deux appareils."),
        P(f"La charge est suspendue sous {s['temp_charge_min_c']} °C (code B101). L'alarme de température haute est à {s['temp_high_c']} °C (code B102).")]
    f += chapter(8, "Association avec un onduleur") + [
        P("La batterie communique avec l'onduleur par le bus HNBus. Une perte de communication provoque le code B401."),
        H2("Matrice de compatibilité"),
        tbl([["Onduleur", "Puissance", "Compatible", "Remarque"]] + [
            [i["model"], f"{i['power_kw']} kW", "Oui" if compat(i, s)[0] else "Non", compat(i, s)[1]] for i in _ALL_INV], [100, 90, 90, 220])]
    f += chapter(9, "Dépannage de premier niveau") + [tbl([["Symptôme", "Vérification", "Code associé"],
        ["La batterie ne charge pas par temps froid", f"Température sous {s['temp_charge_min_c']} °C : attendre le réchauffement", "B101"],
        ["Voyant orange fixe en été", f"Température au-dessus de {s['temp_high_c']} °C : ventiler", "B102"],
        ["Voyant orange clignotant", "Contrôler le câble HNBus, les adresses et l'état de charge", "B201, B401, B403"],
        ["Voyant rouge clignotant", f"Écart entre cellules supérieur à {s['cell_delta_mv']} mV", "B301, B302"],
        ["Batterie éteinte", "Veille profonde : relancer par le bouton de démarrage", "B702"]], [170, 230, 100])]
    f += chapter(10, "Maintenance et stockage") + [
        P(f"Resserrer les bornes à {s['terminal_torque_nm']} N.m une fois par an. Si la batterie reste inutilisée, la recharger au moins tous "
          f"les {s['storage_recharge_months']} mois pour éviter la décharge profonde. La procédure complète figure dans la « Procédure de maintenance {m} »."),
        tbl([["Fréquence", "Action"], ["Mensuelle", "Contrôler les voyants et la température"],
             ["Trimestrielle", "Contrôler l'état de charge et les connexions"], ["Annuelle", "Resserrer les bornes et contrôler la capacité"]], [140, 360])]
    f += chapter(11, "Mise hors service et recyclage") + [
        P("Consigner la batterie, la débrancher et la transporter en emballage homologué pour batteries lithium. La remettre à une filière de recyclage agréée.")]
    f += chapter(12, "Annexes") + [H2("Glossaire"), tbl([["Terme", "Définition"], ["BMS", "Système de gestion de batterie"],
        ["SOC", "État de charge en pourcentage"], ["LFP", "Lithium fer phosphate"], ["HNBus", "Bus de communication onduleur - batterie"]], [120, 380]),
        H2("Historique des révisions"), tbl([["Version", "Modification"], ["1.0", "Première édition."],
        ["2.0", "Alarme de température et matrice de compatibilité mises à jour."]], [80, 420])]
    return f


def manual_flow(s, version="2.0"):
    return inverter_manual(s, version) if s["family"] == "onduleur" else battery_manual(s, version)


# ===================================================================== CODES D'ERREUR
CAT_INV = {
    "1": ("Réseau", ["Mesurer la tension et la fréquence au point de raccordement AC.", "Contrôler le disjoncteur AC et le serrage des bornes AC.",
                     "Si le réseau est conforme et le défaut persiste, relever le code et contacter le gestionnaire de réseau."]),
    "2": ("Entrée DC", ["Mettre hors tension (consignation) puis déconnecter les chaînes une par une.",
                        "Mesurer la tension à vide de chaque chaîne et vérifier la polarité.",
                        "Contrôler le nombre de modules en série par rapport à la tension DC maximale du modèle."]),
    "3": ("Isolement et terre", ["Mettre hors tension (consignation) et déconnecter les chaînes.",
                                 "Mesurer la résistance d'isolement de chaque chaîne par rapport à la terre.",
                                 "Isoler la chaîne défectueuse, rechercher le connecteur ou le câble humide ou endommagé."]),
    "4": ("Thermique", ["Contrôler la propreté des grilles de ventilation et le dégagement autour de l'appareil.",
                        "Vérifier le fonctionnement du ventilateur.", "Contrôler la température ambiante du local."]),
    "5": ("Communication", ["Vérifier le câble de communication (continuité, blindage) et les connecteurs.",
                            "Contrôler que chaque appareil du bus a une adresse unique.", "Redémarrer les appareils dans l'ordre : batterie puis onduleur."]),
    "6": ("Matériel interne", ["Relever le code et l'heure du défaut, redémarrer une seule fois.",
                               "Si le code revient, ne pas poursuivre l'intervention sur site.", "Contacter le SAV avec le numéro de série."]),
    "7": ("Sortie AC", ["Mettre hors tension (consignation).", "Contrôler la charge raccordée et le câblage de sortie.",
                        "Mesurer l'isolement et la continuité des conducteurs AC."]),
    "8": ("Configuration", ["Ouvrir le menu de configuration.", "Régler le paramètre indiqué par le code.", "Valider et vérifier la disparition de l'information."]),
}
CAT_BAT = {
    "1": ("Température", ["Relever la température affichée par la batterie.", "Contrôler la ventilation et l'exposition du local.",
                          "Ne pas forcer la charge ; attendre le retour dans la plage autorisée."]),
    "2": ("Charge et décharge", ["Relever l'état de charge et le courant.", "Contrôler la limite de courant configurée dans l'onduleur.",
                                 "Recharger la batterie selon la procédure du manuel si l'état de charge est bas."]),
    "3": ("Cellules", ["Relever l'écart de tension entre cellules.", "Lancer un cycle d'équilibrage (charge complète).",
                       "Si l'écart reste supérieur au seuil, ne pas poursuivre sur site : contacter le SAV."]),
    "4": ("Communication", ["Vérifier le câble HNBus et les connecteurs.", "Contrôler l'adresse de chaque batterie et de l'onduleur.",
                            "Vérifier la compatibilité du protocole et du firmware."]),
    "5": ("Protections", ["Mettre hors tension (consignation).", "Contrôler le câblage DC et l'absence de court-circuit.",
                          "Ne pas remplacer un fusible interne : contacter le SAV."]),
    "6": ("BMS interne", ["Relever le code et l'heure du défaut, redémarrer une seule fois.", "Si le code revient, arrêter l'intervention.",
                          "Contacter le SAV avec le numéro de série."]),
    "7": ("Configuration", ["Ouvrir le menu de l'onduleur.", "Régler le paramètre indiqué.", "Valider et vérifier la disparition de l'information."]),
}


def codes_flow(s, version="1.0"):
    m, errs = s["model"], errors_for(s)
    rows = [["Code", "Titre", "Gravité", "Voyant", "Cause", "Action"]] + [
        [e["code"], e["title"], e["severity"], e["led"], e["cause"], e["action"]] for e in errs]
    f = chapter(1, "Mode d'emploi du guide", first=True) + [
        P(f"Guide des codes d'erreur du modèle {m}. Les seuils indiqués ne valent que pour ce modèle : relever le modèle sur la plaque "
          "signalétique avant de consulter ce guide."),
        P("<b>AVERTISSEMENT</b> : mettre hors tension avant toute action sur le câblage. Ne pas intervenir sur un code de gravité Critique sans consignation complète."),
        P("Gravités : Information (aucune action urgente), Avertissement (surveiller), Défaut (production limitée ou arrêtée), "
          "Critique (arrêt de sécurité, intervention habilitée).")]
    f += chapter(2, "Tableau des codes") + [P("Tableau 2.1 - Codes d'erreur et actions"), tbl(rows, [32, 80, 52, 62, 120, 120])]
    cat = CAT_INV if s["family"] == "onduleur" else CAT_BAT
    f += chapter(3, "Fiches de diagnostic")
    for e in errs:
        theme, base = cat.get(e["code"][1], cat[sorted(cat)[0]])
        f += [H2(f"Fiche {e['code']} - {e['title']}"),
              P(f"Domaine : {theme}. Gravité : {e['severity']}. Voyant associé : {e['led']}."), P(f"Cause probable : {e['cause']}"),
              P("<b>Diagnostic</b> : " + " ".join(f"({i}) {t}" for i, t in enumerate(base, 1))),
              P(f"<b>Action</b> : {e['action']}")]
        if e["severity"] == "Critique":
            f.append(P("<b>AVERTISSEMENT</b> : code critique. Consigner l'appareil et ne remettre en service qu'après contrôle par une personne habilitée."))
        f.append(P(f"Remise en service : après correction, redémarrer le {m} et vérifier la disparition du code {e['code']} pendant 10 minutes."))
    return f


# ===================================================================== PROCÉDURE DE MAINTENANCE
def procedure_flow(s, version="1.0"):
    m, t = s["model"], s["terminal_torque_nm"]
    inv = s["family"] == "onduleur"
    kind = "onduleur" if inv else "batterie"
    f = chapter(1, "Objet et périmètre", first=True) + [
        P(f"Procédure de maintenance préventive du modèle {m} ({kind}). Document fictif. Elle s'adresse aux techniciens habilités et ne "
          "remplace ni la documentation du constructeur, ni les procédures de sécurité de l'entreprise."),
        P("<b>AVERTISSEMENT</b> : toute intervention commence par la consignation décrite au chapitre 3.")]
    f += chapter(2, "Outillage et consommables") + [tbl([["Élément", "Usage"], ["Clé dynamométrique", f"Serrage des bornes à {t} N.m"],
        ["Multimètre CAT III", "Mesure de tension et de continuité"],
        ["Mégohmmètre" if inv else "Thermomètre infrarouge", "Mesure d'isolement" if inv else "Contrôle de température des modules"],
        ["Pinceau et aspirateur", "Dépoussiérage des grilles"], ["Gants isolants", "Protection individuelle"]], [180, 320])]
    f += chapter(3, "Consignation") + steps(SAFETY_LOCKOUT) + [
        P("<b>AVERTISSEMENT</b> : ne jamais retirer l'étiquette de consignation d'une autre personne.")]
    f += chapter(4, "Périodicité") + [tbl([["Fréquence", "Action"], ["Mensuelle", "Vérifier les voyants et l'absence de code actif"],
        ["Trimestrielle", "Inspection visuelle, dépoussiérage"], ["Annuelle", f"Resserrage des bornes à {t} N.m, contrôle complet"]], [140, 360])]
    spec = (f"Nettoyer les grilles de ventilation ; la limitation de puissance débute à {s['derate_temp_c']} °C." if inv else
            f"Contrôler la température : alarme à {s['temp_high_c']} °C, charge interdite sous {s['temp_charge_min_c']} °C.")
    f += chapter(5, "Étapes de maintenance") + steps([
        "Inspecter le boîtier : fissures, traces de chaleur, humidité, corrosion.", spec,
        f"Resserrer les bornes au couple de {t} N.m, en tirant légèrement sur chaque câble.",
        "Contrôler l'état des câbles et des connecteurs (isolant, traces d'échauffement).",
        "Contrôler les voyants et l'absence de code d'erreur actif.",
        "Relever la version du firmware ; mettre à jour si une version plus récente est publiée.",
        "Contrôler la communication HNBus avec l'équipement associé."]) + [
        P("<b>AVERTISSEMENT</b> : si un connecteur est brûlé ou déformé, ne pas le réutiliser ; le remplacer par une pièce d'origine.")]
    meas = ([["Résistance d'isolement", f"supérieure à {s['iso_kohm']} kΩ", "Mégohmmètre"], ["Tension DC par chaîne", f"inférieure à {s['vdc_max']} V", "Multimètre"]]
            if inv else [["Température des cellules", f"inférieure à {s['temp_high_c']} °C", "Thermomètre"],
                         ["Écart entre cellules", f"inférieur à {s['cell_delta_mv']} mV", "Affichage BMS"]])
    f += chapter(6, "Mesures de contrôle") + [tbl([["Mesure", "Valeur attendue", "Instrument"]] + meas, [160, 200, 140])]
    f += chapter(7, "Remise en service") + steps([
        "Retirer l'étiquette de consignation.", "Fermer le sectionneur DC puis le sectionneur AC.",
        "Attendre le démarrage : voyant vert clignotant puis fixe.", "Vérifier l'absence de code pendant 10 minutes."])
    f += chapter(8, "Fiche d'enregistrement") + [tbl([["Date", "Technicien", "Mesures relevées", "Observations"], ["", "", "", ""], ["", "", "", ""]], [80, 120, 160, 140]),
        P(f"Critère de remplacement : en cas de code Critique répété, de connecteur brûlé ou de capacité inférieure à 80 % de la valeur nominale, "
          f"mettre le {m} hors service et contacter le SAV.")]
    return f


def guide_flow(family):
    lab = "onduleurs solaires" if family == "onduleur" else "batteries de stockage"
    f = chapter(1, "Objet", first=True) + [P(f"Guide général de sécurité et d'exploitation des {lab} {BRAND}. Document fictif.")]
    f += chapter(2, "Sécurité") + ([P("Les chaînes photovoltaïques restent sous tension en plein jour : mettre hors tension AC et DC avant toute intervention.")]
                                   if family == "onduleur" else [P("Ne jamais ouvrir une batterie. Ne pas forcer la charge à basse température.")])
    f += chapter(3, "Identification du modèle") + [P("Toujours identifier le modèle exact sur la plaque signalétique avant de consulter un code d'erreur : "
                                                   "les seuils et la signification des voyants varient d'un modèle à l'autre.")]
    return f
