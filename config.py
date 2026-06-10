import os

# ============================================================
# PERSÖNLICHE DATEN - Komi Tevi
# ============================================================
PERSOENLICHE_DATEN = {
    "vorname":              "Komi",
    "nachname":             "Tevi",
    "strasse":              "Am Koenigsfloss 12",
    "plz":                  "55252",
    "stadt":                "Mainz-Kastel",
    "telefon":              "+49 178 8977320",
    "email":                "xsikom.projects@gmail.com",
    "geburtsdatum":         "29.11.1980",
    "geburtsort":           "Sika-Kondji, Togo",
    "familienstand":        "verheiratet",
    "staatsangehoerigkeit": "deutsch",
}

# ============================================================
# QUALIFIKATIONEN
# ============================================================
QUALIFIKATIONEN = {
    "ausbildung": "IT-Fachtechniker (Ausbildung seit 01.2026, BFW)",
    "schwerpunkt": "Netzwerktechnik & Systemadministration",
    "kenntnisse": [
        "Netzwerktechnologie (TCP/IP, VLAN, Routing, Switching)",
        "Hardware-Wartung & Computer-Technik (seit 1999)",
        "Betriebssysteme Windows & Linux",
        "MS-Office 365, SAP & RTCIS",
        "IT-Support & Troubleshooting",
        "Softwareinstallation & Systembetreuung",
    ],
    "sprachen": [
        "Deutsch (B2)",
        "Franzoesisch (Muttersprache)",
        "Englisch (A1)",
    ],
}

# ============================================================
# E-MAIL EINSTELLUNGEN - GMAIL
# ============================================================
EMAIL_CONFIG = {
    "smtp_server":   "smtp.gmail.com",
    "smtp_port":     587,
    "email":         "xsikom.projects@gmail.com",
    "passwort":      "cpvsdikipzuygdpf",
    "absender_name": "Komi Tevi",
}

# ============================================================
# TELEGRAM EINSTELLUNGEN
# ============================================================
TELEGRAM_CONFIG = {
    "token":   "8854942475:AAHPKQ2uA-sv2V7vEvbOegJfohhtwCTmXDc",
    "chat_id": "7702819219",
    "aktiv":   True,
}

# ============================================================
# SUCHEINSTELLUNGEN - 30 STÄDTE
# ============================================================
SUCH_CONFIG = {
    "suchbegriffe": [
        "IT Praktikum",
        "Praktikum Netzwerktechnik",
        "Praktikum IT Support",
        "Praktikum Fachinformatiker",
        "Praktikum Systemintegration",
        "Praktikum Netzwerkadministrator",
        "Praktikum IT Helpdesk",
        "Praktikum Systemadministration",
        "IT Praktikant",
        "Praktikum Computer Techniker",
    ],
    "standorte": [
        "Mainz",
        "Wiesbaden",
        "Mainz-Kastel",
        "Ingelheim am Rhein",
        "Frankfurt am Main",
        "Darmstadt",
        "Offenbach am Main",
        "Hanau",
        "Ruesselsheim",
        "Mannheim",
        "Heidelberg",
        "Weinheim",
        "Ludwigshafen",
        "Kaiserslautern",
        "Koeln",
        "Bonn",
        "Koblenz",
        "Duesseldorf",
        "Leverkusen",
        "Stuttgart",
        "Karlsruhe",
        "Freiburg im Breisgau",
        "Saarbruecken",
        "Trier",
        "Kassel",
        "Giessen",
        "Fulda",
        "Marburg",
        "Remote",
        "Homeoffice",
    ],
}

