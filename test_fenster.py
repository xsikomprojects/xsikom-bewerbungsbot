import customtkinter as ctk

app = ctk.CTk()
app.title("Test")
app.geometry("400x300")
app.configure(fg_color="#0F1923")

import customtkinter as ctk
label = ctk.CTkLabel(app, text="Test funktioniert!", font=ctk.CTkFont(size=20))
label.pack(pady=50)

print("Fenster wird geöffnet...")
app.mainloop()
print("Fenster geschlossen.")