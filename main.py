import sys


class _NullStream:
    """Fallback stream for PyInstaller windowed builds where stdout/stderr are None."""

    encoding = "utf-8"

    def write(self, data):
        return len(data) if data else 0

    def flush(self):
        pass

    def isatty(self):
        return False


if sys.stdout is None:
    sys.stdout = _NullStream()
if sys.stderr is None:
    sys.stderr = _NullStream()

import customtkinter as ctk
import db
import gui


def main():
    # 1. Resolve persistent %LOCALAPPDATA%\ONESIUM database & safely migrate legacy vault
    db_status = db.prepare_database()

    # 2. Initialize SQLite database schema if missing (non-destructive)
    db.init_db()

    startup_notice = ""
    startup_notice_is_success = False
    if db_status.get("action") == "migrated":
        startup_notice = "Existing vault safely adopted into Local AppData storage."
        startup_notice_is_success = True
    elif db_status.get("action") == "both_exist_preserved":
        startup_notice = "Using Local AppData vault; legacy password_manager.db kept untouched."
        startup_notice_is_success = True

    # 3. Configure CustomTkinter appearance (must precede CTk() creation)
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    # 4. Create CustomTkinter root window
    root = ctk.CTk()

    # 5. Initialize GUI application
    gui.PasswordManagerApp(
        root,
        startup_notice=startup_notice,
        startup_notice_is_success=startup_notice_is_success,
    )

    # 6. Start main event loop
    root.mainloop()


if __name__ == "__main__":
    main()
