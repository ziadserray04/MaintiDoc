"""Données du corpus solaire fictif : modèles, faits, catalogues d'erreurs, voyants, compatibilité.
Tout est inventé (marque « HelioNova »). Aucune valeur n'est réelle."""
BRAND = "HelioNova"
GROUPS_STD = ["grp_installateurs", "grp_sav"]
GROUP_CONF = ["grp_engineering"]

# ---------- Modèles fictifs ----------
INVERTERS = [  # nom, kW, phases, nb MPPT, Vdc max
    ("HN-S3", 3, 1, 1, 550), ("HN-S5", 5, 1, 2, 600), ("HN-S6", 6, 1, 2, 600),
    ("HN-S8", 8, 1, 2, 650), ("HN-S10", 10, 1, 3, 800), ("HN-T15", 15, 3, 2, 1000),
    ("HN-T20", 20, 3, 3, 1000),
]
BATTERIES = [("HN-B5", 5.0), ("HN-B7", 7.5), ("HN-B10", 10.0), ("HN-B13", 13.0),
             ("HN-B15", 15.0), ("HN-B20", 20.0), ("HN-B30", 30.0)]


def inverter_facts(i, spec):
    name, kw, ph, mppt, vdc = spec
    return dict(
        model=name, family="onduleur", power_kw=kw, phases=ph, mppt=mppt, vdc_max=vdc,
        derate_temp_c=60 + i, iso_kohm=500 - 20 * i, terminal_torque_nm=round(2.0 + 0.2 * i, 1),
        ip=65, series="T" if ph == 3 else "S", fuse_a=16 + 4 * i,
        orange_fixed="défaut réseau temporaire" if ph == 3 else "limitation de puissance (derating)",
        efficiency_pct=round(97.0 + 0.1 * i, 1), weight_kg=14 + 2 * i,
        ac_cable_mm2={3: 2.5, 5: 4, 6: 4, 8: 6, 10: 6, 15: 10, 20: 16}[kw],
        ac_current_a=round(kw * 1000 / (230 if ph == 1 else 400 * 1.732), 1),
        dc_string_a_max=12 + 2 * (i % 3), ambient_min_c=-25, ambient_max_c=60,
    )


def battery_facts(i, spec):
    name, kwh = spec
    return dict(
        model=name, family="batterie", capacity_kwh=kwh, voltage_v=51.2, chemistry="LFP",
        max_charge_a=round(kwh * 1000 / 51.2 * 0.5), temp_high_c=50 + (i % 4),
        temp_charge_min_c=0 if i % 2 == 0 else 5, cycles=6000, terminal_torque_nm=round(6.0 + 0.5 * i, 1),
        ip=55, cell_delta_mv=80 + 5 * i,
        weight_kg=round(kwh * 9.5 + 8), dc_cable_mm2=16 if kwh <= 10 else (25 if kwh <= 15 else 35),
        modules_parallel_max=4 if kwh <= 13 else 6, storage_recharge_months=6, standby_w=12 + i,
        soc_reserve_pct=10,
    )


