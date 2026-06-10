print("Schritt 1: Imports...")

try:
    import customtkinter as ctk
    print("  customtkinter OK")
except Exception as e:
    print(f"  FEHLER customtkinter: {e}")

try:
    from user_manager import user_db_erstellen, admin_erstellen, benutzer_pruefen, benutzer_anlegen, alle_benutzer_laden, benutzer_loeschen
    print("  user_manager OK")
except Exception as e:
    print(f"  FEHLER user_manager: {e}")

try:
    from aaliyah_ki import Aaliyah
    print("  aaliyah_ki OK")
except Exception as e:
    print(f"  FEHLER aaliyah_ki: {e}")

try:
    from lebenslauf_editor import standard_profil, benutzer_daten_speichern, benutzer_daten_laden, lebenslauf_aus_profil
    print("  lebenslauf_editor OK")
except Exception as e:
    print(f"  FEHLER lebenslauf_editor: {e}")

print("\nSchritt 2: Datenbank...")
try:
    from user_manager import user_db_erstellen, admin_erstellen
    user_db_erstellen()
    admin_erstellen()
    print("  Datenbank OK")
except Exception as e:
    print(f"  FEHLER Datenbank: {e}")

print("\nSchritt 3: Login Fenster...")
try:
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    def nach_login(user):
        print(f"  Login OK: {user}")

    from app import Login
    print("  Login Klasse geladen")
    login = Login(nach_login)
    print("  Login Fenster erstellt")
    login.mainloop()
except Exception as e:
    print(f"  FEHLER Login: {e}")
    import traceback
    traceback.print_exc()