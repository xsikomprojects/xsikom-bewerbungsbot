"""
XsiKOM-BewerbungsBOT - Tkinter Version
Kompatibel mit Python 3.14
"""
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import os
import sqlite3
from datetime import datetime

from user_manager import (
    user_db_erstellen, admin_erstellen,
    benutzer_pruefen, benutzer_anlegen,
    alle_benutzer_laden, benutzer_loeschen
)
from aaliyah_ki import Aaliyah

DB_NAME = "bewerbungen.db"

# ============================================================
# FARBEN
# ============================================================
BG         = "#0F1923"
SIDEBAR    = "#162635"
KARTE      = "#1A2F42"
DUNKEL     = "#0A1520"
HELL_RAND  = "#2A4A65"

BLAU       = "#00B4D8"
GRUEN      = "#2DD4A8"
ORANGE     = "#FF8C42"
PINK       = "#FF69B4"
GELB       = "#FFD93D"
ROT        = "#FF5252"

TEXT_H     = "#E8EDF2"
TEXT_M     = "#8899AA"
TEXT_D     = "#5C6B7A"

BTN_B      = "#0077B6"
BTN_G      = "#00B894"
BTN_O      = "#E17055"
BTN_L      = "#6C5CE7"


def style_setup():
    """Setzt ttk Styles."""
    style = ttk.Style()
    style.theme_use("clam")

    style.configure(
        "Dark.TFrame",
        background=BG
    )
    style.configure(
        "Sidebar.TFrame",
        background=SIDEBAR
    )
    style.configure(
        "Karte.TFrame",
        background=KARTE,
        relief="flat"
    )
    style.configure(
        "Dark.TLabel",
        background=BG,
        foreground=TEXT_H,
        font=("Helvetica", 11)
    )
    style.configure(
        "Titel.TLabel",
        background=BG,
        foreground=BLAU,
        font=("Helvetica", 18, "bold")
    )
    style.configure(
        "Sub.TLabel",
        background=BG,
        foreground=TEXT_M,
        font=("Helvetica", 10)
    )
    style.configure(
        "Sidebar.TLabel",
        background=SIDEBAR,
        foreground=TEXT_H,
        font=("Helvetica", 11)
    )
    style.configure(
        "Karte.TLabel",
        background=KARTE,
        foreground=TEXT_H,
        font=("Helvetica", 11)
    )


# ============================================================
# LOGIN SCREEN
# ============================================================
class LoginScreen(tk.Tk):

    def __init__(self, callback):
        tk.Tk.__init__(self)
        self.callback = callback
        self.title("XsiKOM-BewerbungsBOT - Login")
        self.geometry("460x560")
        self.configure(bg=BG)
        self.resizable(False, False)
        self._erstellen()

    def _erstellen(self):
        # Logo
        tk.Label(
            self, text="XsiKOM",
            font=("Helvetica", 40, "bold"),
            fg=BLAU, bg=BG
        ).pack(pady=(45, 0))

        tk.Label(
            self, text="BewerbungsBOT",
            font=("Helvetica", 18, "bold"),
            fg=GRUEN, bg=BG
        ).pack()

        tk.Label(
            self, text="Version 7.0",
            font=("Helvetica", 10),
            fg=TEXT_D, bg=BG
        ).pack(pady=(0, 25))

        # Login Box
        box = tk.Frame(self, bg=KARTE, bd=1, relief="solid")
        box.pack(padx=40, fill="x")

        tk.Label(
            box, text="Anmelden",
            font=("Helvetica", 16, "bold"),
            fg=TEXT_H, bg=KARTE
        ).pack(pady=(18, 8))

        # Benutzername
        tk.Label(
            box, text="Benutzername",
            font=("Helvetica", 10),
            fg=TEXT_M, bg=KARTE, anchor="w"
        ).pack(padx=30, fill="x")

        self.user_var = tk.StringVar(value="admin")
        user_entry = tk.Entry(
            box, textvariable=self.user_var,
            font=("Helvetica", 12),
            bg=DUNKEL, fg=TEXT_H,
            insertbackground=TEXT_H,
            relief="flat", bd=5
        )
        user_entry.pack(padx=30, pady=(3, 10), fill="x")

        # Passwort
        tk.Label(
            box, text="Passwort",
            font=("Helvetica", 10),
            fg=TEXT_M, bg=KARTE, anchor="w"
        ).pack(padx=30, fill="x")

        self.pass_var = tk.StringVar(value="XsiKOM2026!")
        pass_entry = tk.Entry(
            box, textvariable=self.pass_var,
            show="*",
            font=("Helvetica", 12),
            bg=DUNKEL, fg=TEXT_H,
            insertbackground=TEXT_H,
            relief="flat", bd=5
        )
        pass_entry.pack(padx=30, pady=(3, 12), fill="x")
        pass_entry.bind("<Return>", lambda e: self._login())

        # Login Button
        tk.Button(
            box, text="🔐 Anmelden",
            command=self._login,
            font=("Helvetica", 13, "bold"),
            bg=BTN_B, fg=TEXT_H,
            activebackground=BLAU,
            activeforeground=TEXT_H,
            relief="flat", bd=0,
            cursor="hand2",
            pady=8
        ).pack(padx=30, pady=(0, 8), fill="x")

        # Register
        tk.Button(
            box, text="Neuen Benutzer registrieren",
            command=self._register,
            font=("Helvetica", 10, "underline"),
            fg=BLAU, bg=KARTE,
            activeforeground=BLAU,
            activebackground=KARTE,
            relief="flat", bd=0,
            cursor="hand2"
        ).pack(pady=(0, 15))

        # Hinweis
        tk.Label(
            self,
            text="Admin: admin | Passwort: XsiKOM2026!",
            font=("Helvetica", 9),
            fg=TEXT_D, bg=BG
        ).pack(pady=8)

    def _login(self):
        user = self.user_var.get().strip()
        pw   = self.pass_var.get().strip()

        if not user or not pw:
            messagebox.showwarning("Fehler", "Alle Felder ausfuellen!")
            return

        result = benutzer_pruefen(user, pw)

        if result:
            self.destroy()
            self.callback(result)
        else:
            messagebox.showerror(
                "Fehler",
                "Benutzername oder Passwort falsch!"
            )

    def _register(self):
        dlg = tk.Toplevel(self)
        dlg.title("Registrieren")
        dlg.geometry("420x460")
        dlg.configure(bg=BG)
        dlg.grab_set()

        tk.Label(
            dlg, text="Neuen Benutzer anlegen",
            font=("Helvetica", 15, "bold"),
            fg=BLAU, bg=BG
        ).pack(pady=15)

        felder = {}
        for label, key, geheim in [
            ("Benutzername:", "user",     False),
            ("Passwort:",     "pass",     True),
            ("Vorname:",      "vorname",  False),
            ("Nachname:",     "nachname", False),
            ("E-Mail:",       "email",    False),
        ]:
            tk.Label(
                dlg, text=label,
                font=("Helvetica", 10),
                fg=TEXT_M, bg=BG, anchor="w"
            ).pack(padx=40, fill="x")

            v = tk.StringVar()
            e = tk.Entry(
                dlg, textvariable=v,
                font=("Helvetica", 11),
                bg=DUNKEL, fg=TEXT_H,
                insertbackground=TEXT_H,
                relief="flat", bd=5,
                show="*" if geheim else ""
            )
            e.pack(padx=40, pady=(2, 8), fill="x")
            felder[key] = v

        def _sp():
            u  = felder["user"].get().strip()
            pw = felder["pass"].get().strip()
            if not u or not pw:
                messagebox.showwarning("Fehler", "User + Passwort!")
                return
            if len(pw) < 6:
                messagebox.showwarning("Fehler", "Min. 6 Zeichen!")
                return
            ok = benutzer_anlegen(
                u, pw,
                felder["email"].get().strip(),
                felder["vorname"].get().strip(),
                felder["nachname"].get().strip()
            )
            if ok:
                messagebox.showinfo("Erfolg", f"'{u}' erstellt!")
                dlg.destroy()
            else:
                messagebox.showerror("Fehler", "Name vergeben!")

        tk.Button(
            dlg, text="💾 Registrieren",
            command=_sp,
            font=("Helvetica", 12, "bold"),
            bg=BTN_G, fg=TEXT_H,
            relief="flat", bd=0,
            cursor="hand2", pady=8
        ).pack(pady=10, padx=40, fill="x")