# ---------- Catalogues d'erreurs (gabarits avec seuils par modèle) ----------
# (code, titre, gravité, voyant, cause, action)
INV_ERRORS = [
    ("E101", "Surtension réseau", "Défaut", "Orange fixe", "La tension du réseau dépasse la limite autorisée.", "Vérifier la tension au point de raccordement ; contacter le gestionnaire de réseau si elle reste élevée."),
    ("E102", "Sous-tension réseau", "Défaut", "Orange fixe", "La tension du réseau est inférieure à la limite autorisée.", "Contrôler le disjoncteur AC et la section des câbles."),
    ("E103", "Fréquence réseau hors plage", "Défaut", "Orange fixe", "La fréquence mesurée sort de la plage de fonctionnement.", "Attendre le retour à la normale ; si le défaut persiste, vérifier le réseau."),
    ("E104", "Perte du réseau (îlotage)", "Défaut", "Orange fixe", "Le réseau n'est plus détecté.", "Vérifier le disjoncteur AC et la présence du réseau."),
    ("E105", "Déséquilibre de phases", "Défaut", "Orange fixe", "L'écart de tension entre phases est trop important.", "Contrôler les phases et le serrage des bornes AC."),
    ("E201", "Surtension DC", "Défaut", "Rouge fixe", "La tension DC des panneaux dépasse {vdc} V.", "Mettre hors tension ; vérifier le nombre de modules en série."),
    ("E202", "Sous-tension DC", "Avertissement", "Vert clignotant", "La tension DC est insuffisante pour démarrer.", "Attendre un meilleur ensoleillement ; contrôler les connecteurs."),
    ("E203", "Inversion de polarité DC", "Critique", "Rouge fixe", "La polarité d'une chaîne PV est inversée.", "Mettre hors tension ; corriger le câblage par une personne habilitée."),
    ("E204", "Courant DC excessif", "Défaut", "Rouge fixe", "Le courant d'une entrée dépasse la limite admissible.", "Vérifier le dimensionnement des chaînes PV."),
    ("E205", "Défaut d'arc DC", "Critique", "Rouge fixe", "Un arc électrique est détecté sur les câbles DC.", "Mettre hors tension ; inspecter connecteurs et câbles avant tout redémarrage."),
    ("E301", "Défaut d'isolement", "Critique", "Rouge clignotant", "La résistance d'isolement est inférieure à {iso} kΩ.", "Mettre hors tension ; rechercher le défaut à la terre sur les chaînes PV."),
    ("E302", "Courant de fuite excessif", "Défaut", "Rouge clignotant", "Le courant de fuite dépasse le seuil de protection.", "Contrôler l'humidité des connecteurs et la mise à la terre."),
    ("E303", "Défaut de mise à la terre", "Critique", "Rouge clignotant", "La liaison à la terre est absente ou défectueuse.", "Vérifier la continuité de la terre par une personne habilitée."),
    ("E401", "Surchauffe interne", "Défaut", "Orange fixe", "La température interne dépasse {derate} °C et la puissance est limitée.", "Dégager les grilles de ventilation ; vérifier le ventilateur."),
    ("E402", "Défaut du ventilateur", "Avertissement", "Orange fixe", "Le ventilateur ne tourne pas à la vitesse attendue.", "Nettoyer ou remplacer le ventilateur après mise hors tension."),
    ("E403", "Capteur de température défectueux", "Défaut", "Orange fixe", "La lecture d'un capteur de température est incohérente.", "Redémarrer l'appareil ; contacter le SAV si le défaut persiste."),
    ("E404", "Température ambiante trop basse", "Avertissement", "Vert clignotant", "L'appareil attend une température de fonctionnement minimale.", "Aucune action ; le démarrage reprendra automatiquement."),
    ("E501", "Perte de communication avec la batterie", "Avertissement", "Orange clignotant", "Le bus de communication avec la batterie ne répond pas.", "Vérifier le câble de communication et l'adresse de la batterie."),
    ("E502", "Perte de communication compteur", "Avertissement", "Orange clignotant", "Le compteur d'énergie ne répond pas.", "Contrôler le câble RS485 et la configuration."),
    ("E503", "Conflit d'adresse de communication", "Avertissement", "Orange clignotant", "Deux appareils utilisent la même adresse.", "Modifier l'adresse d'un des appareils."),
    ("E504", "Échec de mise à jour du firmware", "Avertissement", "Orange clignotant", "La dernière mise à jour s'est interrompue.", "Relancer la mise à jour avec une alimentation stable."),
    ("E601", "Défaut du relais de couplage", "Critique", "Rouge fixe", "Le relais de couplage ne se ferme pas ou reste collé.", "Mettre hors tension ; contacter le SAV, ne pas réparer sur site."),
    ("E602", "Défaut de mesure de courant AC", "Défaut", "Rouge fixe", "Le capteur de courant AC donne une valeur incohérente.", "Redémarrer ; contacter le SAV si le défaut persiste."),
    ("E603", "Défaut du processeur de contrôle", "Critique", "Rouge fixe", "Un test interne du processeur a échoué.", "Contacter le SAV."),
    ("E604", "Défaut de la carte d'alimentation", "Critique", "Rouge fixe", "La tension de l'alimentation interne est hors plage.", "Contacter le SAV."),
    ("E701", "Surcharge de sortie", "Défaut", "Orange fixe", "La charge dépasse la puissance nominale.", "Réduire la charge raccordée."),
    ("E702", "Court-circuit de sortie", "Critique", "Rouge fixe", "Un court-circuit est détecté côté AC.", "Mettre hors tension ; localiser le court-circuit."),
    ("E703", "Surtension sur le bus interne", "Défaut", "Rouge fixe", "La tension du bus interne dépasse la limite.", "Redémarrer ; contacter le SAV si le défaut persiste."),
    ("E801", "Horloge non configurée", "Information", "Vert clignotant", "La date et l'heure n'ont pas été réglées.", "Régler l'horloge dans le menu de configuration."),
    ("E802", "Paramètres de pays non définis", "Information", "Vert clignotant", "Le profil réseau du pays n'est pas sélectionné.", "Sélectionner le profil de pays à la mise en service."),
]
BAT_ERRORS = [
    ("B101", "Température de charge trop basse", "Avertissement", "Orange fixe", "La température des cellules est inférieure à {tmin} °C : la charge est suspendue.", "Attendre le réchauffement ; ne pas forcer la charge."),
    ("B102", "Température élevée", "Défaut", "Orange fixe", "La température des cellules dépasse {thigh} °C.", "Améliorer la ventilation et réduire la puissance de charge."),
    ("B103", "Température critique", "Critique", "Rouge fixe", "La température dépasse la limite de sécurité.", "Mettre hors tension ; ne pas ouvrir la batterie ; contacter le SAV."),
    ("B104", "Capteur de température défectueux", "Défaut", "Orange fixe", "Un capteur de cellule renvoie une valeur aberrante.", "Redémarrer ; contacter le SAV si le défaut persiste."),
    ("B105", "Écart de température entre modules", "Avertissement", "Orange fixe", "L'écart de température entre modules est trop élevé.", "Vérifier le flux d'air autour de la batterie."),
    ("B201", "État de charge faible", "Avertissement", "Orange clignotant", "L'état de charge est inférieur à 10 %.", "Recharger la batterie ; limiter la décharge."),
    ("B202", "Décharge profonde", "Défaut", "Rouge fixe", "La tension des cellules est trop basse.", "Recharger lentement selon la procédure du manuel."),
    ("B203", "Surcharge", "Critique", "Rouge fixe", "La tension d'une cellule dépasse la limite haute.", "Mettre hors tension ; vérifier le réglage de charge de l'onduleur."),
    ("B204", "Courant de charge trop élevé", "Défaut", "Orange fixe", "Le courant de charge dépasse {imax} A.", "Vérifier la limite de courant configurée dans l'onduleur."),
    ("B205", "Courant de décharge trop élevé", "Défaut", "Orange fixe", "Le courant de décharge dépasse la limite.", "Réduire la charge raccordée."),
    ("B206", "Capacité résiduelle en baisse", "Information", "Vert fixe", "La capacité mesurée est sous 80 % de la capacité nominale.", "Planifier un contrôle de santé de la batterie."),
    ("B301", "Déséquilibre des cellules", "Défaut", "Rouge clignotant", "L'écart de tension entre cellules dépasse {delta} mV.", "Lancer un cycle d'équilibrage ; contacter le SAV s'il persiste."),
    ("B302", "Cellule défectueuse", "Critique", "Rouge clignotant", "Une cellule présente une tension anormale.", "Mettre hors tension ; remplacement du module par le SAV."),
    ("B303", "Défaut d'équilibrage", "Avertissement", "Orange clignotant", "L'équilibrage ne s'achève pas.", "Laisser la batterie se charger complètement."),
    ("B401", "Perte de communication avec l'onduleur", "Avertissement", "Orange clignotant", "Le bus de communication ne répond pas.", "Vérifier le câble et l'adresse de la batterie."),
    ("B402", "Protocole de communication incompatible", "Avertissement", "Orange clignotant", "La version du protocole de l'onduleur n'est pas prise en charge.", "Mettre à jour le firmware de l'onduleur."),
    ("B403", "Conflit d'adresse", "Avertissement", "Orange clignotant", "Deux batteries ont la même adresse.", "Modifier l'adresse d'une batterie."),
    ("B404", "Échec de mise à jour du firmware", "Avertissement", "Orange clignotant", "La mise à jour s'est interrompue.", "Relancer la mise à jour avec une alimentation stable."),
    ("B501", "Défaut du contacteur principal", "Critique", "Rouge fixe", "Le contacteur ne se ferme pas ou reste collé.", "Mettre hors tension ; contacter le SAV."),
    ("B502", "Fusible interne ouvert", "Critique", "Rouge fixe", "Le fusible de protection interne est ouvert.", "Ne pas remplacer sur site ; contacter le SAV."),
    ("B503", "Court-circuit DC", "Critique", "Rouge fixe", "Un court-circuit est détecté sur la sortie DC.", "Mettre hors tension ; contrôler le câblage."),
    ("B504", "Défaut de pré-charge", "Défaut", "Rouge fixe", "La pré-charge du bus n'aboutit pas.", "Vérifier le câblage et l'état de l'onduleur."),
    ("B601", "Défaut du système de gestion (BMS)", "Critique", "Rouge fixe", "Un test interne du BMS a échoué.", "Contacter le SAV."),
    ("B602", "Mesure de tension défectueuse", "Défaut", "Rouge fixe", "Une mesure de tension est incohérente.", "Redémarrer ; contacter le SAV si le défaut persiste."),
    ("B603", "Mémoire de données corrompue", "Défaut", "Orange clignotant", "L'historique interne est illisible.", "Contacter le SAV."),
    ("B701", "Horloge non configurée", "Information", "Vert clignotant", "La date et l'heure sont absentes.", "Régler l'horloge via l'onduleur."),
    ("B702", "Mode veille profonde", "Information", "Vert clignotant", "La batterie s'est mise en veille pour préserver la charge.", "Relancer par le bouton de démarrage."),
]

