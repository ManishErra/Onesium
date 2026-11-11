import customtkinter as ctk
import db
import gui


def main():
    # 1. Initialize SQLite database schema
    db.init_db()

    # 2. Configure CustomTkinter appearance (must precede CTk() creation)
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    # 3. Create CustomTkinter root window
    root = ctk.CTk()

    # 4. Initialize GUI application
    gui.PasswordManagerApp(root)

    # 5. Start main event loop
    root.mainloop()


if __name__ == "__main__":
    main()