# ============================================================
# HAUPT APP
# ============================================================
class XsiKOMBot(tk.Tk):

    def __init__(self, user_data):
        tk.Tk.__init__(self)
        self.user    = user_data
        self.aaliyah = Aaliyah()

        self.title(
            f"XsiKOM-BewerbungsBOT - "
            f"{user_data['vorname']} {user_data['nachname']}"
        )
        self.geometry("1280x800")
        self.minsize(1100, 650)
        self.configure(bg=BG)

        try:
            self.iconbitmap("icon.ico")
        except Exception:
            pass

        self._layout()
        self.dashboard_zeigen()

    # ── HILFSMETHODEN ────────────────────────────────────
    def _btn(self, parent, text, cmd, farbe=BTN_B,
             breite=None, hoehe=1):
        b = tk.Button(
            parent, text=text, command=cmd,
            font=("Helvetica", 11, "bold"),
            bg=farbe, fg=TEXT_H,
            activebackground=farbe,
            activeforeground=TEXT_H,
            relief="flat", bd=0,
            cursor="hand2",
            pady=hoehe,
            padx=12
        )
        if breite:
            b.configure(width=breite)
        return b

    def _label(self, parent, text, farbe=TEXT_H,
               groesse=11, fett=False, bg=None):
        bg  = bg or BG
        font = ("Helvetica", groesse, "bold" if fett else "normal")
        return tk.Label(
            parent, text=text,
            font=font, fg=farbe, bg=bg
        )

    def _entry(self, parent, breite=30, geheim=False):
        return tk.Entry(
            parent,
            font=("Helvetica", 11),
            bg=DUNKEL, fg=TEXT_H,
            insertbackground=TEXT_H,
            relief="flat", bd=5,
            show="*" if geheim else "",
            width=breite
        )

    def _leer(self):
        for w in self.haupt_frame.winfo_children():
            w.destroy()

    def _thread(self, fn, *args):
        t = threading.Thread(target=fn, args=args, daemon=True)
        t.start()

    def _status(self, text, farbe=GRUEN):
        self.status_lbl.configure(text=f"● {text}", fg=farbe)
        self.update()

    def _trennlinie(self, parent, bg=None):
        tk.Frame(
            parent,
            bg=bg or HELL_RAND,
            height=1
        ).pack(fill="x", padx=10, pady=3)

    def _karte(self, parent, bg=KARTE):
        f = tk.Frame(parent, bg=bg, bd=1, relief="solid")
        return f

    # ── LAYOUT ───────────────────────────────────────────
    def _layout(self):
        # Sidebar
        self.sidebar = tk.Frame(
            self, bg=SIDEBAR, width=230
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Logo
        logo = tk.Frame(self.sidebar, bg="#162635")
        logo.pack(fill="x", pady=(0, 5))

        tk.Label(
            logo, text="XsiKOM",
            font=("Helvetica", 22, "bold"),
            fg=BLAU, bg="#162635"
        ).pack(pady=(15, 0))

        tk.Label(
            logo, text="BewerbungsBOT",
            font=("Helvetica", 11, "bold"),
            fg=GRUEN, bg="#162635"
        ).pack()

        tk.Label(
            logo,
            text=f"👤 {self.user['vorname']} | {self.user['rolle'].upper()}",
            font=("Helvetica", 9),
            fg=TEXT_D, bg="#162635"
        ).pack(pady=(2, 10))

        tk.Frame(self.sidebar, bg=HELL_RAND, height=1).pack(fill="x", padx=10, pady=3)

        # Menü
        menu = [
            ("🏠 Dashboard",     self.dashboard_zeigen,    BLAU),
            ("🔍 Stellensuche",  self.stellensuche_zeigen, GRUEN),
            ("📧 Bewerbungen",   self.bewerbungen_zeigen,  ORANGE),
            ("📊 Tracker",       self.tracker_zeigen,      PINK),
            ("📄 Lebenslauf",    self.lebenslauf_zeigen,   GELB),
            ("🤖 Aaliyah KI",    self.aaliyah_zeigen,      PINK),
            ("📈 Statistiken",   self.statistiken_zeigen,  GELB),
            ("❓ Hilfe",         self.hilfe_zeigen,        TEXT_M),
        ]

        if self.user.get("rolle") == "admin":
            menu.append(("⚙️ Admin Panel", self.admin_zeigen, ROT))

        menu.append(("🚪 Abmelden", self.abmelden, TEXT_D))

        for text, cmd, farbe in menu:
            tk.Button(
                self.sidebar, text=f"  {text}",
                command=cmd,
                font=("Helvetica", 11),
                bg=SIDEBAR, fg=TEXT_H,
                activebackground="#1E3A4F",
                activeforeground=farbe,
                relief="flat", bd=0,
                cursor="hand2",
                anchor="w",
                pady=6
            ).pack(fill="x", padx=8, pady=1)

        # Status
        tk.Frame(self.sidebar, bg="transparent").pack(fill="both", expand=True)
        tk.Frame(self.sidebar, bg=HELL_RAND, height=1).pack(fill="x", padx=10, pady=3)

        self.status_lbl = tk.Label(
            self.sidebar,
            text="● Bereit",
            font=("Helvetica", 10),
            fg=GRUEN, bg=SIDEBAR
        )
        self.status_lbl.pack(pady=8)

        # Hauptbereich
        self.haupt_frame = tk.Frame(self, bg=BG)
        self.haupt_frame.pack(side="right", fill="both", expand=True)

    def _header(self, titel, sub="", farbe=BLAU):
        h = tk.Frame(self.haupt_frame, bg=SIDEBAR, height=65)
        h.pack(fill="x")
        h.pack_propagate(False)

        tk.Frame(h, bg=farbe, height=3).pack(fill="x")

        tf = tk.Frame(h, bg=SIDEBAR)
        tf.pack(side="left", padx=20, pady=8)

        tk.Label(
            tf, text=titel,
            font=("Helvetica", 17, "bold"),
            fg=TEXT_H, bg=SIDEBAR
        ).pack(anchor="w")

        if sub:
            tk.Label(
                tf, text=sub,
                font=("Helvetica", 9),
                fg=TEXT_D, bg=SIDEBAR
            ).pack(anchor="w")

        tk.Label(
            h,
            text=datetime.now().strftime("%d.%m.%Y %H:%M"),
            font=("Helvetica", 10),
            fg=farbe, bg=SIDEBAR
        ).pack(side="right", padx=20)

    def _scroll_frame(self):
        container = tk.Frame(self.haupt_frame, bg=BG)
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container, bg=BG, highlightthickness=0)
        sb = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scroll = tk.Frame(canvas, bg=BG)

        scroll.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)

        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        return scroll

    # ============================================================
    # DASHBOARD
    # ============================================================
    def dashboard_zeigen(self):
        self._leer()
        self._header("🏠 Dashboard", f"Willkommen, {self.user['vorname']}!", BLAU)
        scroll = self._scroll_frame()

        # Statistiken
        stats = self._stats_laden()

        stat_f = tk.Frame(scroll, bg=BG)
        stat_f.pack(fill="x", padx=15, pady=12)

        for i, (e, w, l, f) in enumerate([
            ("📋", stats["stellen"],     "Stellen",     BLAU),
            ("📧", stats["gesendet"],    "Gesendet",    GRUEN),
            ("💬", stats["antworten"],   "Antworten",   ORANGE),
            ("🎉", stats["einladungen"], "Einladungen", PINK),
        ]):
            karte = tk.Frame(stat_f, bg=KARTE, bd=1, relief="solid", width=160, height=100)
            karte.grid(row=0, column=i, padx=6, sticky="ew")
            karte.pack_propagate(False)
            stat_f.grid_columnconfigure(i, weight=1)

            tk.Frame(karte, bg=f, height=4).pack(fill="x")
            tk.Label(karte, text=e, font=("Helvetica", 20), bg=KARTE).pack(pady=(8, 0))
            tk.Label(karte, text=str(w), font=("Helvetica", 22, "bold"), fg=f, bg=KARTE).pack()
            tk.Label(karte, text=l, font=("Helvetica", 10), fg=TEXT_M, bg=KARTE).pack(pady=(0, 8))

        # Aaliyah Tipp
        tipp_k = self._karte(scroll)
        tipp_k.pack(fill="x", padx=15, pady=8)

        tk.Frame(tipp_k, bg=PINK, height=3).pack(fill="x")
        tk.Label(tipp_k, text="🤖 Aaliyah Tipp des Tages", font=("Helvetica", 11, "bold"), fg=PINK, bg=KARTE).pack(anchor="w", padx=12, pady=(5, 2))
        tk.Label(tipp_k, text=self.aaliyah.zufalls_tipp(), font=("Helvetica", 10), fg=TEXT_H, bg=KARTE, wraplength=750, justify="left").pack(anchor="w", padx=12, pady=(0, 10))

        # Schnellaktionen
        tk.Label(scroll, text="⚡ SCHNELLAKTIONEN", font=("Helvetica", 10, "bold"), fg=TEXT_D, bg=BG).pack(anchor="w", padx=15, pady=(8, 4))

        af = tk.Frame(scroll, bg=BG)
        af.pack(fill="x", padx=15, pady=(0, 10))

        for i, (t, f, c) in enumerate([
            ("🔍 Stellen suchen",   BTN_B,  self._suche_starten),
            ("📧 Bewerbung senden", BTN_G,  self.bewerbungen_zeigen),
            ("🤖 Aaliyah fragen",   "#C0578A", self.aaliyah_zeigen),
            ("📄 Lebenslauf",       BTN_O,  self.lebenslauf_zeigen),
        ]):
            b = self._btn(af, t, c, f)
            b.grid(row=0, column=i, padx=5, sticky="ew")
            af.grid_columnconfigure(i, weight=1)

        # Letzte Bewerbungen
        tk.Label(scroll, text="📬 LETZTE BEWERBUNGEN", font=("Helvetica", 10, "bold"), fg=TEXT_D, bg=BG).pack(anchor="w", padx=15, pady=(8, 4))

        bew_k = self._karte(scroll)
        bew_k.pack(fill="x", padx=15, pady=(0, 15))

        # Header
        h_f = tk.Frame(bew_k, bg=SIDEBAR)
        h_f.pack(fill="x", padx=2, pady=2)

        for t, w in [("Firma", 20), ("Position", 25), ("Status", 12), ("Datum", 15)]:
            tk.Label(h_f, text=t, font=("Helvetica", 10, "bold"), fg=BLAU, bg=SIDEBAR, width=w, anchor="w").pack(side="left", padx=8, pady=5)

        bewerbungen = self._bew_laden(5)
        if not bewerbungen:
            tk.Label(bew_k, text="Noch keine Bewerbungen.", font=("Helvetica", 11), fg=TEXT_D, bg=KARTE).pack(pady=15)
        else:
            for i, b in enumerate(bewerbungen):
                bg = KARTE if i % 2 == 0 else DUNKEL
                z  = tk.Frame(bew_k, bg=bg)
                z.pack(fill="x", padx=2, pady=1)

                sf_map = {"gesendet": GRUEN, "trockenlauf": GELB, "fehler": ROT}
                s_f = sf_map.get(str(b[4]), TEXT_H)

                for t, w, f in [
                    (str(b[1])[:22] if b[1] else "N/A", 20, TEXT_H),
                    (str(b[2])[:26] if b[2] else "N/A", 25, TEXT_H),
                    (str(b[4])[:10] if b[4] else "N/A", 12, s_f),
                    (str(b[5])[:14] if b[5] else "N/A", 15, TEXT_D),
                ]:
                    tk.Label(z, text=t, font=("Helvetica", 10), fg=f, bg=bg, width=w, anchor="w").pack(side="left", padx=8, pady=4)

    # ============================================================
    # STELLENSUCHE
    # ============================================================
    def stellensuche_zeigen(self):
        self._leer()
        self._header("🔍 Stellensuche", "8 Portale | 30 Staedte", GRUEN)
        scroll = self._scroll_frame()

        # Portale
        pf = tk.Frame(scroll, bg=BG)
        pf.pack(fill="x", padx=15, pady=10)

        for i, n in enumerate(["Indeed", "StepStone", "Monster", "XING", "LinkedIn", "Glassdoor", "Arbeitsagentur", "Kimeta"]):
            k = self._karte(pf)
            k.grid(row=i//4, column=i%4, padx=4, pady=4, sticky="ew")
            pf.grid_columnconfigure(i%4, weight=1)
            tk.Label(k, text=f"✅ {n}", font=("Helvetica", 11), fg=GRUEN, bg=KARTE).pack(pady=10, padx=10)

        # Buttons
        bf = tk.Frame(scroll, bg=BG)
        bf.pack(fill="x", padx=15, pady=8)

        for i, (t, f, c) in enumerate([
            ("🔍 Alle Portale",  BTN_B,  self._suche_starten),
            ("🏢 IT-Firmen",     BTN_G,  self._it_firmen),
            ("🌐 Webseiten",     BTN_O,  self._webseiten),
        ]):
            b = self._btn(bf, t, c, f)
            b.grid(row=0, column=i, padx=5, sticky="ew")
            bf.grid_columnconfigure(i, weight=1)

        # Log
        tk.Label(scroll, text="📋 SUCH-LOG", font=("Helvetica", 10, "bold"), fg=TEXT_D, bg=BG).pack(anchor="w", padx=15, pady=(10, 4))

        lk = self._karte(scroll)
        lk.pack(fill="x", padx=15, pady=(0, 10))

        self.log_box = tk.Text(
            lk, height=10,
            font=("Consolas", 10),
            bg=DUNKEL, fg=GRUEN,
            insertbackground=GRUEN,
            relief="flat", bd=8
        )
        self.log_box.pack(fill="x", padx=8, pady=8)
        self.log_box.insert("end", "Bereit fuer Stellensuche...\n")

    # ============================================================
    # BEWERBUNGEN
    # ============================================================
    def bewerbungen_zeigen(self):
        self._leer()
        self._header("📧 Bewerbungen", "Senden & Verwalten", ORANGE)
        scroll = self._scroll_frame()

        tk.Label(scroll, text="📧 EINZELNE BEWERBUNG", font=("Helvetica", 10, "bold"), fg=TEXT_D, bg=BG).pack(anchor="w", padx=15, pady=(8, 4))

        fk = self._karte(scroll)
        fk.pack(fill="x", padx=15, pady=(0, 10))

        form = tk.Frame(fk, bg=KARTE)
        form.pack(fill="x", padx=15, pady=12)

        tk.Label(form, text="Firma:", font=("Helvetica", 11), fg=TEXT_M, bg=KARTE).grid(row=0, column=0, padx=8, pady=6, sticky="w")
        self.firma_entry = self._entry(form, breite=40)
        self.firma_entry.grid(row=0, column=1, padx=8, pady=6)

        tk.Label(form, text="E-Mail:", font=("Helvetica", 11), fg=TEXT_M, bg=KARTE).grid(row=1, column=0, padx=8, pady=6, sticky="w")
        self.email_entry = self._entry(form, breite=40)
        self.email_entry.grid(row=1, column=1, padx=8, pady=6)

        tk.Label(form, text="Bereich:", font=("Helvetica", 11), fg=TEXT_M, bg=KARTE).grid(row=2, column=0, padx=8, pady=6, sticky="w")
        self.bereich_var = tk.StringVar(value="allgemein")
        bereich_menu = ttk.Combobox(form, textvariable=self.bereich_var, values=["allgemein", "netzwerk", "systemadmin", "support"], width=20, state="readonly")
        bereich_menu.grid(row=2, column=1, padx=8, pady=6, sticky="w")

        bf = tk.Frame(fk, bg=KARTE)
        bf.pack(fill="x", padx=15, pady=(0, 12))

        self._btn(bf, "📄 Anschreiben",  self._anschreiben,          BTN_O).pack(side="left", padx=4)
        self._btn(bf, "📧 LIVE senden",  lambda: self._senden(False), BTN_G).pack(side="left", padx=4)
        self._btn(bf, "🔄 Trockenlauf",  lambda: self._senden(True),  BTN_B).pack(side="left", padx=4)

        # Massenbewerbung
        tk.Label(scroll, text="📬 MASSENBEWERBUNG", font=("Helvetica", 10, "bold"), fg=TEXT_D, bg=BG).pack(anchor="w", padx=15, pady=(10, 4))

        mk = self._karte(scroll)
        mk.pack(fill="x", padx=15, pady=(0, 15))

        stellen   = self._stellen_laden()
        mit_email = sum(1 for s in stellen if s[4])

        info = tk.Frame(mk, bg=KARTE)
        info.pack(fill="x", padx=12, pady=10)

        for t, w, f in [
            ("Stellen:", str(len(stellen)), TEXT_H),
            ("Mit E-Mail:", str(mit_email), GRUEN),
            ("Ohne:", str(len(stellen)-mit_email), ROT),
        ]:
            tk.Label(info, text=f"{t} {w}", font=("Helvetica", 11), fg=f, bg=KARTE).pack(side="left", padx=12)

        mb = tk.Frame(mk, bg=KARTE)
        mb.pack(fill="x", padx=12, pady=(0, 12))

        self._btn(mb, "🔄 Trockenlauf",  lambda: self._masse(True),  BTN_B).pack(side="left", padx=4)
        self._btn(mb, "🚀 LIVE Senden!", lambda: self._masse(False), ROT).pack(side="left", padx=4)

    # ============================================================
    # TRACKER
    # ============================================================
    def tracker_zeigen(self):
        self._leer()
        self._header("📊 Tracker", "Antworten & Status", PINK)
        scroll = self._scroll_frame()

        tracker = self._tracker_laden()

        if not tracker:
            tk.Label(scroll, text="Noch keine Bewerbungen im Tracker.", font=("Helvetica", 12), fg=TEXT_D, bg=BG).pack(pady=40)
        else:
            for t in tracker:
                sf = GRUEN if t[6] else (ROT if t[7] else GELB)
                st = "EINLADUNG!" if t[6] else ("Absage" if t[7] else "Ausstehend")

                k = self._karte(scroll)
                k.pack(fill="x", padx=15, pady=3)

                z = tk.Frame(k, bg=KARTE)
                z.pack(fill="x", padx=5, pady=5)

                tk.Frame(z, bg=sf, width=4).pack(side="left", fill="y", padx=(0, 10))
                tk.Label(z, text=str(t[1])[:25] if t[1] else "N/A", font=("Helvetica", 11, "bold"), fg=TEXT_H, bg=KARTE, width=22, anchor="w").pack(side="left")
                tk.Label(z, text=st, font=("Helvetica", 11, "bold"), fg=sf, bg=KARTE, width=12, anchor="w").pack(side="left", padx=5)
                tk.Label(z, text=str(t[4])[:15] if t[4] else "N/A", font=("Helvetica", 10), fg=TEXT_D, bg=KARTE, width=14, anchor="w").pack(side="left")
                self._btn(z, "✏️", lambda tid=t[0]: self._antwort_dlg(tid), BTN_L, breite=4).pack(side="right", padx=8)

        self._btn(scroll, "🔔 Erinnerungen pruefen", self._erinnerungen, BTN_O).pack(anchor="w", padx=15, pady=12)

    # ============================================================
    # LEBENSLAUF
    # ============================================================
    def lebenslauf_zeigen(self):
        self._leer()
        self._header("📄 Lebenslauf-Editor", "Dein Profil", GELB)
        scroll = self._scroll_frame()

        from lebenslauf_editor import standard_profil, benutzer_daten_laden, benutzer_daten_speichern, lebenslauf_aus_profil

        profil = benutzer_daten_laden(self.user["benutzername"]) or standard_profil()

        fk = self._karte(scroll)
        fk.pack(fill="x", padx=15, pady=(8, 10))

        tk.Frame(fk, bg=GELB, height=3).pack(fill="x")
        tk.Label(fk, text="👤 PERSOENLICHE DATEN", font=("Helvetica", 11, "bold"), fg=GELB, bg=KARTE).pack(anchor="w", padx=12, pady=(6, 4))

        form = tk.Frame(fk, bg=KARTE)
        form.pack(fill="x", padx=12, pady=(0, 8))

        self.lv = {}
        felder  = [
            ("Vorname:", "vorname"), ("Nachname:", "nachname"),
            ("Strasse:", "strasse"), ("PLZ:", "plz"),
            ("Stadt:", "stadt"), ("Telefon:", "telefon"),
            ("E-Mail:", "email"), ("Geburtsdatum:", "geburtsdatum"),
        ]

        for i, (label, key) in enumerate(felder):
            r = i // 2
            c = (i % 2) * 2
            tk.Label(form, text=label, font=("Helvetica", 10), fg=TEXT_M, bg=KARTE).grid(row=r, column=c, padx=(8, 4), pady=5, sticky="w")
            e = self._entry(form, breite=25)
            e.grid(row=r, column=c+1, padx=(0, 12), pady=5)
            e.insert(0, profil.get(key, ""))
            self.lv[key] = e

        # Kenntnisse
        tk.Label(fk, text="IT-Kenntnisse (eine pro Zeile):", font=("Helvetica", 10), fg=TEXT_M, bg=KARTE).pack(anchor="w", padx=12)
        self.lv_ken = tk.Text(fk, height=7, font=("Helvetica", 10), bg=DUNKEL, fg=TEXT_H, insertbackground=TEXT_H, relief="flat", bd=5)
        self.lv_ken.pack(fill="x", padx=12, pady=4)
        self.lv_ken.insert("1.0", "\n".join(profil.get("kenntnisse", [])))

        # Sprachen
        tk.Label(fk, text="Sprachen:", font=("Helvetica", 10), fg=TEXT_M, bg=KARTE).pack(anchor="w", padx=12)
        self.lv_spr = tk.Text(fk, height=4, font=("Helvetica", 10), bg=DUNKEL, fg=TEXT_H, insertbackground=TEXT_H, relief="flat", bd=5)
        self.lv_spr.pack(fill="x", padx=12, pady=4)
        self.lv_spr.insert("1.0", "\n".join(profil.get("sprachen", [])))

        # Buttons
        bbf = tk.Frame(scroll, bg=BG)
        bbf.pack(fill="x", padx=15, pady=8)

        self._btn(bbf, "💾 Speichern",    self._lv_speichern, BTN_G).pack(side="left", padx=4)
        self._btn(bbf, "📄 PDF erstellen", self._lv_pdf,       BTN_B).pack(side="left", padx=4)

    def _lv_speichern(self):
        from lebenslauf_editor import benutzer_daten_speichern
        profil = {k: e.get().strip() for k, e in self.lv.items()}
        profil["kenntnisse"] = [z.strip() for z in self.lv_ken.get("1.0", "end").strip().split("\n") if z.strip()]
        profil["sprachen"]   = [z.strip() for z in self.lv_spr.get("1.0", "end").strip().split("\n") if z.strip()]
        profil["berufserfahrung"] = []
        profil["zertifikate"]     = []
        benutzer_daten_speichern(self.user["benutzername"], profil)
        messagebox.showinfo("Gespeichert", "Profil gespeichert!")

    def _lv_pdf(self):
        from lebenslauf_editor import benutzer_daten_laden, lebenslauf_aus_profil
        self._lv_speichern()
        profil = benutzer_daten_laden(self.user["benutzername"])
        if profil:
            pfad = lebenslauf_aus_profil(profil)
            messagebox.showinfo("PDF erstellt", f"Lebenslauf:\n{pfad}")
            os.startfile(pfad)

    # ============================================================
    # AALIYAH
    # ============================================================
    def aaliyah_zeigen(self):
        self._leer()
        self._header("🤖 Aaliyah KI", "Deine Bewerbungsberaterin", PINK)

        main = tk.Frame(self.haupt_frame, bg=BG)
        main.pack(fill="both", expand=True, padx=15, pady=10)

        # Chat
        ck = self._karte(main)
        ck.pack(fill="both", expand=True, pady=(0, 8))

        tk.Frame(ck, bg=PINK, height=3).pack(fill="x")
        tk.Label(ck, text="💬 Chat mit Aaliyah", font=("Helvetica", 11, "bold"), fg=PINK, bg=KARTE).pack(anchor="w", padx=12, pady=(5, 2))

        self.chat_box = tk.Text(
            ck, height=18,
            font=("Helvetica", 11),
            bg=DUNKEL, fg=TEXT_H,
            insertbackground=TEXT_H,
            relief="flat", bd=8,
            wrap="word"
        )
        self.chat_box.pack(fill="both", expand=True, padx=10, pady=6)
        self.chat_box.insert("end", f"🤖 Aaliyah: {self.aaliyah.begruessung()}\n\n")
        self.chat_box.insert("end", "💡 Probiere: 'tipps bewerbung' | 'lebenslauf' | 'gehalt' | 'netzwerk'\n\n")

        # Input
        inf = tk.Frame(main, bg=KARTE)
        inf.pack(fill="x", pady=(0, 8))

        self.aaliyah_entry = self._entry(inf, breite=55)
        self.aaliyah_entry.pack(side="left", padx=(10, 8), pady=10)
        self.aaliyah_entry.bind("<Return>", lambda e: self._aaliyah_send())

        self._btn(inf, "📤 Senden",  self._aaliyah_send,  PINK,    breite=10).pack(side="left", padx=(0, 6), pady=10)
        self._btn(inf, "🗑️ Löschen", self._aaliyah_clear, BTN_L,  breite=10).pack(side="left", pady=10)

        # Schnellfragen
        sf = tk.Frame(main, bg=BG)
        sf.pack(fill="x")

        for i, t in enumerate(["tipps bewerbung", "lebenslauf", "gespraech", "gehalt", "netzwerk", "stress"]):
            tk.Button(
                sf, text=t,
                command=lambda q=t: self._aaliyah_quick(q),
                font=("Helvetica", 9),
                bg=KARTE, fg=TEXT_H,
                activebackground=HELL_RAND,
                relief="flat", bd=1,
                cursor="hand2",
                pady=4
            ).grid(row=0, column=i, padx=3, sticky="ew")
            sf.grid_columnconfigure(i, weight=1)

    def _aaliyah_send(self):
        frage = self.aaliyah_entry.get().strip()
        if not frage:
            return
        self.chat_box.insert("end", f"👤 Du: {frage}\n")
        self.aaliyah_entry.delete(0, "end")
        antwort = self.aaliyah.antwort(frage)
        self.chat_box.insert("end", f"\n🤖 Aaliyah: {antwort}\n\n")
        self.chat_box.see("end")

    def _aaliyah_quick(self, frage):
        self.aaliyah_entry.delete(0, "end")
        self.aaliyah_entry.insert(0, frage)
        self._aaliyah_send()

    def _aaliyah_clear(self):
        self.chat_box.delete("1.0", "end")
        self.aaliyah.verlauf_leeren()
        self.chat_box.insert("end", f"🤖 Aaliyah: {self.aaliyah.begruessung()}\n\n")

    # ============================================================
    # STATISTIKEN
    # ============================================================
    def statistiken_zeigen(self):
        self._leer()
        self._header("📈 Statistiken", "Auswertung & Charts", GELB)
        scroll = self._scroll_frame()

        stats = self._stats_laden()
        sf    = tk.Frame(scroll, bg=BG)
        sf.pack(fill="x", padx=15, pady=12)

        for i, (e, w, l, f) in enumerate([
            ("📋", stats["stellen"],     "Stellen",     BLAU),
            ("📧", stats["gesamt"],      "Gesamt",      GRUEN),
            ("✅", stats["gesendet"],    "Gesendet",    ORANGE),
            ("💬", stats["antworten"],   "Antworten",   GELB),
            ("🎉", stats["einladungen"], "Einladungen", PINK),
            ("❌", stats["absagen"],     "Absagen",     ROT),
        ]):
            karte = tk.Frame(sf, bg=KARTE, bd=1, relief="solid", width=170, height=95)
            karte.grid(row=i//3, column=i%3, padx=6, pady=6, sticky="ew")
            karte.pack_propagate(False)
            sf.grid_columnconfigure(i%3, weight=1)

            tk.Frame(karte, bg=f, height=4).pack(fill="x")
            tk.Label(karte, text=e, font=("Helvetica", 18), bg=KARTE).pack(pady=(5, 0))
            tk.Label(karte, text=str(w), font=("Helvetica", 20, "bold"), fg=f, bg=KARTE).pack()
            tk.Label(karte, text=l, font=("Helvetica", 9), fg=TEXT_M, bg=KARTE).pack()

        bf = tk.Frame(scroll, bg=BG)
        bf.pack(fill="x", padx=15, pady=8)
        self._btn(bf, "📊 Charts erstellen", self._charts, BTN_O).pack(side="left", padx=4)
        self._btn(bf, "📥 Excel Export",     self._excel,  BTN_L).pack(side="left", padx=4)

    # ============================================================
    # HILFE
    # ============================================================
    def hilfe_zeigen(self):
        self._leer()
        self._header("❓ Hilfe & Support", "Anleitung & FAQ", TEXT_M)
        scroll = self._scroll_frame()

        themen = [
            ("🚀 ERSTE SCHRITTE", BLAU, ["1. Stellensuche starten", "2. IT-Firmen hinzufuegen", "3. Stellen pruefen", "4. Trockenlauf testen", "5. LIVE senden"]),
            ("🤖 AALIYAH KI", PINK, ["Deine KI-Beraterin!", "Frag nach: Bewerbungstipps,", "Lebenslauf, Gespraech, Gehalt..."]),
            ("📧 E-MAIL", GRUEN, ["Gmail App-Passwort erstellen", "In config.py eintragen", "Verbindung testen"]),
            ("⚠️ FEHLER", ROT, ["App-Passwort falsch → Neu erstellen", "PDF fehlt → PDFs neu erstellen", "Telegram → Bot in Telegram starten"]),
        ]

        for titel, farbe, punkte in themen:
            k = self._karte(scroll)
            k.pack(fill="x", padx=15, pady=5)

            tk.Frame(k, bg=farbe, height=3).pack(fill="x")
            tk.Label(k, text=titel, font=("Helvetica", 11, "bold"), fg=farbe, bg=KARTE).pack(anchor="w", padx=12, pady=(5, 2))

            for p in punkte:
                tk.Label(k, text=f"  • {p}", font=("Helvetica", 10), fg=TEXT_H, bg=KARTE, anchor="w").pack(anchor="w", padx=20, pady=1)

            tk.Label(k, text="", bg=KARTE).pack()

    # ============================================================
    # ADMIN
    # ============================================================
    def admin_zeigen(self):
        if self.user.get("rolle") != "admin":
            messagebox.showerror("Fehler", "Nur Admins!")
            return

        self._leer()
        self._header("⚙️ Admin Panel", "Benutzerverwaltung", ROT)
        scroll = self._scroll_frame()

        tk.Label(scroll, text="👥 BENUTZER", font=("Helvetica", 10, "bold"), fg=TEXT_D, bg=BG).pack(anchor="w", padx=15, pady=(8, 4))

        for u in alle_benutzer_laden():
            rf = ROT if u[5] == "admin" else BLAU
            k  = self._karte(scroll)
            k.pack(fill="x", padx=15, pady=2)

            z = tk.Frame(k, bg=KARTE)
            z.pack(fill="x", padx=5, pady=5)

            tk.Frame(z, bg=rf, width=4).pack(side="left", fill="y", padx=(0, 8))
            tk.Label(z, text=f"{u[1]} - {u[3]} {u[4]}", font=("Helvetica", 11, "bold"), fg=TEXT_H, bg=KARTE, width=28, anchor="w").pack(side="left")
            tk.Label(z, text=u[5].upper(), font=("Helvetica", 9, "bold"), fg=rf, bg=KARTE, width=8).pack(side="left")

            if u[5] != "admin":
                self._btn(z, "🗑️", lambda uid=u[0]: self._user_del(uid), ROT, breite=3).pack(side="right", padx=8)

        tk.Label(scroll, text="➕ NEUEN BENUTZER ANLEGEN", font=("Helvetica", 10, "bold"), fg=TEXT_D, bg=BG).pack(anchor="w", padx=15, pady=(15, 4))

        nk = self._karte(scroll)
        nk.pack(fill="x", padx=15)

        form = tk.Frame(nk, bg=KARTE)
        form.pack(fill="x", padx=12, pady=10)

        self.adm = {}
        for i, (label, key, geheim) in enumerate([
            ("Benutzername:", "user",     False),
            ("Passwort:",     "pass",     True),
            ("Vorname:",      "vorname",  False),
            ("Nachname:",     "nachname", False),
        ]):
            r = i // 2
            c = (i % 2) * 2
            tk.Label(form, text=label, font=("Helvetica", 10), fg=TEXT_M, bg=KARTE).grid(row=r, column=c, padx=(8, 4), pady=6, sticky="w")
            e = self._entry(form, breite=22, geheim=geheim)
            e.grid(row=r, column=c+1, padx=(0, 12), pady=6)
            self.adm[key] = e

        self._btn(nk, "➕ Benutzer anlegen", self._user_anlegen, BTN_G).pack(anchor="w", padx=12, pady=(0, 12))

    def _user_anlegen(self):
        u  = self.adm["user"].get().strip()
        pw = self.adm["pass"].get().strip()
        vn = self.adm["vorname"].get().strip()
        nn = self.adm["nachname"].get().strip()
        if not u or not pw:
            messagebox.showwarning("Fehler", "User + Passwort!")
            return
        ok = benutzer_anlegen(u, pw, "", vn, nn)
        if ok:
            messagebox.showinfo("Erfolg", f"'{u}' erstellt!")
            self.admin_zeigen()
        else:
            messagebox.showerror("Fehler", "Name vergeben!")

    def _user_del(self, uid):
        if messagebox.askyesno("Loeschen?", "Benutzer loeschen?"):
            benutzer_loeschen(uid)
            self.admin_zeigen()

    # ============================================================
    # AKTIONEN
    # ============================================================
    def _suche_starten(self):
        def fn():
            self._status("Suche...", GELB)
            try:
                from job_suche import vollsuche_starten
                vollsuche_starten()
                self._status("Fertig!", GRUEN)
                messagebox.showinfo("Fertig", "Stellensuche abgeschlossen!")
            except Exception as e:
                self._status("Fehler!", ROT)
                messagebox.showerror("Fehler", str(e))
        self._thread(fn)

    def _it_firmen(self):
        def fn():
            self._status("Firmen...", GELB)
            try:
                from job_suche import it_firmen_hinzufuegen
                n = it_firmen_hinzufuegen()
                self._status("Fertig!", GRUEN)
                messagebox.showinfo("Fertig", f"{n} IT-Firmen hinzugefuegt!")
            except Exception as e:
                messagebox.showerror("Fehler", str(e))
        self._thread(fn)

    def _webseiten(self):
        def fn():
            self._status("Webseiten...", GELB)
            try:
                from firmen_suche import alle_firmen_durchsuchen
                alle_firmen_durchsuchen()
                self._status("Fertig!", GRUEN)
                messagebox.showinfo("Fertig", "Webseiten durchsucht!")
            except Exception as e:
                messagebox.showerror("Fehler", str(e))
        self._thread(fn)

    def _anschreiben(self):
        firma = self.firma_entry.get().strip()
        if not firma:
            messagebox.showwarning("Fehler", "Firma eingeben!")
            return
        def fn():
            self._status("Erstelle...", GELB)
            try:
                from anschreiben_generator import anschreiben_erstellen
                pfad = anschreiben_erstellen(firma=firma, bereich=self.bereich_var.get())
                self._status("Fertig!", GRUEN)
                os.startfile(pfad)
            except Exception as e:
                messagebox.showerror("Fehler", str(e))
        self._thread(fn)

    def _senden(self, trockenlauf=False):
        firma = self.firma_entry.get().strip()
        email = self.email_entry.get().strip()
        if not firma or not email:
            messagebox.showwarning("Fehler", "Firma und E-Mail eingeben!")
            return
        if not trockenlauf and not messagebox.askyesno("Senden?", f"Bewerbung an {firma}?"):
            return
        def fn():
            self._status("Sende...", GELB)
            try:
                from anschreiben_generator import anschreiben_erstellen
                from email_sender import bewerbung_senden
                pfad   = anschreiben_erstellen(firma=firma, bereich=self.bereich_var.get())
                result = bewerbung_senden(
                    empfaenger=email, firma=firma,
                    position="IT-Fachtechniker / Netzwerktechniker",
                    anschreiben_pfad=pfad, trockenlauf=trockenlauf
                )
                if result:
                    self._status("Gesendet!", GRUEN)
                    messagebox.showinfo("Erfolg", "Bewerbung gesendet!")
                else:
                    self._status("Fehler!", ROT)
            except Exception as e:
                messagebox.showerror("Fehler", str(e))
        self._thread(fn)

    def _masse(self, trockenlauf=True):
        if not trockenlauf and not messagebox.askyesno("ACHTUNG!", "Echte E-Mails senden?"):
            return
        def fn():
            self._status("Masse...", GELB)
            try:
                from database import stellen_laden
                from anschreiben_generator import anschreiben_erstellen
                from email_sender import bewerbung_senden
                import time
                stellen   = stellen_laden()
                mit_email = [s for s in stellen if s[4]]
                ok        = 0
                for s in mit_email:
                    firma = s[2] if s[2] else "Unbekannt"
                    email = s[4]
                    try:
                        pfad = anschreiben_erstellen(firma=firma, bereich="allgemein")
                    except Exception:
                        pfad = None
                    result = bewerbung_senden(
                        empfaenger=email, firma=firma,
                        position="IT-Fachtechniker / Netzwerktechniker",
                        anschreiben_pfad=pfad, trockenlauf=trockenlauf
                    )
                    if result:
                        ok += 1
                    if not trockenlauf:
                        time.sleep(30)
                self._status("Fertig!", GRUEN)
                messagebox.showinfo("Fertig", f"{ok} Bewerbungen verarbeitet!")
            except Exception as e:
                messagebox.showerror("Fehler", str(e))
        self._thread(fn)

    def _charts(self):
        def fn():
            self._status("Charts...", GELB)
            try:
                from charts import charts_erstellen
                charts_erstellen()
                self._status("Fertig!", GRUEN)
                messagebox.showinfo("Fertig", "Charts erstellt!")
            except Exception as e:
                messagebox.showerror("Fehler", str(e))
        self._thread(fn)

    def _excel(self):
        def fn():
            self._status("Export...", GELB)
            try:
                from excel_export import excel_export
                excel_export()
                self._status("Fertig!", GRUEN)
                messagebox.showinfo("Fertig", "Excel exportiert!")
            except Exception as e:
                messagebox.showerror("Fehler", str(e))
        self._thread(fn)

    def _antwort_dlg(self, tracker_id):
        dlg = tk.Toplevel(self)
        dlg.title("Antwort eintragen")
        dlg.geometry("380x340")
        dlg.configure(bg=BG)
        dlg.grab_set()

        tk.Label(dlg, text="Antwort eintragen", font=("Helvetica", 14, "bold"), fg=BLAU, bg=BG).pack(pady=12)

        sv = tk.StringVar(value="positiv")
        for t, v, f in [
            ("🎉 Einladung!", "einladung", GRUEN),
            ("✅ Positiv",    "positiv",   BLAU),
            ("❌ Absage",     "absage",    ROT),
            ("💬 Neutral",    "neutral",   GELB),
        ]:
            tk.Radiobutton(dlg, text=t, variable=sv, value=v, fg=f, bg=BG, activebackground=BG, selectcolor=DUNKEL, font=("Helvetica", 11)).pack(anchor="w", padx=30, pady=3)

        notiz = self._entry(dlg, breite=35)
        notiz.pack(pady=8)
        notiz.insert(0, "Notiz...")

        def _sp():
            from bewerbungs_tracker import antwort_eintragen
            status = sv.get()
            antwort_eintragen(tracker_id, status, notiz.get(), einladung=(status == "einladung"))
            dlg.destroy()
            messagebox.showinfo("OK", "Gespeichert!")
            self.tracker_zeigen()

        self._btn(dlg, "💾 Speichern", _sp, BTN_G).pack(pady=12)

    def _erinnerungen(self):
        def fn():
            try:
                from bewerbungs_tracker import erinnerungen_pruefen
                e = erinnerungen_pruefen()
                messagebox.showinfo("Info", f"{len(e)} Erinnerungen!")
            except Exception as e:
                messagebox.showerror("Fehler", str(e))
        self._thread(fn)

    def abmelden(self):
        if messagebox.askyesno("Abmelden?", "Wirklich abmelden?"):
            self.destroy()
            starten()

    # ============================================================
    # DATEN LADEN
    # ============================================================
    def _stats_laden(self):
        try:
            conn = sqlite3.connect(DB_NAME)
            c    = conn.cursor()
            c.execute("SELECT COUNT(*) FROM stellen")
            stellen = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM bewerbungen")
            gesamt = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM bewerbungen WHERE status='gesendet'")
            gesendet = c.fetchone()[0]
            try:
                c.execute("SELECT COUNT(*) FROM tracker WHERE antwort_status != 'ausstehend'")
                antworten = c.fetchone()[0]
                c.execute("SELECT COUNT(*) FROM tracker WHERE einladung=1")
                einladungen = c.fetchone()[0]
                c.execute("SELECT COUNT(*) FROM tracker WHERE absage=1")
                absagen = c.fetchone()[0]
            except Exception:
                antworten = einladungen = absagen = 0
            conn.close()
            return {"stellen": stellen, "gesamt": gesamt, "gesendet": gesendet, "antworten": antworten, "einladungen": einladungen, "absagen": absagen}
        except Exception:
            return {"stellen": 0, "gesamt": 0, "gesendet": 0, "antworten": 0, "einladungen": 0, "absagen": 0}

    def _bew_laden(self, limit=5):
        try:
            conn = sqlite3.connect(DB_NAME)
            c    = conn.cursor()
            c.execute(f"SELECT * FROM bewerbungen ORDER BY id DESC LIMIT {limit}")
            r = c.fetchall()
            conn.close()
            return r
        except Exception:
            return []

    def _stellen_laden(self):
        try:
            from database import stellen_laden
            return stellen_laden()
        except Exception:
            return []

    def _tracker_laden(self):
        try:
            conn = sqlite3.connect(DB_NAME)
            c    = conn.cursor()
            c.execute("SELECT * FROM tracker ORDER BY id DESC")
            r = c.fetchall()
            conn.close()
            return r
        except Exception:
            return []


# ============================================================
# START
# ============================================================
def starten():
    user_db_erstellen()
    admin_erstellen()

    def nach_login(user_data):
        app = XsiKOMBot(user_data)
        app.mainloop()

    login = LoginScreen(nach_login)
    login.mainloop()


if __name__ == "__main__":
    starten()