LEDS_INV = [("Vert fixe", "Production normale"), ("Vert clignotant", "Démarrage ou attente d'ensoleillement"),
            ("Orange fixe", None), ("Orange clignotant", "Perte de communication (batterie ou compteur)"),
            ("Rouge fixe", "Arrêt sur défaut"), ("Rouge clignotant", "Défaut d'isolement ou de fuite à la terre")]
LEDS_BAT = [("Vert fixe", "Batterie prête"), ("Vert clignotant", "Charge ou décharge en cours"),
            ("Orange fixe", "Température hors plage de charge"), ("Orange clignotant", "État de charge faible ou communication perdue"),
            ("Rouge fixe", "Arrêt de protection"), ("Rouge clignotant", "Déséquilibre ou défaut de cellule")]


def errors_for(f):
    cat = INV_ERRORS if f["family"] == "onduleur" else BAT_ERRORS
    ctx = dict(vdc=f.get("vdc_max"), iso=f.get("iso_kohm"), derate=f.get("derate_temp_c"),
               tmin=f.get("temp_charge_min_c"), thigh=f.get("temp_high_c"), imax=f.get("max_charge_a"),
               delta=f.get("cell_delta_mv"))
    out = []
    for c, t, g, led, cause, act in cat:
        out.append(dict(code=c, title=t, severity=g, led=led, cause=cause.format(**ctx), action=act.format(**ctx)))
    return out


