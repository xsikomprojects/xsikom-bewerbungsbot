"""
Grafische Auswertung mit Matplotlib
"""
import sqlite3
import os
from datetime import datetime
from database import DB_NAME


def charts_erstellen():
    """Erstellt alle Auswertungs-Charts."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
    except ImportError:
        print("  Matplotlib nicht installiert!")
        print("  -> pip install matplotlib")
        return

    conn = sqlite3.connect(DB_NAME)
    c    = conn.cursor()

    # Daten laden
    c.execute("SELECT quelle, COUNT(*) FROM stellen GROUP BY quelle")
    quellen_data = c.fetchall()

    c.execute("SELECT status, COUNT(*) FROM bewerbungen GROUP BY status")
    status_data = c.fetchall()

    c.execute(
        "SELECT standort, COUNT(*) FROM stellen "
        "WHERE standort != '' "
        "GROUP BY standort ORDER BY COUNT(*) DESC LIMIT 8"
    )
    standort_data = c.fetchall()

    c.execute(
        "SELECT datum FROM bewerbungen "
        "WHERE status='gesendet' ORDER BY datum"
    )
    datum_data = c.fetchall()

    conn.close()

    # Ordner erstellen
    charts_pfad = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "charts"
    )
    os.makedirs(charts_pfad, exist_ok=True)

    # FARBEN
    BLAU    = "#00467F"
    GRUEN   = "#2ECC71"
    GELB    = "#F39C12"
    ROT     = "#E74C3C"
    HELL    = "#DCE6F1"
    FARBEN  = [
        "#00467F", "#2ECC71", "#F39C12",
        "#E74C3C", "#9B59B6", "#1ABC9C",
        "#E67E22", "#34495E"
    ]

    # ============================================================
    # CHART 1: STELLEN NACH QUELLE (Kreisdiagramm)
    # ============================================================
    if quellen_data:
        fig, ax = plt.subplots(figsize=(10, 7))
        fig.patch.set_facecolor("#F8F9FA")
        ax.set_facecolor("#F8F9FA")

        labels = [q[0] for q in quellen_data]
        werte  = [q[1] for q in quellen_data]
        farben = FARBEN[:len(labels)]

        wedges, texts, autotexts = ax.pie(
            werte,
            labels=labels,
            colors=farben,
            autopct="%1.1f%%",
            startangle=90,
            pctdistance=0.85,
        )

        for text in texts:
            text.set_fontsize(11)
        for autotext in autotexts:
            autotext.set_fontsize(10)
            autotext.set_color("white")
            autotext.set_fontweight("bold")

        ax.set_title(
            "Stellen nach Jobportal\nKomi Tevi - IT-Praktikum Bot",
            fontsize=14, fontweight="bold",
            color=BLAU, pad=20
        )

        gesamt = sum(werte)
        ax.text(
            0, -1.3,
            f"Gesamt: {gesamt} Stellen gefunden",
            ha="center", fontsize=11,
            color=BLAU, fontweight="bold"
        )

        plt.tight_layout()
        pfad1 = os.path.join(charts_pfad, "stellen_quellen.png")
        plt.savefig(pfad1, dpi=150, bbox_inches="tight")
        plt.close()
        print(f"  Chart 1 erstellt: stellen_quellen.png")

    # ============================================================
    # CHART 2: BEWERBUNGSSTATUS (Balkendiagramm)
    # ============================================================
    if status_data:
        fig, ax = plt.subplots(figsize=(10, 6))
        fig.patch.set_facecolor("#F8F9FA")
        ax.set_facecolor("#F8F9FA")

        labels = [s[0] for s in status_data]
        werte  = [s[1] for s in status_data]

        farben_map = {
            "gesendet":    GRUEN,
            "trockenlauf": GELB,
            "fehler":      ROT,
            "vorbereitet": BLAU,
        }
        barfarben = [
            farben_map.get(l, BLAU) for l in labels
        ]

        balken = ax.bar(
            labels, werte,
            color=barfarben,
            edgecolor="white",
            linewidth=1.5,
            width=0.6
        )

        # Werte auf Balken
        for balken_elem, wert in zip(balken, werte):
            ax.text(
                balken_elem.get_x() + balken_elem.get_width() / 2,
                balken_elem.get_height() + 0.1,
                str(wert),
                ha="center", va="bottom",
                fontsize=12, fontweight="bold",
                color=BLAU
            )

        ax.set_title(
            "Bewerbungen nach Status\nKomi Tevi - IT-Praktikum Bot",
            fontsize=14, fontweight="bold",
            color=BLAU, pad=15
        )
        ax.set_xlabel("Status", fontsize=11, color=BLAU)
        ax.set_ylabel("Anzahl", fontsize=11, color=BLAU)
        ax.set_facecolor("#F8F9FA")
        ax.grid(axis="y", alpha=0.3)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        plt.tight_layout()
        pfad2 = os.path.join(charts_pfad, "bewerbungen_status.png")
        plt.savefig(pfad2, dpi=150, bbox_inches="tight")
        plt.close()
        print(f"  Chart 2 erstellt: bewerbungen_status.png")

    # ============================================================
    # CHART 3: TOP STANDORTE (Horizontales Balkendiagramm)
    # ============================================================
    if standort_data:
        fig, ax = plt.subplots(figsize=(10, 7))
        fig.patch.set_facecolor("#F8F9FA")
        ax.set_facecolor("#F8F9FA")

        staedte = [s[0] for s in standort_data]
        werte   = [s[1] for s in standort_data]

        farben = [
            BLAU if i == 0 else
            "#1A5D9E" if i == 1 else
            "#2E7BC4"
            for i in range(len(staedte))
        ]

        balken = ax.barh(
            staedte, werte,
            color=farben,
            edgecolor="white",
            linewidth=1.5,
            height=0.6
        )

        for balken_elem, wert in zip(balken, werte):
            ax.text(
                balken_elem.get_width() + 0.1,
                balken_elem.get_y() + balken_elem.get_height() / 2,
                str(wert),
                ha="left", va="center",
                fontsize=11, fontweight="bold",
                color=BLAU
            )

        ax.set_title(
            "Top Standorte\nKomi Tevi - IT-Praktikum Bot",
            fontsize=14, fontweight="bold",
            color=BLAU, pad=15
        )
        ax.set_xlabel("Anzahl Stellen", fontsize=11, color=BLAU)
        ax.grid(axis="x", alpha=0.3)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.invert_yaxis()

        plt.tight_layout()
        pfad3 = os.path.join(charts_pfad, "top_standorte.png")
        plt.savefig(pfad3, dpi=150, bbox_inches="tight")
        plt.close()
        print(f"  Chart 3 erstellt: top_standorte.png")

    # ============================================================
    # CHART 4: ZUSAMMENFASSUNG (Dashboard)
    # ============================================================
    fig = plt.figure(figsize=(14, 9))
    fig.patch.set_facecolor("#F8F9FA")

    fig.suptitle(
        "IT-Praktikum Bewerbungsbot - Dashboard\nKomi Tevi",
        fontsize=16, fontweight="bold",
        color=BLAU, y=0.98
    )

    # Statistik Boxen
    conn   = sqlite3.connect(DB_NAME)
    c      = conn.cursor()

    c.execute("SELECT COUNT(*) FROM stellen")
    stellen_ges = c.fetchone()[0]

    c.execute(
        "SELECT COUNT(*) FROM bewerbungen WHERE status='gesendet'"
    )
    bew_gesendet = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM bewerbungen")
    bew_ges = c.fetchone()[0]

    try:
        c.execute(
            "SELECT COUNT(*) FROM tracker WHERE einladung=1"
        )
        einladungen = c.fetchone()[0]
    except Exception:
        einladungen = 0

    conn.close()

    stats = [
        ("Stellen\ngefunden",  stellen_ges,  BLAU,  "📋"),
        ("Bewerbungen\ngesamt", bew_ges,     GRUEN, "📬"),
        ("Gesendet",           bew_gesendet, GELB,  "📧"),
        ("Einladungen",        einladungen,  ROT,   "🎉"),
    ]

    for i, (label, wert, farbe, emoji) in enumerate(stats):
        ax = fig.add_subplot(2, 4, i + 1)
        ax.set_facecolor(farbe)

        ax.text(
            0.5, 0.65, str(wert),
            ha="center", va="center",
            fontsize=32, fontweight="bold",
            color="white",
            transform=ax.transAxes
        )
        ax.text(
            0.5, 0.25, label,
            ha="center", va="center",
            fontsize=11, color="white",
            fontweight="bold",
            transform=ax.transAxes
        )

        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)

    # Kreisdiagramm unten links
    if quellen_data:
        ax2 = fig.add_subplot(2, 2, 3)
        ax2.set_facecolor("#F8F9FA")
        labels = [q[0] for q in quellen_data[:5]]
        werte  = [q[1] for q in quellen_data[:5]]
        ax2.pie(
            werte, labels=labels,
            colors=FARBEN[:len(labels)],
            autopct="%1.0f%%",
            textprops={"fontsize": 9}
        )
        ax2.set_title(
            "Quellen", fontsize=12,
            fontweight="bold", color=BLAU
        )

    # Balkendiagramm unten rechts
    if standort_data:
        ax3 = fig.add_subplot(2, 2, 4)
        ax3.set_facecolor("#F8F9FA")
        staedte = [s[0][:10] for s in standort_data[:5]]
        werte   = [s[1] for s in standort_data[:5]]
        ax3.bar(
            staedte, werte,
            color=BLAU,
            edgecolor="white"
        )
        ax3.set_title(
            "Top Staedte", fontsize=12,
            fontweight="bold", color=BLAU
        )
        ax3.tick_params(axis="x", rotation=30)
        ax3.spines["top"].set_visible(False)
        ax3.spines["right"].set_visible(False)
        ax3.grid(axis="y", alpha=0.3)

    # Datum
    fig.text(
        0.5, 0.01,
        f"Stand: {datetime.now().strftime('%d.%m.%Y %H:%M')} | "
        f"xsikom.projects@gmail.com",
        ha="center", fontsize=9,
        color="gray"
    )

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    pfad4 = os.path.join(charts_pfad, "dashboard.png")
    plt.savefig(pfad4, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Chart 4 erstellt: dashboard.png")

    print(f"\n  {'='*50}")
    print(f"  ALLE CHARTS ERSTELLT!")
    print(f"  {'='*50}")
    print(f"  Ordner: {charts_pfad}")
    print(f"\n  Dateien:")
    print(f"  - stellen_quellen.png")
    print(f"  - bewerbungen_status.png")
    print(f"  - top_standorte.png")
    print(f"  - dashboard.png")

    # Ordner öffnen
    try:
        os.startfile(charts_pfad)
    except Exception:
        pass

    return charts_pfad


if __name__ == "__main__":
    print("\n  Erstelle Charts...")
    charts_erstellen()