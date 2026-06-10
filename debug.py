import traceback
import sys

print("=" * 60)
print("DEBUG START")
print("=" * 60)

try:
    print("\n1. Imports...")
    import customtkinter as ctk
    print("   customtkinter OK")

    from user_manager import user_db_erstellen, admin_erstellen
    print("   user_manager OK")

    from aaliyah_ki import Aaliyah
    print("   aaliyah_ki OK")

    from lebenslauf_editor import standard_profil
    print("   lebenslauf_editor OK")

    print("\n2. Datenbank...")
    user_db_erstellen()
    admin_erstellen()
    print("   Datenbank OK")

    print("\n3. App importieren...")
    from app import Login, App
    print("   App Module OK")

    print("\n4. Login Fenster starten...")
    def cb(user):
        print(f"\n5. Login erfolgreich: {user}")
        print("\n6. Hauptapp starten...")
        try:
            app = App(user)
            print("   App erstellt")
            app.mainloop()
            print("   App beendet")
        except Exception as e:
            print(f"\n  FEHLER in App: {e}")
            traceback.print_exc()
            input("\n  Enter zum Beenden...")

    login = Login(cb)
    print("   Login erstellt - öffne Fenster...")
    login.mainloop()
    print("\n7. Programm beendet")

except Exception as e:
    print(f"\nFEHLER: {e}")
    print("\nTRACEBACK:")
    traceback.print_exc()
    print("\n" + "=" * 60)
    input("Enter zum Beenden...")