def leds_for(f):
    if f["family"] == "batterie":
        return LEDS_BAT
    return [(a, b if b else f"{f['orange_fixed'][0].upper()}{f['orange_fixed'][1:]}") for a, b in LEDS_INV]


def specs_rows(f):
    if f["family"] == "onduleur":
        return [["Caractéristique", "Valeur"], ["Puissance nominale", f"{f['power_kw']} kW"],
                ["Phases", str(f["phases"])], ["Entrées MPPT", str(f["mppt"])],
                ["Tension DC maximale", f"{f['vdc_max']} V"], ["Indice de protection", f"IP{f['ip']}"],
                ["Limitation de puissance à partir de", f"{f['derate_temp_c']} °C"],
                ["Seuil de défaut d'isolement", f"{f['iso_kohm']} kΩ"],
                ["Couple de serrage des bornes", f"{f['terminal_torque_nm']} N.m"], ["Calibre du fusible AC", f"{f['fuse_a']} A"]]
    return [["Caractéristique", "Valeur"], ["Capacité utile", f"{f['capacity_kwh']} kWh"],
            ["Tension nominale", f"{f['voltage_v']} V"], ["Technologie", "LFP (lithium fer phosphate)"],
            ["Courant de charge maximal", f"{f['max_charge_a']} A"], ["Alarme de température haute", f"{f['temp_high_c']} °C"],
            ["Charge interdite sous", f"{f['temp_charge_min_c']} °C"], ["Cycles garantis", str(f["cycles"])],
            ["Couple de serrage des bornes", f"{f['terminal_torque_nm']} N.m"], ["Indice de protection", f"IP{f['ip']}"]]




def compat(inv: dict, bat: dict) -> tuple[bool, str]:
    """Règle de compatibilité fictive onduleur/batterie (même règle dans tous les documents)."""
    cap_max = inv["power_kw"] * 2.0
    if bat["capacity_kwh"] > cap_max:
        return False, f"capacité supérieure à {cap_max:g} kWh (limite de {inv['model']})"
    if bat["capacity_kwh"] > 15 and inv["phases"] != 3:
        return False, "batteries de plus de 15 kWh réservées aux onduleurs triphasés"
    return True, "compatible"
