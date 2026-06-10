"""
XsiKOM-BewerbungsBOT v7.0 FINAL
"""
import customtkinter as ctk
from tkinter import messagebox
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
from lebenslauf_editor import (
    standard_profil,
    benutzer_daten_speichern,
    benutzer_daten_laden,
    lebenslauf_aus_profil
)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

HG, SIDEBAR, KARTE = "#0F1923", "#162635", "#1A2F42"
DUNKEL, RAND, GRAD = "#0A1520", "#2A4A65", "#1E3D5C"
BLAU, GRUEN, ORANGE = "#00B4D8", "#2DD4A8", "#FF8C42"
PINK, GELB, ROT = "#E040FB", "#FFD93D", "#FF5252"
TH, TM, TD = "#E8EDF2", "#8899AA", "#5C6B7A"
BB, BG2, BO, BL = "#0077B6", "#00B894", "#E17055", "#6C5CE7"
DB_NAME = "bewerbungen.db"


def mkbtn(parent, text, cmd, fg=BB, h=38, w=None):
    hovers = {
        BB: "#0090D8", BG2: "#00D8B0", BO: "#FF9070",
        BL: "#8070FF", ROT: "#FF7070", PINK: "#FF50FF",
        GRUEN: "#50FFC0", BLAU: "#30D0F0", SIDEBAR: KARTE,
        KARTE: RAND, "#C0578A": "#E070A0", "#FF69B4": "#FF80C0",
        GELB: "#FFEE60"
    }
    hover = hovers.get(fg, BB)
    b = ctk.CTkButton(parent, text=text, command=cmd,
                       fg_color=fg, hover_color=hover, height=h,
                       font=ctk.CTkFont(size=12, weight="bold"),
                       corner_radius=9)
    if w:
        b.configure(width=w)
    return b


def mkentry(parent, breite=350, ph="", geheim=False):
    return ctk.CTkEntry(parent, width=breite, height=34,
                        placeholder_text=ph, fg_color=DUNKEL,
                        border_color=RAND, text_color=TH,
                        corner_radius=7, show="*" if geheim else "")


def mkkarte(parent, h=None):
    s = ctk.CTkFrame(parent, fg_color=DUNKEL, corner_radius=14)
    k = ctk.CTkFrame(s, fg_color=KARTE, corner_radius=12,
                      border_width=1, border_color=RAND)
    k.pack(padx=(0,3), pady=(0,3), fill="both", expand=True)
    if h:
        s.configure(height=h)
        s.pack_propagate(False)
    return s, k


def mkheader(parent, titel, sub="", farbe=BLAU):
    hs = ctk.CTkFrame(parent, fg_color=DUNKEL, height=65, corner_radius=0)
    hs.pack(fill="x")
    hs.pack_propagate(False)
    h = ctk.CTkFrame(hs, fg_color=GRAD, corner_radius=0)
    h.pack(fill="both", expand=True, padx=(0,2), pady=(0,2))
    ctk.CTkFrame(h, fg_color=farbe, height=3, corner_radius=0).pack(fill="x")
    tf = ctk.CTkFrame(h, fg_color="transparent")
    tf.pack(side="left", padx=20, pady=8)
    ctk.CTkLabel(tf, text=titel, font=ctk.CTkFont(size=17, weight="bold"), text_color=TH).pack(anchor="w")
    if sub:
        ctk.CTkLabel(tf, text=sub, font=ctk.CTkFont(size=9), text_color=TD).pack(anchor="w")
    ctk.CTkLabel(h, text=datetime.now().strftime("%d.%m.%Y %H:%M"),
                  font=ctk.CTkFont(size=10), text_color=farbe).pack(side="right", padx=20)


def mklbl(parent, text, farbe=TD):
    ctk.CTkLabel(parent, text=text,
                  font=ctk.CTkFont(size=10, weight="bold"),
                  text_color=farbe).pack(anchor="w", pady=(8,4))


def mkstat(parent, emoji, wert, label, farbe):
    s, k = mkkarte(parent, h=112)
    ctk.CTkFrame(k, fg_color=farbe, height=4, corner_radius=0).pack(fill="x", padx=8, pady=(10,0))
    ctk.CTkLabel(k, text=emoji, font=ctk.CTkFont(size=22)).pack(pady=(6,0))
    ctk.CTkLabel(k, text=str(wert), font=ctk.CTkFont(size=25, weight="bold"), text_color=farbe).pack()
    ctk.CTkLabel(k, text=label, font=ctk.CTkFont(size=10), text_color=TM).pack(pady=(0,8))
    return s


