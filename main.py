import tkinter as tk
import db
import gui


def main():
    # 1. Initialize SQLite database schema
    db.init_db()

    # 2. Create Tkinter root window
    root = tk.Tk()

    # 3. Initialize GUI application
    gui.PasswordManagerApp(root)

    # 4. Start main event loop
    root.mainloop()


if __name__ == "__main__":
    main()