# ============================================================
# BEKANNTE IT-FIRMEN - 20 FIRMEN MIT E-MAIL
# ============================================================
IT_FIRMEN = [
    {
        "firma":    "Vodafone GmbH",
        "email":    "bewerbung@vodafone.com",
        "standort": "Frankfurt am Main",
        "bereich":  "netzwerk",
    },
    {
        "firma":    "T-Systems International GmbH",
        "email":    "praktikum@t-systems.com",
        "standort": "Frankfurt am Main",
        "bereich":  "systemadmin",
    },
    {
        "firma":    "SAP SE",
        "email":    "jobs@sap.com",
        "standort": "Heidelberg",
        "bereich":  "systemadmin",
    },
    {
        "firma":    "Cisco Systems GmbH",
        "email":    "bewerbung@cisco.com",
        "standort": "Frankfurt am Main",
        "bereich":  "netzwerk",
    },
    {
        "firma":    "IBM Deutschland GmbH",
        "email":    "praktikum@de.ibm.com",
        "standort": "Frankfurt am Main",
        "bereich":  "systemadmin",
    },
    {
        "firma":    "Telekom Deutschland GmbH",
        "email":    "praktikum@telekom.de",
        "standort": "Bonn",
        "bereich":  "netzwerk",
    },
    {
        "firma":    "Bechtle AG",
        "email":    "ausbildung@bechtle.com",
        "standort": "Weinheim",
        "bereich":  "support",
    },
    {
        "firma":    "Freudenberg IT",
        "email":    "bewerbung@freudenberg-it.de",
        "standort": "Weinheim",
        "bereich":  "systemadmin",
    },
    {
        "firma":    "Computacenter AG",
        "email":    "praktikum@computacenter.com",
        "standort": "Duesseldorf",
        "bereich":  "support",
    },
    {
        "firma":    "Dimension Data Germany",
        "email":    "bewerbung@dimensiondata.com",
        "standort": "Frankfurt am Main",
        "bereich":  "netzwerk",
    },
    {
        "firma":    "Datagroup SE",
        "email":    "karriere@datagroup.de",
        "standort": "Koeln",
        "bereich":  "support",
    },
    {
        "firma":    "Cancom SE",
        "email":    "jobs@cancom.de",
        "standort": "Frankfurt am Main",
        "bereich":  "systemadmin",
    },
    {
        "firma":    "SoftwareONE Deutschland",
        "email":    "hr@softwareone.com",
        "standort": "Frankfurt am Main",
        "bereich":  "support",
    },
    {
        "firma":    "Logicalis GmbH",
        "email":    "bewerbung@de.logicalis.com",
        "standort": "Frankfurt am Main",
        "bereich":  "netzwerk",
    },
    {
        "firma":    "NTT Germany AG",
        "email":    "hr.de@ntt.com",
        "standort": "Frankfurt am Main",
        "bereich":  "netzwerk",
    },
    {
        "firma":    "NetCologne GmbH",
        "email":    "personal@netcologne.de",
        "standort": "Koeln",
        "bereich":  "netzwerk",
    },
    {
        "firma":    "Bearing Point GmbH",
        "email":    "careers@bearingpoint.com",
        "standort": "Frankfurt am Main",
        "bereich":  "systemadmin",
    },
    {
        "firma":    "Atos SE",
        "email":    "praktikum@atos.net",
        "standort": "Frankfurt am Main",
        "bereich":  "systemadmin",
    },
    {
        "firma":    "Axians IT Solutions",
        "email":    "karriere@axians.de",
        "standort": "Frankfurt am Main",
        "bereich":  "netzwerk",
    },
    {
        "firma":    "Bechtle Logistik & Service GmbH",
        "email":    "bewerbung@bechtle.com",
        "standort": "Mannheim",
        "bereich":  "support",
    },
]

# ============================================================
# PRAKTIKUM DETAILS
# ============================================================
PRAKTIKUM_CONFIG = {
    "art":              "Pflichtpraktikum (BFW)",
    "dauer":            "3 Monate",
    "fruehester_start": "01.03.2026",
}

# ============================================================
# UNTERLAGEN PFADE
# ============================================================
UNTERLAGEN_PFAD = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "unterlagen"
)
ANSCHREIBEN_PFAD = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "anschreiben"
)
UNTERLAGEN = {
    "lebenslauf":  os.path.join(UNTERLAGEN_PFAD, "lebenslauf.pdf"),
    "zeugnisse":   os.path.join(UNTERLAGEN_PFAD, "zeugnisse.pdf"),
    "zertifikate": os.path.join(UNTERLAGEN_PFAD, "zertifikate.pdf"),
}


# ============================================================
# KONFIGURATIONS PRÜFUNG
# ============================================================
def config_pruefen():
    fehler    = []
    warnungen = []
    for pfad in [UNTERLAGEN_PFAD, ANSCHREIBEN_PFAD]:
        if not os.path.exists(pfad):
            os.makedirs(pfad)
    for name, pfad in UNTERLAGEN.items():
        if not os.path.exists(pfad):
            warnungen.append(f"Datei fehlt: {name}")
    return fehler, warnungen


# ============================================================
# KONFIGURATION ANZEIGEN
# ============================================================
def config_anzeigen():
    print("\n" + "="*55)
    print("  KONFIGURATION - Komi Tevi")
    print("="*55)
    print(
        f"  Name      : "
        f"{PERSOENLICHE_DATEN['vorname']} "
        f"{PERSOENLICHE_DATEN['nachname']}"
    )
    print(
        f"  Adresse   : "
        f"{PERSOENLICHE_DATEN['strasse']}, "
        f"{PERSOENLICHE_DATEN['plz']} "
        f"{PERSOENLICHE_DATEN['stadt']}"
    )
    print(f"  Telefon   : {PERSOENLICHE_DATEN['telefon']}")
    print(f"  E-Mail    : {PERSOENLICHE_DATEN['email']}")
    print(
        f"  Telegram  : "
        f"{'Aktiv' if TELEGRAM_CONFIG['aktiv'] else 'Nicht aktiv'}"
    )
    print(f"  Start     : {PRAKTIKUM_CONFIG['fruehester_start']}")
    print(f"  Staedte   : {len(SUCH_CONFIG['standorte'])} Staedte")
    print(f"  IT-Firmen : {len(IT_FIRMEN)} Firmen")
    print("="*55)


# ============================================================
# TEST
# ============================================================
if __name__ == "__main__":
    fehler, warnungen = config_pruefen()
    config_anzeigen()
    if warnungen:
        print("\n  Warnungen:")
        for w in warnungen:
            print(f"  {w}")
    print("\n  Konfiguration erfolgreich!")