class Login(ctk.CTk):

    def __init__(self, cb):
        ctk.CTk.__init__(self)
        self.cb = cb
        self.title("XsiKOM-BewerbungsBOT - Login")
        self.geometry("460x570")
        self.configure(fg_color=HG)
        self.resizable(False, False)
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="XsiKOM",
                     font=ctk.CTkFont(size=40, weight="bold"),
                     text_color=BLAU).pack(pady=(40,0))
        ctk.CTkLabel(self, text="BewerbungsBOT",
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=GRUEN).pack()
        ctk.CTkLabel(self, text="Version 7.0  |  Komi Tevi",
                     font=ctk.CTkFont(size=9), text_color=TD).pack(pady=(0,20))

        box = ctk.CTkFrame(self, fg_color=KARTE, corner_radius=16,
                            border_width=1, border_color=RAND)
        box.pack(padx=40, fill="x")

        ctk.CTkLabel(box, text="Anmelden",
                     font=ctk.CTkFont(size=17, weight="bold"),
                     text_color=TH).pack(pady=(18,8))

        ctk.CTkLabel(box, text="Benutzername",
                     font=ctk.CTkFont(size=11), text_color=TM).pack(padx=30, anchor="w")
        self.uv = ctk.StringVar(value="admin")
        ctk.CTkEntry(box, textvariable=self.uv,
                      width=350, height=36, fg_color=DUNKEL,
                      border_color=RAND, text_color=TH,
                      corner_radius=8).pack(padx=30, pady=(3,10))

        ctk.CTkLabel(box, text="Passwort",
                     font=ctk.CTkFont(size=11), text_color=TM).pack(padx=30, anchor="w")
        self.pv = ctk.StringVar(value="XsiKOM2026!")
        pe = ctk.CTkEntry(box, textvariable=self.pv,
                          width=350, height=36, show="*",
                          fg_color=DUNKEL, border_color=RAND,
                          text_color=TH, corner_radius=8)
        pe.pack(padx=30, pady=(3,12))
        pe.bind("<Return>", lambda e: self._login())

        mkbtn(box, "🔐 Anmelden", self._login, BB, h=40).pack(padx=30, pady=(0,8), fill="x")
        mkbtn(box, "➕ Neuen Benutzer registrieren", self._reg, SIDEBAR, h=35).pack(padx=30, pady=(0,15), fill="x")

        ctk.CTkLabel(self, text="Standard-Login: admin / XsiKOM2026!",
                     font=ctk.CTkFont(size=9), text_color=TD).pack(pady=8)

    def _login(self):
        u, pw = self.uv.get().strip(), self.pv.get().strip()
        if not u or not pw:
            messagebox.showwarning("Fehler", "Alle Felder ausfuellen!")
            return
        r = benutzer_pruefen(u, pw)
        if r:
            self.destroy()
            self.cb(r)
        else:
            messagebox.showerror("Fehler", "Login falsch!")

    def _reg(self):
        d = ctk.CTkToplevel(self)
        d.title("Registrieren")
        d.geometry("420x490")
        d.configure(fg_color=HG)
        d.grab_set()
        ctk.CTkLabel(d, text="Neuen Benutzer anlegen",
                     font=ctk.CTkFont(size=15, weight="bold"),
                     text_color=BLAU).pack(pady=15)
        f = {}
        for lbl, key, geh in [("Benutzername:","u",False),("Passwort:","pw",True),
                                ("Vorname:","vn",False),("Nachname:","nn",False),
                                ("E-Mail:","em",False)]:
            ctk.CTkLabel(d, text=lbl, font=ctk.CTkFont(size=10), text_color=TM).pack(padx=40, anchor="w")
            v = ctk.StringVar()
            ctk.CTkEntry(d, textvariable=v, width=340, height=34,
                          fg_color=DUNKEL, border_color=RAND,
                          text_color=TH, corner_radius=7,
                          show="*" if geh else "").pack(padx=40, pady=(2,7))
            f[key] = v

        def sp():
            u, pw = f["u"].get().strip(), f["pw"].get().strip()
            if not u or not pw:
                return messagebox.showwarning("Fehler", "User+Passwort!")
            if len(pw) < 6:
                return messagebox.showwarning("Fehler", "Min. 6 Zeichen!")
            if benutzer_anlegen(u, pw, f["em"].get().strip(),
                                f["vn"].get().strip(), f["nn"].get().strip()):
                messagebox.showinfo("Erfolg", f"'{u}' erstellt!")
                d.destroy()
            else:
                messagebox.showerror("Fehler", "Name vergeben!")

        mkbtn(d, "💾 Registrieren", sp, BG2, h=40).pack(pady=10, padx=40, fill="x")


class App(ctk.CTk):

    def __init__(self, user):
        ctk.CTk.__init__(self)
        self.user = user
        self.aaliyah = Aaliyah()
        self.title(f"XsiKOM-BewerbungsBOT - {user['vorname']} {user['nachname']}")
        self.geometry("1300x820")
        self.minsize(1050, 650)
        self.configure(fg_color=HG)
        self._layout()
        self.show_dashboard()

    def _thread(self, fn):
        threading.Thread(target=fn, daemon=True).start()

    def _status(self, text, farbe=GRUEN):
        self.st_dot.configure(text_color=farbe)
        self.st_lbl.configure(text=text)
        self.update()

    def _clear(self):
        for w in self.main.winfo_children():
            w.destroy()

    def _scroll(self):
        s = ctk.CTkScrollableFrame(self.main, fg_color=HG)
        s.pack(fill="both", expand=True, padx=16, pady=12)
        return s

    def _stats(self):
        try:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM stellen")
            st = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM bewerbungen")
            ge = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM bewerbungen WHERE status='gesendet'")
            gs = c.fetchone()[0]
            try:
                c.execute("SELECT COUNT(*) FROM tracker WHERE antwort_status != 'ausstehend'")
                aw = c.fetchone()[0]
                c.execute("SELECT COUNT(*) FROM tracker WHERE einladung=1")
                ei = c.fetchone()[0]
                c.execute("SELECT COUNT(*) FROM tracker WHERE absage=1")
                ab = c.fetchone()[0]
            except:
                aw = ei = ab = 0
            conn.close()
            return {"stellen":st,"gesamt":ge,"gesendet":gs,"antworten":aw,"einladungen":ei,"absagen":ab}
        except:
            return {"stellen":0,"gesamt":0,"gesendet":0,"antworten":0,"einladungen":0,"absagen":0}

    def _stellen(self):
        try:
            from database import stellen_laden
            return stellen_laden()
        except:
            return []

    def _bew(self, n=5):
        try:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute(f"SELECT * FROM bewerbungen ORDER BY id DESC LIMIT {n}")
            r = c.fetchall()
            conn.close()
            return r
        except:
            return []

    def _tracker(self):
        try:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT * FROM tracker ORDER BY id DESC")
            r = c.fetchall()
            conn.close()
            return r
        except:
            return []

    def _layout(self):
        sb = ctk.CTkFrame(self, width=240, fg_color=SIDEBAR, corner_radius=0)
        sb.pack(side="left", fill="y")
        sb.pack_propagate(False)

        lf = ctk.CTkFrame(sb, fg_color=GRAD, height=105, corner_radius=0)
        lf.pack(fill="x")
        lf.pack_propagate(False)
        ctk.CTkLabel(lf, text="XsiKOM", font=ctk.CTkFont(size=22, weight="bold"), text_color=BLAU).pack(pady=(15,0))
        ctk.CTkLabel(lf, text="BewerbungsBOT", font=ctk.CTkFont(size=11, weight="bold"), text_color=GRUEN).pack()
        ctk.CTkLabel(lf, text=f"👤 {self.user['vorname']} | {self.user['rolle'].upper()}",
                      font=ctk.CTkFont(size=9), text_color=TD).pack(pady=(2,8))

        ctk.CTkFrame(sb, fg_color=RAND, height=1).pack(fill="x", padx=12, pady=4)

        menu = [
            ("🏠  Dashboard", self.show_dashboard),
            ("🔍  Stellensuche", self.show_suche),
            ("📧  Bewerbungen", self.show_bewerbungen),
            ("📊  Tracker", self.show_tracker),
            ("📄  Lebenslauf", self.show_lebenslauf),
            ("🤖  Aaliyah KI", self.show_aaliyah),
            ("📈  Statistiken", self.show_statistiken),
            ("❓  Hilfe", self.show_hilfe),
        ]
        if self.user.get("rolle") == "admin":
            menu.append(("⚙️  Admin Panel", self.show_admin))
        menu.append(("🚪  Abmelden", self.abmelden))

        for text, cmd in menu:
            mkbtn(sb, text, cmd, SIDEBAR, h=36).pack(fill="x", padx=8, pady=1)

        ctk.CTkFrame(sb, fg_color="transparent").pack(fill="both", expand=True)
        ctk.CTkFrame(sb, fg_color=RAND, height=1).pack(fill="x", padx=12, pady=4)

        stb = ctk.CTkFrame(sb, fg_color=DUNKEL, corner_radius=8)
        stb.pack(fill="x", padx=10, pady=8)
        self.st_dot = ctk.CTkLabel(stb, text="●", font=ctk.CTkFont(size=11), text_color=GRUEN)
        self.st_dot.pack(side="left", padx=(8,4), pady=7)
        self.st_lbl = ctk.CTkLabel(stb, text="Bereit", font=ctk.CTkFont(size=10), text_color=TM)
        self.st_lbl.pack(side="left", pady=7)

        self.main = ctk.CTkFrame(self, fg_color=HG, corner_radius=0)
        self.main.pack(side="right", fill="both", expand=True)

    def show_dashboard(self):
        self._clear()
        mkheader(self.main, "🏠 Dashboard", f"Willkommen, {self.user['vorname']}!", BLAU)
        sc = self._scroll()

        stats = self._stats()
        sf = ctk.CTkFrame(sc, fg_color="transparent")
        sf.pack(fill="x", pady=(0,14))
        for i, (e,w,l,f) in enumerate([
            ("📋", stats["stellen"], "Stellen", BLAU),
            ("📧", stats["gesendet"], "Gesendet", GRUEN),
            ("💬", stats["antworten"], "Antworten", ORANGE),
            ("🎉", stats["einladungen"], "Einladungen", PINK),
        ]):
            k = mkstat(sf, e, w, l, f)
            k.grid(row=0, column=i, padx=6, sticky="ew")
            sf.grid_columnconfigure(i, weight=1)

        s, k = mkkarte(sc)
        s.pack(fill="x", pady=(0,12))
        ctk.CTkFrame(k, fg_color="#FF69B4", height=3, corner_radius=0).pack(fill="x", padx=8, pady=(8,4))
        ctk.CTkLabel(k, text="🤖 Aaliyah - Tipp des Tages",
                     font=ctk.CTkFont(size=11, weight="bold"), text_color="#FF69B4").pack(anchor="w", padx=12)
        ctk.CTkLabel(k, text=self.aaliyah.zufalls_tipp(),
                     font=ctk.CTkFont(size=11), text_color=TH,
                     wraplength=750).pack(anchor="w", padx=12, pady=(4,12))

        mklbl(sc, "⚡ SCHNELLAKTIONEN")
        af = ctk.CTkFrame(sc, fg_color="transparent")
        af.pack(fill="x", pady=(0,12))
        for i, (t,f,c) in enumerate([
            ("🔍 Stellen suchen", BB, self._do_suche),
            ("📧 Bewerbung senden", BG2, self.show_bewerbungen),
            ("🤖 Aaliyah fragen", "#C0578A", self.show_aaliyah),
            ("📄 Lebenslauf", BO, self.show_lebenslauf),
        ]):
            mkbtn(af, t, c, f).grid(row=0, column=i, padx=5, sticky="ew")
            af.grid_columnconfigure(i, weight=1)

    def show_suche(self):
        self._clear()
        mkheader(self.main, "🔍 Stellensuche", "8 Portale | 30 Staedte", GRUEN)
        sc = self._scroll()

        pf = ctk.CTkFrame(sc, fg_color="transparent")
        pf.pack(fill="x", pady=(0,12))
        for i, n in enumerate(["Indeed","StepStone","Monster","XING","LinkedIn","Glassdoor","Arbeitsagentur","Kimeta"]):
            s, k = mkkarte(pf, h=46)
            s.grid(row=i//4, column=i%4, padx=4, pady=4, sticky="ew")
            pf.grid_columnconfigure(i%4, weight=1)
            ctk.CTkLabel(k, text=f"✅  {n}", font=ctk.CTkFont(size=11), text_color=GRUEN).pack(pady=11)

        bf = ctk.CTkFrame(sc, fg_color="transparent")
        bf.pack(fill="x", pady=10)
        for i, (t,f,c) in enumerate([
            ("🔍 Alle Portale", BB, self._do_suche),
            ("🏢 IT-Firmen", BG2, self._do_firmen),
            ("🌐 Webseiten", BO, self._do_webseiten),
        ]):
            mkbtn(bf, t, c, f, h=44).grid(row=0, column=i, padx=5, sticky="ew")
            bf.grid_columnconfigure(i, weight=1)

    def show_bewerbungen(self):
        self._clear()
        mkheader(self.main, "📧 Bewerbungen", "Senden & Verwalten", ORANGE)
        sc = self._scroll()

        mklbl(sc, "📧 EINZELNE BEWERBUNG")
        fs, fk = mkkarte(sc)
        fs.pack(fill="x", pady=(0,12))

        ctk.CTkLabel(fk, text="Firma:", font=ctk.CTkFont(size=11), text_color=TM).grid(row=0, column=0, padx=12, pady=8, sticky="w")
        self.e_firma = mkentry(fk, 370, "Firmenname...")
        self.e_firma.grid(row=0, column=1, padx=12, pady=8)

        ctk.CTkLabel(fk, text="E-Mail:", font=ctk.CTkFont(size=11), text_color=TM).grid(row=1, column=0, padx=12, pady=8, sticky="w")
        self.e_email = mkentry(fk, 370, "bewerbung@firma.de")
        self.e_email.grid(row=1, column=1, padx=12, pady=8)

        ctk.CTkLabel(fk, text="Bereich:", font=ctk.CTkFont(size=11), text_color=TM).grid(row=2, column=0, padx=12, pady=8, sticky="w")
        self.e_bereich = ctk.StringVar(value="allgemein")
        ctk.CTkOptionMenu(fk, variable=self.e_bereich,
                          values=["allgemein","netzwerk","systemadmin","support"],
                          width=220, fg_color=BB, corner_radius=8).grid(row=2, column=1, padx=12, pady=8, sticky="w")

        bf = ctk.CTkFrame(fk, fg_color="transparent")
        bf.grid(row=3, column=0, columnspan=2, padx=12, pady=12, sticky="w")
        mkbtn(bf, "📄 Anschreiben", self._do_anschreiben, BO).pack(side="left", padx=4)
        mkbtn(bf, "📧 LIVE senden", lambda: self._do_senden(False), BG2).pack(side="left", padx=4)
        mkbtn(bf, "🔄 Trockenlauf", lambda: self._do_senden(True), BB).pack(side="left", padx=4)

        mklbl(sc, "📬 MASSENBEWERBUNG")
        ms, mk = mkkarte(sc)
        ms.pack(fill="x", pady=(0,12))
        stellen = self._stellen()
        mit_email = sum(1 for s in stellen if s[4])
        inf = ctk.CTkFrame(mk, fg_color="transparent")
        inf.pack(fill="x", padx=12, pady=10)
        for t,w,f in [("Stellen:", str(len(stellen)), TH),
                       ("Mit E-Mail:", str(mit_email), GRUEN),
                       ("Ohne:", str(len(stellen)-mit_email), ROT)]:
            ctk.CTkLabel(inf, text=f"{t} {w}", font=ctk.CTkFont(size=11), text_color=f).pack(side="left", padx=12)

        mbf = ctk.CTkFrame(mk, fg_color="transparent")
        mbf.pack(fill="x", padx=12, pady=(0,12))
        mkbtn(mbf, "🔄 Trockenlauf", lambda: self._do_masse(True), BB, h=42).pack(side="left", padx=4)
        mkbtn(mbf, "🚀 LIVE Senden!", lambda: self._do_masse(False), ROT, h=42).pack(side="left", padx=4)

    def show_tracker(self):
        self._clear()
        mkheader(self.main, "📊 Tracker", "Antworten & Status", PINK)
        sc = self._scroll()
        tracker = self._tracker()
        if not tracker:
            ctk.CTkLabel(sc, text="Noch keine Bewerbungen im Tracker.",
                          font=ctk.CTkFont(size=13), text_color=TD).pack(pady=40)
        else:
            for t in tracker:
                sf2 = GRUEN if t[6] else (ROT if t[7] else GELB)
                st = "🎉 EINLADUNG!" if t[6] else ("❌ Absage" if t[7] else "⏳ Ausstehend")
                s, k = mkkarte(sc, h=58)
                s.pack(fill="x", pady=3)
                ctk.CTkFrame(k, fg_color=sf2, width=4, corner_radius=2).pack(side="left", fill="y", padx=(8,10), pady=8)
                ctk.CTkLabel(k, text=str(t[1])[:25] if t[1] else "N/A",
                              font=ctk.CTkFont(size=12, weight="bold"),
                              text_color=TH, width=195, anchor="w").pack(side="left")
                ctk.CTkLabel(k, text=st, font=ctk.CTkFont(size=11, weight="bold"),
                              text_color=sf2, width=120, anchor="w").pack(side="left", padx=5)

    def show_lebenslauf(self):
        self._clear()
        mkheader(self.main, "📄 Lebenslauf-Editor", "Dein Profil", GELB)
        sc = self._scroll()

        profil = benutzer_daten_laden(self.user["benutzername"]) or standard_profil()

        fs, fk = mkkarte(sc)
        fs.pack(fill="x", pady=(0,12))
        ctk.CTkFrame(fk, fg_color=GELB, height=3, corner_radius=0).pack(fill="x", padx=8, pady=(8,4))
        ctk.CTkLabel(fk, text="👤 PERSOENLICHE DATEN",
                      font=ctk.CTkFont(size=11, weight="bold"), text_color=GELB).pack(anchor="w", padx=12)

        form = ctk.CTkFrame(fk, fg_color="transparent")
        form.pack(fill="x", padx=12, pady=(4,8))

        self.lv = {}
        for i, (label, key) in enumerate([("Vorname:","vorname"),("Nachname:","nachname"),
                                            ("Strasse:","strasse"),("PLZ:","plz"),
                                            ("Stadt:","stadt"),("Telefon:","telefon"),
                                            ("E-Mail:","email"),("Geburtsdatum:","geburtsdatum")]):
            r, c = i//2, (i%2)*2
            ctk.CTkLabel(form, text=label, font=ctk.CTkFont(size=10), text_color=TM).grid(row=r, column=c, padx=(8,4), pady=5, sticky="w")
            e = mkentry(form, 240)
            e.grid(row=r, column=c+1, padx=(0,12), pady=5)
            e.insert(0, profil.get(key, ""))
            self.lv[key] = e

        ctk.CTkLabel(fk, text="IT-Kenntnisse:", font=ctk.CTkFont(size=10), text_color=TM).pack(anchor="w", padx=12)
        self.lv_ken = ctk.CTkTextbox(fk, height=110, font=ctk.CTkFont(size=10),
                                       fg_color=DUNKEL, text_color=TH, corner_radius=7)
        self.lv_ken.pack(fill="x", padx=12, pady=4)
        self.lv_ken.insert("1.0", "\n".join(profil.get("kenntnisse", [])))

        ctk.CTkLabel(fk, text="Sprachen:", font=ctk.CTkFont(size=10), text_color=TM).pack(anchor="w", padx=12)
        self.lv_spr = ctk.CTkTextbox(fk, height=70, font=ctk.CTkFont(size=10),
                                       fg_color=DUNKEL, text_color=TH, corner_radius=7)
        self.lv_spr.pack(fill="x", padx=12, pady=(4,12))
        self.lv_spr.insert("1.0", "\n".join(profil.get("sprachen", [])))

        bbf = ctk.CTkFrame(sc, fg_color="transparent")
        bbf.pack(fill="x", pady=8)
        mkbtn(bbf, "💾 Speichern", self._do_lv_save, BG2, h=42).pack(side="left", padx=4)
        mkbtn(bbf, "📄 PDF erstellen", self._do_lv_pdf, BB, h=42).pack(side="left", padx=4)

    def show_aaliyah(self):
        self._clear()
        mkheader(self.main, "🤖 Aaliyah KI-Assistentin", "Deine Bewerbungsberaterin", "#FF69B4")

        mf = ctk.CTkFrame(self.main, fg_color=HG)
        mf.pack(fill="both", expand=True, padx=16, pady=12)

        cs, ck = mkkarte(mf)
        cs.pack(fill="both", expand=True, pady=(0,8))
        ctk.CTkFrame(ck, fg_color="#FF69B4", height=3, corner_radius=0).pack(fill="x", padx=8, pady=(8,4))
        ctk.CTkLabel(ck, text="💬 Chat mit Aaliyah",
                      font=ctk.CTkFont(size=12, weight="bold"),
                      text_color="#FF69B4").pack(anchor="w", padx=12)

        self.chat = ctk.CTkTextbox(ck, height=330, font=ctk.CTkFont(size=12),
                                     fg_color=DUNKEL, text_color=TH, corner_radius=8)
        self.chat.pack(fill="both", expand=True, padx=10, pady=8)
        self.chat.insert("end", f"🤖 Aaliyah: {self.aaliyah.begruessung()}\n\n")
        self.chat.insert("end", "💡 Probiere: 'tipps bewerbung' | 'lebenslauf' | 'gehalt'\n\n")

        inf = ctk.CTkFrame(mf, fg_color=KARTE, corner_radius=10, height=52)
        inf.pack(fill="x", pady=(0,8))
        inf.pack_propagate(False)

        self.aal_ent = ctk.CTkEntry(inf, height=34, placeholder_text="Frag Aaliyah...",
                                      fg_color=DUNKEL, border_color=RAND, text_color=TH,
                                      corner_radius=8, font=ctk.CTkFont(size=12))
        self.aal_ent.pack(side="left", fill="x", expand=True, padx=(12,8), pady=10)
        self.aal_ent.bind("<Return>", lambda e: self._aal_send())

        mkbtn(inf, "📤 Senden", self._aal_send, "#C0578A", w=110, h=34).pack(side="left", padx=(0,8), pady=10)
        mkbtn(inf, "🗑️ Leeren", self._aal_clear, BL, w=90, h=34).pack(side="left", padx=(0,12), pady=10)

        sf = ctk.CTkFrame(mf, fg_color="transparent")
        sf.pack(fill="x")
        for i, t in enumerate(["tipps bewerbung","lebenslauf","gespraech","gehalt","netzwerk","stress"]):
            mkbtn(sf, t, lambda q=t: self._aal_quick(q), KARTE, h=28).grid(row=0, column=i, padx=3, sticky="ew")
            sf.grid_columnconfigure(i, weight=1)

    def show_statistiken(self):
        self._clear()
        mkheader(self.main, "📈 Statistiken", "Auswertung", GELB)
        sc = self._scroll()

        stats = self._stats()
        sf = ctk.CTkFrame(sc, fg_color="transparent")
        sf.pack(fill="x", pady=(0,16))
        for i, (e,w,l,f) in enumerate([
            ("📋", stats["stellen"], "Stellen", BLAU),
            ("📧", stats["gesamt"], "Gesamt", GRUEN),
            ("✅", stats["gesendet"], "Gesendet", ORANGE),
            ("💬", stats["antworten"], "Antworten", GELB),
            ("🎉", stats["einladungen"], "Einladungen", PINK),
            ("❌", stats["absagen"], "Absagen", ROT),
        ]):
            k = mkstat(sf, e, w, l, f)
            k.grid(row=i//3, column=i%3, padx=7, pady=7, sticky="ew")
            sf.grid_columnconfigure(i%3, weight=1)

        bf = ctk.CTkFrame(sc, fg_color="transparent")
        bf.pack(fill="x", pady=8)
        mkbtn(bf, "📊 Charts", self._do_charts, BO, h=44).grid(row=0, column=0, padx=5, sticky="ew")
        mkbtn(bf, "📥 Excel", self._do_excel, BL, h=44).grid(row=0, column=1, padx=5, sticky="ew")
        bf.grid_columnconfigure(0, weight=1)
        bf.grid_columnconfigure(1, weight=1)

    def show_hilfe(self):
        self._clear()
        mkheader(self.main, "❓ Hilfe", "Anleitung", TM)
        sc = self._scroll()

        for titel, farbe, punkte in [
            ("🚀 ERSTE SCHRITTE", BLAU, ["1. Stellensuche", "2. IT-Firmen", "3. Pruefen", "4. Trockenlauf", "5. LIVE"]),
            ("🤖 AALIYAH", "#FF69B4", ["Deine KI-Beraterin!", "Frag nach Tipps!"]),
            ("📧 E-MAIL", GRUEN, ["Gmail App-Passwort", "In config.py eintragen"]),
            ("⚠️ FEHLER", ROT, ["App-Passwort pruefen", "PDFs neu erstellen"]),
        ]:
            s, k = mkkarte(sc)
            s.pack(fill="x", pady=6)
            ctk.CTkFrame(k, fg_color=farbe, height=3, corner_radius=0).pack(fill="x", padx=8, pady=(8,4))
            ctk.CTkLabel(k, text=titel, font=ctk.CTkFont(size=12, weight="bold"),
                          text_color=farbe).pack(anchor="w", padx=12)
            for p in punkte:
                ctk.CTkLabel(k, text=f"  • {p}", font=ctk.CTkFont(size=11),
                              text_color=TH, anchor="w").pack(anchor="w", padx=20, pady=1)
            ctk.CTkLabel(k, text="").pack()

    def show_admin(self):
        if self.user.get("rolle") != "admin":
            return messagebox.showerror("Fehler", "Nur Admins!")
        self._clear()
        mkheader(self.main, "⚙️ Admin Panel", "Benutzerverwaltung", ROT)
        sc = self._scroll()

        mklbl(sc, "👥 ALLE BENUTZER")
        for u in alle_benutzer_laden():
            rf = ROT if u[5] == "admin" else BLAU
            s, k = mkkarte(sc, h=52)
            s.pack(fill="x", pady=2)
            ctk.CTkFrame(k, fg_color=rf, width=4, corner_radius=2).pack(side="left", fill="y", padx=(8,10), pady=8)
            ctk.CTkLabel(k, text=f"{u[1]} - {u[3]} {u[4]}",
                          font=ctk.CTkFont(size=11, weight="bold"),
                          text_color=TH, width=225, anchor="w").pack(side="left")
            ctk.CTkLabel(k, text=u[5].upper(), font=ctk.CTkFont(size=9, weight="bold"),
                          text_color=rf, width=70).pack(side="left")

    def _do_suche(self):
        def fn():
            self._status("Suche...", GELB)
            try:
                from job_suche import vollsuche_starten
                vollsuche_starten()
                self._status("Fertig!", GRUEN)
                messagebox.showinfo("Fertig", "Suche fertig!")
            except Exception as e:
                self._status("Fehler!", ROT)
                messagebox.showerror("Fehler", str(e))
        self._thread(fn)

    def _do_firmen(self):
        def fn():
            try:
                from job_suche import it_firmen_hinzufuegen
                n = it_firmen_hinzufuegen()
                messagebox.showinfo("Fertig", f"{n} Firmen hinzugefuegt!")
            except Exception as e:
                messagebox.showerror("Fehler", str(e))
        self._thread(fn)

    def _do_webseiten(self):
        def fn():
            try:
                from firmen_suche import alle_firmen_durchsuchen
                alle_firmen_durchsuchen()
                messagebox.showinfo("Fertig", "Webseiten durchsucht!")
            except Exception as e:
                messagebox.showerror("Fehler", str(e))
        self._thread(fn)

    def _do_anschreiben(self):
        firma = self.e_firma.get().strip()
        if not firma:
            return messagebox.showwarning("Fehler", "Firma eingeben!")
        def fn():
            try:
                from anschreiben_generator import anschreiben_erstellen
                pfad = anschreiben_erstellen(firma=firma, bereich=self.e_bereich.get())
                os.startfile(pfad)
            except Exception as e:
                messagebox.showerror("Fehler", str(e))
        self._thread(fn)

    def _do_senden(self, trockenlauf=False):
        firma = self.e_firma.get().strip()
        email = self.e_email.get().strip()
        if not firma or not email:
            return messagebox.showwarning("Fehler", "Firma+E-Mail!")
        if not trockenlauf and not messagebox.askyesno("Senden?", f"An {firma}?"):
            return
        def fn():
            try:
                from anschreiben_generator import anschreiben_erstellen
                from email_sender import bewerbung_senden
                pfad = anschreiben_erstellen(firma=firma, bereich=self.e_bereich.get())
                r = bewerbung_senden(empfaenger=email, firma=firma,
                                      position="IT-Fachtechniker / Netzwerktechniker",
                                      anschreiben_pfad=pfad, trockenlauf=trockenlauf)
                if r:
                    messagebox.showinfo("OK", "Gesendet!")
            except Exception as e:
                messagebox.showerror("Fehler", str(e))
        self._thread(fn)

    def _do_masse(self, trockenlauf=True):
        if not trockenlauf and not messagebox.askyesno("ACHTUNG!", "Echte E-Mails?"):
            return
        def fn():
            try:
                from database import stellen_laden
                from anschreiben_generator import anschreiben_erstellen
                from email_sender import bewerbung_senden
                import time
                stellen = stellen_laden()
                me = [s for s in stellen if s[4]]
                ok = 0
                for s in me:
                    f = s[2] if s[2] else "Unbekannt"
                    e = s[4]
                    try:
                        p = anschreiben_erstellen(firma=f, bereich="allgemein")
                    except:
                        p = None
                    r = bewerbung_senden(empfaenger=e, firma=f,
                                          position="IT-Fachtechniker / Netzwerktechniker",
                                          anschreiben_pfad=p, trockenlauf=trockenlauf)
                    if r: ok += 1
                    if not trockenlauf: time.sleep(30)
                messagebox.showinfo("Fertig", f"{ok} verarbeitet!")
            except Exception as e:
                messagebox.showerror("Fehler", str(e))
        self._thread(fn)

    def _do_lv_save(self):
        profil = {k: e.get().strip() for k, e in self.lv.items()}
        profil["kenntnisse"] = [z.strip() for z in self.lv_ken.get("1.0","end").strip().split("\n") if z.strip()]
        profil["sprachen"] = [z.strip() for z in self.lv_spr.get("1.0","end").strip().split("\n") if z.strip()]
        profil["berufserfahrung"] = []
        profil["zertifikate"] = []
        benutzer_daten_speichern(self.user["benutzername"], profil)
        messagebox.showinfo("OK", "Gespeichert!")

    def _do_lv_pdf(self):
        self._do_lv_save()
        p = benutzer_daten_laden(self.user["benutzername"])
        if p:
            pfad = lebenslauf_aus_profil(p)
            os.startfile(pfad)

    def _aal_send(self):
        f = self.aal_ent.get().strip()
        if not f: return
        self.chat.insert("end", f"👤 Du: {f}\n")
        self.aal_ent.delete(0, "end")
        a = self.aaliyah.antwort(f)
        self.chat.insert("end", f"\n🤖 Aaliyah: {a}\n\n")
        self.chat.see("end")

    def _aal_quick(self, f):
        self.aal_ent.delete(0, "end")
        self.aal_ent.insert(0, f)
        self._aal_send()

    def _aal_clear(self):
        self.chat.delete("1.0", "end")
        self.aaliyah.verlauf_leeren()
        self.chat.insert("end", f"🤖 Aaliyah: {self.aaliyah.begruessung()}\n\n")

    def _do_charts(self):
        def fn():
            try:
                from charts import charts_erstellen
                charts_erstellen()
                messagebox.showinfo("OK", "Charts erstellt!")
            except Exception as e:
                messagebox.showerror("Fehler", str(e))
        self._thread(fn)

    def _do_excel(self):
        def fn():
            try:
                from excel_export import excel_export
                excel_export()
                messagebox.showinfo("OK", "Excel erstellt!")
            except Exception as e:
                messagebox.showerror("Fehler", str(e))
        self._thread(fn)

    def abmelden(self):
        if messagebox.askyesno("Abmelden?", "Wirklich?"):
            self.destroy()
            starten()


def starten():
    user_db_erstellen()
    admin_erstellen()
    def cb(u):
        a = App(u)
        a.mainloop()
    Login(cb).mainloop()


if __name__ == "__main__":
    starten()