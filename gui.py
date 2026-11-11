import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, font as tkfont
from datetime import datetime
import auth
import vault
import password_utils

# Configure CustomTkinter appearance (must precede any CTk widget creation)
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

AUTO_LOCK_MS = 5 * 60 * 1000  # 5 minutes in milliseconds

# ---------------------------------------------------------------------------
# Onesium Design System — Precision Vault Palette
# ---------------------------------------------------------------------------
COLOR_BG = "#0B0F17"               # Deep canvas background
COLOR_SURFACE = "#121926"          # Cards, modal dialogs, panels, sidebar
COLOR_SURFACE_ELEVATED = "#192333" # Elevated surface, table headers, active items
COLOR_INPUT = "#0F1724"            # Input field background
COLOR_BORDER = "#273449"           # 1px structural boundaries & outlines
COLOR_PRIMARY = "#3B82F6"          # Primary blue interactive buttons
COLOR_PRIMARY_HOVER = "#2563EB"    # Primary button hover
COLOR_PRIMARY_ACTIVE = "#1E40AF"   # Primary button active
COLOR_ACCENT = "#3B82F6"           # Bright focus accent ring
COLOR_TEXT_PRIMARY = "#F8FAFC"     # High contrast primary text
COLOR_TEXT_SECONDARY = "#94A3B8"   # Secondary field labels & captions
COLOR_TEXT_MUTED = "#64748B"       # Placeholders, status, timestamps
COLOR_TEXT_DIM = "#64748B"         # Dim text alias
COLOR_SUCCESS = "#10B981"          # Green for cryptographic strength & offline status
COLOR_WARNING = "#F59E0B"          # Yellow for moderate strength
COLOR_DANGER = "#EF4444"           # Red for errors & common password warnings

FONT_FAMILY = "Segoe UI"
FONT_MONO = "Consolas"

# Strength → colour map (used in registration feedback)
_STRENGTH_COLORS = {
    "Very Weak":  COLOR_DANGER,
    "Weak":       COLOR_WARNING,
    "Moderate":   COLOR_WARNING,
    "Strong":     COLOR_SUCCESS,
    "Very Strong": COLOR_SUCCESS,
}


def apply_vault_theme(root):
    """Configures modern dark ttk styles for the Onesium desktop interface."""
    # CTk root uses fg_color; plain Tk root uses bg
    try:
        root.configure(fg_color=COLOR_BG)
    except Exception:
        try:
            root.configure(bg=COLOR_BG)
        except Exception:
            pass

    style = ttk.Style()
    try:
        style.theme_use("clam")
    except Exception:
        pass

    # Baseline defaults
    style.configure(".", background=COLOR_BG, foreground=COLOR_TEXT_PRIMARY, font=(FONT_FAMILY, 9))

    # Frames
    style.configure("TFrame", background=COLOR_BG)
    style.configure("Card.TFrame", background=COLOR_SURFACE)
    style.configure("Elevated.TFrame", background=COLOR_SURFACE_ELEVATED)

    # Labels
    style.configure("TLabel", background=COLOR_BG, foreground=COLOR_TEXT_PRIMARY)
    style.configure("Card.TLabel", background=COLOR_SURFACE, foreground=COLOR_TEXT_PRIMARY)
    style.configure("Muted.TLabel", background=COLOR_BG, foreground=COLOR_TEXT_SECONDARY, font=(FONT_FAMILY, 9))
    style.configure("CardMuted.TLabel", background=COLOR_SURFACE, foreground=COLOR_TEXT_SECONDARY, font=(FONT_FAMILY, 9))
    style.configure("Dim.TLabel", background=COLOR_BG, foreground=COLOR_TEXT_MUTED, font=(FONT_FAMILY, 8))

    # Input Entry Fields
    style.configure(
        "TEntry",
        fieldbackground=COLOR_INPUT,
        foreground=COLOR_TEXT_PRIMARY,
        insertcolor=COLOR_TEXT_PRIMARY,
        bordercolor=COLOR_BORDER,
        lightcolor=COLOR_BORDER,
        darkcolor=COLOR_BORDER,
        padding=6,
    )
    style.map(
        "TEntry",
        bordercolor=[("focus", COLOR_ACCENT), ("!focus", COLOR_BORDER)],
        lightcolor=[("focus", COLOR_ACCENT), ("!focus", COLOR_BORDER)],
        darkcolor=[("focus", COLOR_ACCENT), ("!focus", COLOR_BORDER)],
    )

    # Buttons
    style.configure(
        "TButton",
        background=COLOR_SURFACE_ELEVATED,
        foreground=COLOR_TEXT_PRIMARY,
        borderwidth=1,
        bordercolor=COLOR_BORDER,
        focuscolor="none",
        padding=(10, 5),
        font=(FONT_FAMILY, 9),
    )
    style.map(
        "TButton",
        background=[("active", "#2A344A"), ("pressed", COLOR_SURFACE), ("disabled", COLOR_SURFACE)],
        foreground=[("disabled", COLOR_TEXT_DIM)],
        bordercolor=[("active", COLOR_ACCENT), ("disabled", COLOR_BORDER)],
    )

    style.configure(
        "Primary.TButton",
        background=COLOR_PRIMARY,
        foreground="#FFFFFF",
        font=(FONT_FAMILY, 9, "bold"),
        borderwidth=1,
        bordercolor=COLOR_PRIMARY,
        focuscolor="none",
        padding=(12, 6),
    )
    style.map(
        "Primary.TButton",
        background=[("active", COLOR_PRIMARY_HOVER), ("pressed", COLOR_PRIMARY_ACTIVE), ("disabled", COLOR_BORDER)],
        foreground=[("disabled", COLOR_TEXT_DIM)],
        bordercolor=[("active", COLOR_ACCENT), ("disabled", COLOR_BORDER)],
    )

    style.configure(
        "Sidebar.TButton",
        background=COLOR_SURFACE,
        foreground=COLOR_TEXT_MUTED,
        borderwidth=0,
        focuscolor="none",
        anchor="w",
        padding=(12, 8),
        font=(FONT_FAMILY, 9),
    )
    style.map(
        "Sidebar.TButton",
        background=[("active", COLOR_SURFACE_ELEVATED), ("pressed", COLOR_SURFACE_ELEVATED)],
        foreground=[("active", COLOR_TEXT_PRIMARY)],
    )

    style.configure(
        "SidebarActive.TButton",
        background=COLOR_SURFACE_ELEVATED,
        foreground=COLOR_TEXT_PRIMARY,
        borderwidth=1,
        bordercolor=COLOR_BORDER,
        focuscolor="none",
        anchor="w",
        padding=(12, 8),
        font=(FONT_FAMILY, 9, "bold"),
    )

    # Treeview Credential Table
    style.configure(
        "Treeview",
        background=COLOR_SURFACE,
        foreground=COLOR_TEXT_PRIMARY,
        fieldbackground=COLOR_SURFACE,
        rowheight=32,
        borderwidth=0,
        font=(FONT_FAMILY, 9),
    )
    style.map(
        "Treeview",
        background=[("selected", COLOR_PRIMARY)],
        foreground=[("selected", "#FFFFFF")],
    )
    style.configure(
        "Treeview.Heading",
        background=COLOR_SURFACE_ELEVATED,
        foreground=COLOR_TEXT_PRIMARY,
        font=(FONT_FAMILY, 9, "bold"),
        borderwidth=1,
        bordercolor=COLOR_BORDER,
        padding=(8, 6),
    )
    style.map("Treeview.Heading", background=[("active", "#2A344A")])

    # Scrollbar
    style.configure(
        "Vertical.TScrollbar",
        background=COLOR_SURFACE_ELEVATED,
        troughcolor=COLOR_SURFACE,
        bordercolor=COLOR_BORDER,
        arrowcolor=COLOR_TEXT_MUTED,
        width=10,
    )


def center_window(window, width, height, parent=None):
    """Centers a window on screen or relative to its parent window."""
    window.update_idletasks()
    if parent and parent.winfo_exists():
        x = parent.winfo_x() + (parent.winfo_width() - width) // 2
        y = parent.winfo_y() + (parent.winfo_height() - height) // 2
    else:
        x = (window.winfo_screenwidth() - width) // 2
        y = (window.winfo_screenheight() - height) // 2
    window.geometry(f"{width}x{height}+{max(0, x)}+{max(0, y)}")


# ---------------------------------------------------------------------------
# Icon & Formatting Helpers (zero external dependencies)
# ---------------------------------------------------------------------------
_FLUENT_ICONS = {
    "shield": "\uEA18",
    "shield_check": "\uE83D",
    "vault": "\uE72E",
    "key": "\uE8D7",
    "upload": "\uE898",
    "download": "\uE896",
    "logout": "\uF3B1",
    "search": "\uE721",
    "clear": "\uE711",
    "add": "\uE710",
    "globe": "\uE774",
    "chevron": "\uE76C",
    "user": "\uE77B",
}

_UNICODE_FALLBACK_ICONS = {
    "shield": "\U0001f6e1",
    "shield_check": "\U0001f6e1",
    "vault": "\U0001f512",
    "key": "\U0001f511",
    "upload": "\u2191",
    "download": "\u2193",
    "logout": "\u21AA",
    "search": "\U0001f50d",
    "clear": "\u2715",
    "add": "+",
    "globe": "\U0001f310",
    "chevron": "\u203A",
    "user": "\U0001f464",
}


def _resolve_icon_font():
    """Returns crisp Windows vector icon font if available, else None."""
    try:
        families = set(tkfont.families())
        if "Segoe Fluent Icons" in families:
            return "Segoe Fluent Icons"
        if "Segoe MDL2 Assets" in families:
            return "Segoe MDL2 Assets"
    except Exception:
        pass
    return None


def _format_updated_date(timestamp_str):
    """Formats an ISO/SQLite timestamp cleanly for subtle row display."""
    if not timestamp_str:
        return ""
    raw = str(timestamp_str).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(raw[:19], fmt)
            return dt.strftime("%b %d, %Y")
        except ValueError:
            continue
    return raw[:16]


def _truncate_text(text, max_len):
    """Truncates overly long display strings cleanly without altering underlying data."""
    if not text:
        return ""
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "\u2026"


class _ToolTip:
    """Lightweight dark-themed hover tooltip that cleans up safely on destroy."""

    def __init__(self, widget, text, delay_ms=350):
        self.widget = widget
        self.text = text
        self.delay_ms = delay_ms
        self._after_id = None
        self._tip_window = None

        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")
        widget.bind("<Destroy>", self._hide, add="+")

    def _schedule(self, event=None):
        self._cancel()
        if not self.text:
            return
        try:
            self._after_id = self.widget.after(self.delay_ms, self._show)
        except tk.TclError:
            pass

    def _cancel(self):
        if self._after_id is not None:
            try:
                self.widget.after_cancel(self._after_id)
            except tk.TclError:
                pass
            self._after_id = None

    def _show(self):
        self._after_id = None
        try:
            if not self.widget.winfo_exists():
                return
            x = self.widget.winfo_rootx() + 10
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        except tk.TclError:
            return

        self._hide()
        tip = tk.Toplevel(self.widget)
        tip.wm_overrideredirect(True)
        tip.attributes("-topmost", True)
        tip.configure(bg=COLOR_BORDER)

        inner = tk.Label(
            tip,
            text=self.text,
            bg=COLOR_SURFACE_ELEVATED,
            fg=COLOR_TEXT_PRIMARY,
            font=(FONT_FAMILY, 9),
            padx=8,
            pady=4,
        )
        inner.pack(padx=1, pady=1)

        tip.update_idletasks()
        screen_w = tip.winfo_screenwidth()
        screen_h = tip.winfo_screenheight()
        tw = tip.winfo_reqwidth()
        th = tip.winfo_reqheight()
        if x + tw > screen_w - 8:
            x = max(8, screen_w - tw - 8)
        if y + th > screen_h - 8:
            y = max(8, self.widget.winfo_rooty() - th - 6)
        tip.wm_geometry(f"+{x}+{y}")
        self._tip_window = tip

    def _hide(self, event=None):
        self._cancel()
        if self._tip_window is not None:
            try:
                self._tip_window.destroy()
            except tk.TclError:
                pass
            self._tip_window = None


class PasswordManagerApp:
    """
    GUI Presentation Layer for ONESIUM — The Credential Vault.
    Manages view transitions, vault dashboard, credential operations, and in-memory session credentials.
    """

    def __init__(self, root):
        self.root = root
        self.root.title("Onesium — The Credential Vault")
        self.root.geometry("460x560")
        self.root.minsize(420, 480)
        self.root.resizable(False, False)
        self._window_resizable = (False, False)

        apply_vault_theme(self.root)
        self._icon_font = _resolve_icon_font()

        # In-memory session state (cleared on logout / auto-lock)
        self.current_user_id = None
        self.current_encryption_key = None
        self.current_username = None
        self.selected_entry_id = None
        self.active_dialog = None
        self.auto_lock_job = None

        # Dashboard view state (never stores plaintext passwords)
        self.row_widgets = {}
        self.displayed_entries = []
        self._total_credential_count = 0
        self._last_search_query = ""
        self._list_canvas = None
        self._list_canvas_window = None

        # Bind user activity to reset auto-lock timer & single global wheel handler
        self.root.bind_all("<Key>", self.reset_auto_lock_timer)
        self.root.bind_all("<Button>", self.reset_auto_lock_timer)
        self.root.bind_all("<MouseWheel>", self._on_dashboard_mousewheel)

        # Container frame for switching views (CTkFrame replaces ttk.Frame)
        self.container = ctk.CTkFrame(self.root, corner_radius=0, fg_color=COLOR_BG)
        self.container.pack(fill="both", expand=True)

        # Centre window on screen before showing first view
        center_window(self.root, 460, 560)

        self.show_login_screen()

    def _icon_glyph(self, name):
        """Returns icon glyph matching the resolved icon font."""
        table = _FLUENT_ICONS if self._icon_font else _UNICODE_FALLBACK_ICONS
        return table.get(name, "")

    def _icon_font_tuple(self, size=14):
        """Returns font tuple for rendering icons cleanly."""
        return (self._icon_font or FONT_FAMILY, size)

    def _on_dashboard_mousewheel(self, event):
        """Routes mouse-wheel scrolling solely to the active credential list viewport."""
        if self.current_user_id is None:
            return
        canvas = self._list_canvas
        if canvas is None:
            return
        try:
            if not canvas.winfo_exists() or not canvas.winfo_ismapped():
                return
            cx = canvas.winfo_rootx()
            cy = canvas.winfo_rooty()
            cw = canvas.winfo_width()
            ch = canvas.winfo_height()
            if not (cx <= event.x_root <= cx + cw and cy <= event.y_root <= cy + ch):
                return
            if canvas.yview() != (0.0, 1.0):
                step = -1 if event.delta > 0 else 1
                canvas.yview_scroll(step * 2, "units")
        except tk.TclError:
            pass

    def clear_container(self):
        """Moves focus off about-to-be-destroyed child widgets and clears the container."""
        try:
            focused = self.root.focus_get()
            if focused is not None and focused is not self.root:
                self.root.focus_set()
        except (tk.TclError, KeyError):
            try:
                self.root.focus_set()
            except tk.TclError:
                pass
        self.row_widgets = {}
        self._list_canvas = None
        self._list_canvas_window = None
        for widget in self.container.winfo_children():
            widget.destroy()

    def _set_window_resizable(self, width, height):
        """Updates root resizable state only when changed to avoid CTk focus/withdraw churn."""
        target = (bool(width), bool(height))
        if self._window_resizable != target:
            self.root.resizable(*target)
            self._window_resizable = target

    def _toggle_show(self, entry, btn):
        """Toggles password masking for plain tk/ttk Entry widgets (dashboard dialogs)."""
        if entry.cget("show") == "*":
            entry.config(show="")
            btn.config(text="Hide")
        else:
            entry.config(show="*")
            btn.config(text="Show")

    # ----------------------------------------------------------------------
    # 1. Login Screen  (CustomTkinter)
    # ----------------------------------------------------------------------
    def show_login_screen(self, initial_message="", is_success=False):
        was_wide = self.root.winfo_width() > 550
        self.clear_container()
        self.root.minsize(420, 500)
        self.root.geometry("460x560")
        self._set_window_resizable(False, False)
        if was_wide:
            center_window(self.root, 460, 560)

        # Outer padding wrapper
        outer = ctk.CTkFrame(self.container, fg_color=COLOR_BG, corner_radius=0)
        outer.pack(fill="both", expand=True, padx=28, pady=20)

        # ---- Branding Header ----
        brand_frame = ctk.CTkFrame(outer, fg_color=COLOR_BG, corner_radius=0)
        brand_frame.pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(
            brand_frame,
            text="\U0001f6e1  ONESIUM",
            font=(FONT_FAMILY, 22, "bold"),
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(pady=(0, 3))

        ctk.CTkLabel(
            brand_frame,
            text="The Credential Vault",
            font=(FONT_FAMILY, 11),
            text_color=COLOR_TEXT_MUTED,
        ).pack(pady=(0, 8))

        ctk.CTkLabel(
            brand_frame,
            text="  \u25cf  Offline  \u2022  Private  \u2022  Local  ",
            font=(FONT_FAMILY, 9, "bold"),
            text_color=COLOR_SUCCESS,
            fg_color=COLOR_SURFACE,
            corner_radius=4,
        ).pack(pady=(0, 0))

        # ---- Form Card ----
        card = ctk.CTkFrame(
            outer,
            fg_color=COLOR_SURFACE,
            corner_radius=12,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        card.pack(fill="x", pady=(14, 10))

        # Card inner content (padded nested frame)
        ci = ctk.CTkFrame(card, fg_color="transparent", corner_radius=0)
        ci.pack(fill="both", expand=True, padx=20, pady=16)

        ctk.CTkLabel(
            ci, text="Welcome back",
            font=(FONT_FAMILY, 13, "bold"),
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(anchor="w", pady=(0, 2))

        ctk.CTkLabel(
            ci, text="Your vault is stored locally on this device.",
            font=(FONT_FAMILY, 10),
            text_color=COLOR_TEXT_SECONDARY,
        ).pack(anchor="w", pady=(0, 14))

        # Username field
        ctk.CTkLabel(
            ci, text="Username",
            font=(FONT_FAMILY, 10, "bold"),
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(anchor="w", pady=(0, 4))

        self.login_username_entry = ctk.CTkEntry(
            ci,
            height=38,
            corner_radius=8,
            fg_color=COLOR_INPUT,
            border_color=COLOR_BORDER,
            text_color=COLOR_TEXT_PRIMARY,
            placeholder_text="Enter your username",
            placeholder_text_color=COLOR_TEXT_MUTED,
        )
        self.login_username_entry.pack(fill="x", pady=(0, 12))
        self.login_username_entry.focus()

        # Master Password — label row with Show/Hide toggle
        pwd_label_row = ctk.CTkFrame(ci, fg_color="transparent", corner_radius=0)
        pwd_label_row.pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(
            pwd_label_row, text="Master Password",
            font=(FONT_FAMILY, 10, "bold"),
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(side="left")

        # Closure-based show/hide state (avoids cget("show") inconsistencies)
        _pw_shown = [False]

        def _toggle_login_pw():
            if _pw_shown[0]:
                self.login_password_entry.configure(show="*")
                _login_eye.configure(text="Show")
                _pw_shown[0] = False
            else:
                self.login_password_entry.configure(show="")
                _login_eye.configure(text="Hide")
                _pw_shown[0] = True

        _login_eye = ctk.CTkButton(
            pwd_label_row,
            text="Show",
            width=52, height=24,
            corner_radius=4,
            fg_color=COLOR_SURFACE_ELEVATED,
            hover_color=COLOR_BORDER,
            text_color=COLOR_TEXT_MUTED,
            font=(FONT_FAMILY, 9),
            command=_toggle_login_pw,
        )
        _login_eye.pack(side="right")

        self.login_password_entry = ctk.CTkEntry(
            ci,
            height=38,
            corner_radius=8,
            fg_color=COLOR_INPUT,
            border_color=COLOR_BORDER,
            text_color=COLOR_TEXT_PRIMARY,
            placeholder_text="Enter your master password",
            placeholder_text_color=COLOR_TEXT_MUTED,
        )
        self.login_password_entry.pack(fill="x", pady=(0, 12))
        # Explicitly configure show="*" after pack to work around a CTk 6.x
        # issue where the show parameter is not reliably applied on widget rebuild.
        self.login_password_entry.configure(show="*")
        # CTkEntry proxies bind() to its internal tk.Entry — <Return> fires correctly
        self.login_password_entry.bind("<Return>", lambda e: self.handle_login())

        # Status / error message label
        status_color = COLOR_SUCCESS if is_success else COLOR_DANGER
        self.login_status_label = ctk.CTkLabel(
            ci,
            text=initial_message,
            text_color=status_color if initial_message else COLOR_DANGER,
            font=(FONT_FAMILY, 9),
            wraplength=360,
        )
        self.login_status_label.pack(pady=(0, 8))

        # Unlock Vault — primary action button
        ctk.CTkButton(
            ci,
            text="Unlock Vault",
            height=42,
            corner_radius=8,
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            text_color="#FFFFFF",
            font=(FONT_FAMILY, 11, "bold"),
            command=self.handle_login,
        ).pack(fill="x", pady=(0, 4))

        # ---- Create Account link ----
        switch_frame = ctk.CTkFrame(outer, fg_color=COLOR_BG, corner_radius=0)
        switch_frame.pack(pady=(8, 0))

        ctk.CTkLabel(
            switch_frame,
            text="Don't have a vault?",
            text_color=COLOR_TEXT_MUTED,
            font=(FONT_FAMILY, 10),
        ).pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            switch_frame,
            text="Create Account",
            fg_color="transparent",
            hover_color=COLOR_BG,
            text_color=COLOR_PRIMARY,
            font=(FONT_FAMILY, 10, "bold"),
            command=self.show_register_screen,
            width=120,
            height=28,
            border_width=0,
        ).pack(side="left")

    def handle_login(self):
        username = self.login_username_entry.get().strip()
        password = self.login_password_entry.get()

        if not username or not password:
            self.login_status_label.configure(
                text="Please enter both username and master password.",
                text_color=COLOR_DANGER,
            )
            return

        result = auth.login_user(username, password)
        if result is None:
            self.login_status_label.configure(
                text="Invalid username or master password.",
                text_color=COLOR_DANGER,
            )
            self.login_password_entry.delete(0, tk.END)
            return

        user_id, encryption_key = result
        self.current_user_id = user_id
        self.current_encryption_key = encryption_key
        self.current_username = username

        self.reset_auto_lock_timer()
        self.show_dashboard_screen()

    # ----------------------------------------------------------------------
    # 2. Registration Screen  (CustomTkinter)
    # ----------------------------------------------------------------------
    def show_register_screen(self):
        self.clear_container()
        self.root.minsize(420, 580)
        self.root.geometry("460x630")
        self._set_window_resizable(False, False)

        # Outer padding wrapper
        outer = ctk.CTkFrame(self.container, fg_color=COLOR_BG, corner_radius=0)
        outer.pack(fill="both", expand=True, padx=28, pady=16)

        # ---- Branding Header ----
        brand_frame = ctk.CTkFrame(outer, fg_color=COLOR_BG, corner_radius=0)
        brand_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            brand_frame,
            text="\U0001f6e1  ONESIUM",
            font=(FONT_FAMILY, 20, "bold"),
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(pady=(0, 2))

        ctk.CTkLabel(
            brand_frame,
            text="Create Your Vault",
            font=(FONT_FAMILY, 11),
            text_color=COLOR_TEXT_MUTED,
        ).pack(pady=(0, 0))

        # ---- Form Card ----
        card = ctk.CTkFrame(
            outer,
            fg_color=COLOR_SURFACE,
            corner_radius=12,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        card.pack(fill="x", pady=(10, 6))

        # Card inner content
        ci = ctk.CTkFrame(card, fg_color="transparent", corner_radius=0)
        ci.pack(fill="both", expand=True, padx=20, pady=14)

        # Username field
        ctk.CTkLabel(
            ci, text="Username",
            font=(FONT_FAMILY, 10, "bold"),
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(anchor="w", pady=(0, 4))

        self.reg_username_entry = ctk.CTkEntry(
            ci,
            height=38,
            corner_radius=8,
            fg_color=COLOR_INPUT,
            border_color=COLOR_BORDER,
            text_color=COLOR_TEXT_PRIMARY,
            placeholder_text="Choose a username",
            placeholder_text_color=COLOR_TEXT_MUTED,
        )
        self.reg_username_entry.pack(fill="x", pady=(0, 10))
        self.reg_username_entry.focus()

        # Master Password — label row with Show/Hide toggle
        pwd_row = ctk.CTkFrame(ci, fg_color="transparent", corner_radius=0)
        pwd_row.pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(
            pwd_row, text="Master Password",
            font=(FONT_FAMILY, 10, "bold"),
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(side="left")

        _pw1_shown = [False]

        def _toggle_reg_pw1():
            if _pw1_shown[0]:
                self.reg_password_entry.configure(show="*")
                _reg_eye1.configure(text="Show")
                _pw1_shown[0] = False
            else:
                self.reg_password_entry.configure(show="")
                _reg_eye1.configure(text="Hide")
                _pw1_shown[0] = True

        _reg_eye1 = ctk.CTkButton(
            pwd_row,
            text="Show",
            width=52, height=24,
            corner_radius=4,
            fg_color=COLOR_SURFACE_ELEVATED,
            hover_color=COLOR_BORDER,
            text_color=COLOR_TEXT_MUTED,
            font=(FONT_FAMILY, 9),
            command=_toggle_reg_pw1,
        )
        _reg_eye1.pack(side="right")

        self.reg_pwd_var = tk.StringVar()
        self.reg_password_entry = ctk.CTkEntry(
            ci,
            textvariable=self.reg_pwd_var,
            height=38,
            corner_radius=8,
            fg_color=COLOR_INPUT,
            border_color=COLOR_BORDER,
            text_color=COLOR_TEXT_PRIMARY,
            placeholder_text="Create a strong master password",
            placeholder_text_color=COLOR_TEXT_MUTED,
        )
        self.reg_password_entry.pack(fill="x", pady=(0, 4))
        self.reg_password_entry.configure(show="*")

        # Password strength indicator
        self.reg_strength_label = ctk.CTkLabel(
            ci,
            text="Strength: Very Weak",
            font=(FONT_FAMILY, 9, "bold"),
            text_color=COLOR_DANGER,
        )
        self.reg_strength_label.pack(anchor="w", pady=(0, 2))

        # Common password warning
        self.reg_common_warn = ctk.CTkLabel(
            ci,
            text="",
            font=(FONT_FAMILY, 9),
            text_color=COLOR_DANGER,
        )
        self.reg_common_warn.pack(anchor="w", pady=(0, 8))

        def update_reg_feedback(*args):
            val = self.reg_pwd_var.get()
            st = password_utils.check_password_strength(val)
            color = _STRENGTH_COLORS.get(st["label"], COLOR_TEXT_SECONDARY)
            self.reg_strength_label.configure(
                text=f"Strength: {st['label']}",
                text_color=color,
            )
            if password_utils.is_common_password(val):
                self.reg_common_warn.configure(text="\u26a0  This is a commonly used password.")
            else:
                self.reg_common_warn.configure(text="")

        self.reg_pwd_var.trace_add("write", update_reg_feedback)

        # Confirm Master Password — label row with Show/Hide toggle
        cpwd_row = ctk.CTkFrame(ci, fg_color="transparent", corner_radius=0)
        cpwd_row.pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(
            cpwd_row, text="Confirm Master Password",
            font=(FONT_FAMILY, 10, "bold"),
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(side="left")

        _pw2_shown = [False]

        def _toggle_reg_pw2():
            if _pw2_shown[0]:
                self.reg_confirm_entry.configure(show="*")
                _reg_eye2.configure(text="Show")
                _pw2_shown[0] = False
            else:
                self.reg_confirm_entry.configure(show="")
                _reg_eye2.configure(text="Hide")
                _pw2_shown[0] = True

        _reg_eye2 = ctk.CTkButton(
            cpwd_row,
            text="Show",
            width=52, height=24,
            corner_radius=4,
            fg_color=COLOR_SURFACE_ELEVATED,
            hover_color=COLOR_BORDER,
            text_color=COLOR_TEXT_MUTED,
            font=(FONT_FAMILY, 9),
            command=_toggle_reg_pw2,
        )
        _reg_eye2.pack(side="right")

        self.reg_confirm_entry = ctk.CTkEntry(
            ci,
            height=38,
            corner_radius=8,
            fg_color=COLOR_INPUT,
            border_color=COLOR_BORDER,
            text_color=COLOR_TEXT_PRIMARY,
            placeholder_text="Confirm your master password",
            placeholder_text_color=COLOR_TEXT_MUTED,
        )
        self.reg_confirm_entry.pack(fill="x", pady=(0, 10))
        self.reg_confirm_entry.configure(show="*")
        self.reg_confirm_entry.bind("<Return>", lambda e: self.handle_register())

        # Status / error message label
        self.reg_status_label = ctk.CTkLabel(
            ci,
            text="",
            text_color=COLOR_DANGER,
            font=(FONT_FAMILY, 9),
            wraplength=360,
        )
        self.reg_status_label.pack(pady=(0, 6))

        # Create Vault — primary action button
        ctk.CTkButton(
            ci,
            text="Create Vault",
            height=42,
            corner_radius=8,
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            text_color="#FFFFFF",
            font=(FONT_FAMILY, 11, "bold"),
            command=self.handle_register,
        ).pack(fill="x", pady=(0, 4))

        # ---- Back to Login link ----
        switch_frame = ctk.CTkFrame(outer, fg_color=COLOR_BG, corner_radius=0)
        switch_frame.pack(pady=(6, 0))

        ctk.CTkLabel(
            switch_frame,
            text="Already have a vault?",
            text_color=COLOR_TEXT_MUTED,
            font=(FONT_FAMILY, 10),
        ).pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            switch_frame,
            text="Back to Login",
            fg_color="transparent",
            hover_color=COLOR_BG,
            text_color=COLOR_PRIMARY,
            font=(FONT_FAMILY, 10, "bold"),
            command=self.show_login_screen,
            width=110,
            height=28,
            border_width=0,
        ).pack(side="left")

    def handle_register(self):
        username = self.reg_username_entry.get().strip()
        password = self.reg_password_entry.get()
        confirm_password = self.reg_confirm_entry.get()

        if not username:
            self.reg_status_label.configure(text="Username cannot be empty.", text_color=COLOR_DANGER)
            return

        if not password:
            self.reg_status_label.configure(text="Master password cannot be empty.", text_color=COLOR_DANGER)
            return

        if password != confirm_password:
            self.reg_status_label.configure(text="Passwords do not match.", text_color=COLOR_DANGER)
            return

        try:
            user_id = auth.register_user(username, password)
        except (ValueError, TypeError) as e:
            self.reg_status_label.configure(text=str(e), text_color=COLOR_DANGER)
            return

        if user_id is None:
            self.reg_status_label.configure(
                text="Username already exists. Please choose another.",
                text_color=COLOR_DANGER,
            )
            return

        # Registration successful → return to login with green success banner
        self.show_login_screen(
            initial_message=f"Account '{username}' created successfully! Please login.",
            is_success=True,
        )

    # ----------------------------------------------------------------------
    # 3. Vault Dashboard Screen  (CustomTkinter)
    # ----------------------------------------------------------------------
    def show_dashboard_screen(self):
        self.clear_container()
        self.root.minsize(800, 520)
        self.root.geometry("980x620")
        self._set_window_resizable(True, True)
        center_window(self.root, 980, 620)

        self.selected_entry_id = None
        self._last_search_query = ""
        self._total_credential_count = 0

        # Root layout: Sidebar (left) + 1px divider + Main Content Area (right)
        body_frame = ctk.CTkFrame(self.container, fg_color=COLOR_BG, corner_radius=0)
        body_frame.pack(fill="both", expand=True)

        self._build_dashboard_sidebar(body_frame)

        divider = ctk.CTkFrame(body_frame, width=1, fg_color=COLOR_BORDER, corner_radius=0)
        divider.pack(side="left", fill="y")

        self._build_dashboard_main(body_frame)

        # Initial data load (metadata only, never decrypts passwords)
        self.refresh_credential_list()

    def _make_sidebar_item(self, parent, icon_name, label_text, command, active=False, tooltip_text=""):
        """Creates a compact rounded sidebar navigation button with aligned icon and hover state."""
        base_fg = COLOR_SURFACE_ELEVATED if active else "transparent"
        hover_fg = COLOR_SURFACE_ELEVATED
        text_fg = COLOR_TEXT_PRIMARY if active else COLOR_TEXT_SECONDARY
        icon_fg = COLOR_PRIMARY if active else COLOR_TEXT_MUTED

        row = ctk.CTkFrame(
            parent,
            height=36,
            corner_radius=8,
            fg_color=base_fg,
            border_width=1 if active else 0,
            border_color=COLOR_BORDER if active else COLOR_SURFACE,
            cursor="hand2",
        )
        row.pack(fill="x", pady=(0, 4))
        row.pack_propagate(False)

        if active:
            accent = ctk.CTkFrame(row, width=3, height=18, corner_radius=2, fg_color=COLOR_PRIMARY)
            accent.pack(side="left", padx=(4, 6), pady=9)
        else:
            spacer = ctk.CTkFrame(row, width=3, height=18, fg_color="transparent")
            spacer.pack(side="left", padx=(4, 6))

        icon_lbl = ctk.CTkLabel(
            row,
            text=self._icon_glyph(icon_name),
            font=self._icon_font_tuple(13),
            text_color=icon_fg,
            fg_color="transparent",
            width=20,
        )
        icon_lbl.pack(side="left", padx=(0, 8))

        text_lbl = ctk.CTkLabel(
            row,
            text=label_text,
            font=(FONT_FAMILY, 11, "bold" if active else "normal"),
            text_color=text_fg,
            fg_color="transparent",
            anchor="w",
        )
        text_lbl.pack(side="left", fill="x", expand=True)

        def on_enter(_event=None):
            if not active:
                row.configure(fg_color=hover_fg)
                text_lbl.configure(text_color=COLOR_TEXT_PRIMARY)
                icon_lbl.configure(text_color=COLOR_TEXT_PRIMARY)

        def on_leave(_event=None):
            if active:
                return
            try:
                px, py = row.winfo_pointerxy()
                rx, ry = row.winfo_rootx(), row.winfo_rooty()
                if rx <= px <= rx + row.winfo_width() and ry <= py <= ry + row.winfo_height():
                    return
            except tk.TclError:
                return
            row.configure(fg_color=base_fg)
            text_lbl.configure(text_color=text_fg)
            icon_lbl.configure(text_color=icon_fg)

        def on_click(_event=None):
            if callable(command):
                command()

        for widget in row.winfo_children() + [row]:
            widget.configure(cursor="hand2")
            widget.bind("<Enter>", on_enter, add="+")
            widget.bind("<Leave>", on_leave, add="+")
            widget.bind("<Button-1>", on_click, add="+")

        if tooltip_text:
            _ToolTip(row, tooltip_text)

        row.invoke = command
        return row

    def _build_dashboard_sidebar(self, parent):
        """Builds the secondary left navigation sidebar."""
        sidebar = ctk.CTkFrame(parent, width=228, fg_color=COLOR_SURFACE, corner_radius=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        inner = ctk.CTkFrame(sidebar, fg_color="transparent", corner_radius=0)
        inner.pack(fill="both", expand=True, padx=14, pady=18)

        # ---- Branding ----
        brand_row = ctk.CTkFrame(inner, fg_color="transparent", corner_radius=0)
        brand_row.pack(fill="x", pady=(0, 10))

        logo_badge = ctk.CTkFrame(
            brand_row,
            width=32,
            height=32,
            corner_radius=8,
            fg_color=COLOR_SURFACE_ELEVATED,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        logo_badge.pack(side="left", padx=(0, 10))
        logo_badge.pack_propagate(False)

        ctk.CTkLabel(
            logo_badge,
            text=self._icon_glyph("shield"),
            font=self._icon_font_tuple(14),
            text_color=COLOR_PRIMARY,
            fg_color="transparent",
        ).pack(expand=True)

        brand_text = ctk.CTkFrame(brand_row, fg_color="transparent", corner_radius=0)
        brand_text.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            brand_text,
            text="ONESIUM",
            font=(FONT_FAMILY, 14, "bold"),
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            brand_text,
            text="The Credential Vault",
            font=(FONT_FAMILY, 9),
            text_color=COLOR_TEXT_MUTED,
            anchor="w",
        ).pack(anchor="w")

        # ---- Offline / Private / Local Status Pill ----
        status_pill = ctk.CTkFrame(
            inner,
            height=28,
            corner_radius=8,
            fg_color=COLOR_INPUT,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        status_pill.pack(fill="x", pady=(2, 18))
        status_pill.pack_propagate(False)

        ctk.CTkLabel(
            status_pill,
            text="\u25cf  Offline \u2022 Private \u2022 Local",
            font=(FONT_FAMILY, 9, "bold"),
            text_color=COLOR_SUCCESS,
            fg_color=COLOR_INPUT,
            anchor="w",
        ).pack(side="left", padx=10, pady=2)
        _ToolTip(status_pill, "All credentials stay encrypted locally on this device.")

        # ---- Navigation Section ----
        ctk.CTkLabel(
            inner,
            text="NAVIGATION",
            font=(FONT_FAMILY, 9, "bold"),
            text_color=COLOR_TEXT_MUTED,
            anchor="w",
        ).pack(anchor="w", padx=6, pady=(0, 6))

        self.nav_vault_btn = self._make_sidebar_item(
            inner,
            icon_name="vault",
            label_text="Your Vault",
            command=self.clear_search,
            active=True,
            tooltip_text="View all saved credentials",
        )

        self.nav_generator_btn = self._make_sidebar_item(
            inner,
            icon_name="key",
            label_text="Password Generator",
            command=self.open_generator_dialog,
            active=False,
            tooltip_text="Generate a strong random password",
        )

        # ---- Vault Tools Section ----
        ctk.CTkLabel(
            inner,
            text="VAULT TOOLS",
            font=(FONT_FAMILY, 9, "bold"),
            text_color=COLOR_TEXT_MUTED,
            anchor="w",
        ).pack(anchor="w", padx=6, pady=(14, 6))

        self.nav_backup_btn = self._make_sidebar_item(
            inner,
            icon_name="upload",
            label_text="Backup Vault",
            command=self.handle_backup,
            active=False,
            tooltip_text="Export an encrypted backup (.pmv)",
        )

        self.nav_restore_btn = self._make_sidebar_item(
            inner,
            icon_name="download",
            label_text="Restore Vault",
            command=self.handle_restore,
            active=False,
            tooltip_text="Restore credentials from an encrypted backup",
        )

        # ---- Bottom User Session & Lock / Logout ----
        bottom_box = ctk.CTkFrame(inner, fg_color="transparent", corner_radius=0)
        bottom_box.pack(side="bottom", fill="x")

        ctk.CTkFrame(bottom_box, height=1, fg_color=COLOR_BORDER, corner_radius=0).pack(
            fill="x", pady=(0, 12)
        )

        user_card = ctk.CTkFrame(
            bottom_box,
            corner_radius=8,
            fg_color=COLOR_INPUT,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        user_card.pack(fill="x", pady=(0, 8))

        user_inner = ctk.CTkFrame(user_card, fg_color="transparent", corner_radius=0)
        user_inner.pack(fill="x", padx=10, pady=8)

        avatar = ctk.CTkFrame(
            user_inner,
            width=28,
            height=28,
            corner_radius=14,
            fg_color=COLOR_SURFACE_ELEVATED,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        avatar.pack(side="left", padx=(0, 8))
        avatar.pack_propagate(False)

        ctk.CTkLabel(
            avatar,
            text=self._icon_glyph("user"),
            font=self._icon_font_tuple(12),
            text_color=COLOR_TEXT_SECONDARY,
            fg_color="transparent",
        ).pack(expand=True)

        user_meta = ctk.CTkFrame(user_inner, fg_color="transparent", corner_radius=0)
        user_meta.pack(side="left", fill="x", expand=True)

        self.sidebar_user_label = ctk.CTkLabel(
            user_meta,
            text=_truncate_text(self.current_username or "User", 16),
            font=(FONT_FAMILY, 10, "bold"),
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w",
        )
        self.sidebar_user_label.pack(anchor="w")

        ctk.CTkLabel(
            user_meta,
            text="Local session",
            font=(FONT_FAMILY, 9),
            text_color=COLOR_TEXT_MUTED,
            anchor="w",
        ).pack(anchor="w")

        self.btn_logout = self._make_sidebar_item(
            bottom_box,
            icon_name="logout",
            label_text="Lock & Logout",
            command=self.handle_logout,
            active=False,
            tooltip_text="Lock vault, clear clipboard, and return to login",
        )
        self.btn_logout.configure(
            fg_color=COLOR_SURFACE_ELEVATED,
            border_width=1,
            border_color=COLOR_BORDER,
        )

    def _build_dashboard_main(self, parent):
        """Builds the main vault header, search toolbar, credential list, and empty state."""
        main_area = ctk.CTkFrame(parent, fg_color=COLOR_BG, corner_radius=0)
        main_area.pack(side="left", fill="both", expand=True, padx=24, pady=20)

        # ---- Top Header Row ----
        header_row = ctk.CTkFrame(main_area, fg_color="transparent", corner_radius=0)
        header_row.pack(fill="x", pady=(0, 14))

        title_col = ctk.CTkFrame(header_row, fg_color="transparent", corner_radius=0)
        title_col.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            title_col,
            text="Your Vault",
            font=(FONT_FAMILY, 20, "bold"),
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_col,
            text="Your credentials, securely stored on this device.",
            font=(FONT_FAMILY, 11),
            text_color=COLOR_TEXT_SECONDARY,
            anchor="w",
        ).pack(anchor="w", pady=(2, 0))

        count_pill = ctk.CTkFrame(
            header_row,
            height=30,
            corner_radius=8,
            fg_color=COLOR_SURFACE,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        count_pill.pack(side="right", anchor="n", pady=(4, 0))

        self.count_badge = ctk.CTkLabel(
            count_pill,
            text="0 Saved",
            font=(FONT_FAMILY, 10, "bold"),
            text_color=COLOR_TEXT_SECONDARY,
            fg_color=COLOR_SURFACE,
            padx=10,
            pady=3,
        )
        self.count_badge.pack(padx=2, pady=2)

        # ---- Search Bar & Primary Add Action Row ----
        toolbar = ctk.CTkFrame(main_area, fg_color="transparent", corner_radius=0)
        toolbar.pack(fill="x", pady=(0, 14))

        search_box = ctk.CTkFrame(
            toolbar,
            height=40,
            corner_radius=8,
            fg_color=COLOR_INPUT,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        search_box.pack(side="left", fill="x", expand=True, padx=(0, 12))
        search_box.pack_propagate(False)

        search_icon = ctk.CTkLabel(
            search_box,
            text=self._icon_glyph("search"),
            font=self._icon_font_tuple(13),
            text_color=COLOR_TEXT_MUTED,
            fg_color=COLOR_INPUT,
            width=26,
        )
        search_icon.pack(side="left", padx=(10, 4), pady=4)

        self.search_entry = ctk.CTkEntry(
            search_box,
            height=32,
            border_width=0,
            corner_radius=0,
            fg_color=COLOR_INPUT,
            text_color=COLOR_TEXT_PRIMARY,
            placeholder_text="Search by site or username...",
            placeholder_text_color=COLOR_TEXT_MUTED,
            font=(FONT_FAMILY, 11),
        )
        self.search_entry.pack(side="left", fill="both", expand=True, pady=3)
        self.search_entry.bind("<KeyRelease>", self.handle_search)
        self.search_entry.bind("<Escape>", lambda e: self.clear_search())

        self.clear_search_btn = ctk.CTkButton(
            search_box,
            text=self._icon_glyph("clear"),
            font=self._icon_font_tuple(11),
            width=28,
            height=28,
            corner_radius=6,
            fg_color=COLOR_INPUT,
            hover_color=COLOR_SURFACE_ELEVATED,
            text_color=COLOR_TEXT_MUTED,
            command=self.clear_search,
        )
        self.clear_search_btn.pack(side="right", padx=(4, 6), pady=4)
        _ToolTip(self.clear_search_btn, "Clear search")

        self.btn_add = ctk.CTkButton(
            toolbar,
            text="+  Add Credential",
            height=40,
            width=156,
            corner_radius=8,
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            text_color="#FFFFFF",
            font=(FONT_FAMILY, 11, "bold"),
            command=self.open_add_dialog,
        )
        self.btn_add.pack(side="right")
        _ToolTip(self.btn_add, "Add a new credential to your vault")

        # ---- List / Empty State Host ----
        self.list_host = ctk.CTkFrame(main_area, fg_color=COLOR_BG, corner_radius=0)
        self.list_host.pack(fill="both", expand=True)

        # Scrollable Credential List Viewport (Canvas + CTkScrollbar + CTkFrame)
        self.list_viewport_frame = ctk.CTkFrame(self.list_host, fg_color=COLOR_BG, corner_radius=0)

        self._list_canvas = tk.Canvas(
            self.list_viewport_frame,
            bg=COLOR_BG,
            highlightthickness=0,
            bd=0,
            yscrollincrement=20,
        )
        self._list_scrollbar = ctk.CTkScrollbar(
            self.list_viewport_frame,
            orientation="vertical",
            command=self._list_canvas.yview,
            fg_color=COLOR_BG,
            button_color=COLOR_SURFACE_ELEVATED,
            button_hover_color=COLOR_BORDER,
        )
        self._list_canvas.configure(yscrollcommand=self._list_scrollbar.set)

        self._list_scrollbar.pack(side="right", fill="y", padx=(6, 0))
        self._list_canvas.pack(side="left", fill="both", expand=True)

        self.credential_rows_frame = ctk.CTkFrame(self._list_canvas, fg_color=COLOR_BG, corner_radius=0)
        self._list_canvas_window = self._list_canvas.create_window(
            (0, 0),
            window=self.credential_rows_frame,
            anchor="nw",
        )

        def _sync_scrollregion(_event=None):
            if self._list_canvas and self._list_canvas.winfo_exists():
                bbox = self._list_canvas.bbox("all")
                if bbox:
                    self._list_canvas.configure(scrollregion=bbox)
                else:
                    self._list_canvas.configure(scrollregion=(0, 0, 0, 0))
                self._update_scrollbar_visibility()

        def _fit_rows_width(event):
            if self._list_canvas and self._list_canvas.winfo_exists() and self._list_canvas_window is not None:
                self._list_canvas.itemconfigure(self._list_canvas_window, width=event.width)
                self._update_scrollbar_visibility()

        self.credential_rows_frame.bind("<Configure>", _sync_scrollregion)
        self._list_canvas.bind("<Configure>", _fit_rows_width)

        # ---- Designed Empty State ----
        self.empty_state_frame = ctk.CTkFrame(self.list_host, fg_color=COLOR_BG, corner_radius=0)

        empty_card = ctk.CTkFrame(
            self.empty_state_frame,
            width=400,
            corner_radius=14,
            fg_color=COLOR_SURFACE,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        empty_card.place(relx=0.5, rely=0.46, anchor="center")

        empty_inner = ctk.CTkFrame(empty_card, fg_color="transparent", corner_radius=0)
        empty_inner.pack(padx=34, pady=30)

        empty_icon_badge = ctk.CTkFrame(
            empty_inner,
            width=54,
            height=54,
            corner_radius=14,
            fg_color=COLOR_SURFACE_ELEVATED,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        empty_icon_badge.pack(pady=(0, 14))
        empty_icon_badge.pack_propagate(False)

        self.empty_icon_label = ctk.CTkLabel(
            empty_icon_badge,
            text=self._icon_glyph("shield_check"),
            font=self._icon_font_tuple(22),
            text_color=COLOR_PRIMARY,
            fg_color="transparent",
        )
        self.empty_icon_label.pack(expand=True)

        self.empty_title_label = ctk.CTkLabel(
            empty_inner,
            text="Your vault is empty",
            font=(FONT_FAMILY, 15, "bold"),
            text_color=COLOR_TEXT_PRIMARY,
        )
        self.empty_title_label.pack(pady=(0, 6))

        self.empty_desc_label = ctk.CTkLabel(
            empty_inner,
            text="Add your first credential to keep logins encrypted and accessible only on this device.",
            font=(FONT_FAMILY, 11),
            text_color=COLOR_TEXT_SECONDARY,
            wraplength=310,
            justify="center",
        )
        self.empty_desc_label.pack(pady=(0, 18))

        self.empty_action_btn = ctk.CTkButton(
            empty_inner,
            text="+  Add Your First Credential",
            height=40,
            width=220,
            corner_radius=8,
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            text_color="#FFFFFF",
            font=(FONT_FAMILY, 11, "bold"),
            command=self.open_add_dialog,
        )
        self.empty_action_btn.pack()

    def _update_scrollbar_visibility(self):
        """Shows the vertical scrollbar only when credential rows overflow the viewport."""
        if not self._list_canvas or not hasattr(self, "_list_scrollbar"):
            return
        try:
            if not self._list_canvas.winfo_exists():
                return
            yview = self._list_canvas.yview()
            needs_scroll = yview != (0.0, 1.0)
            is_packed = bool(self._list_scrollbar.winfo_manager())
            if needs_scroll and not is_packed:
                self._list_scrollbar.pack(side="right", fill="y", padx=(6, 0), before=self._list_canvas)
            elif not needs_scroll and is_packed:
                self._list_scrollbar.pack_forget()
        except tk.TclError:
            pass

    def _create_credential_row(self, entry):
        """
        Creates a modern CustomTkinter credential card for a single sqlite3.Row.
        Strictly renders non-sensitive metadata only; never reads or decrypts passwords.
        """
        entry_id = entry["entry_id"]
        site_name = entry["site_name"]
        username_field = entry["username_field"]
        updated_at = entry["updated_at"]

        is_selected = self.selected_entry_id == entry_id
        card_fg = COLOR_SURFACE_ELEVATED if is_selected else COLOR_SURFACE
        card_border = COLOR_PRIMARY if is_selected else COLOR_BORDER

        card = ctk.CTkFrame(
            self.credential_rows_frame,
            height=64,
            corner_radius=10,
            fg_color=card_fg,
            border_width=1,
            border_color=card_border,
            cursor="hand2",
        )
        card.pack(fill="x", pady=(0, 8))
        card.grid_propagate(False)
        card.grid_columnconfigure(1, weight=1)
        card.grid_rowconfigure(0, weight=1)

        # Column 0: Application monogram or neutral fallback icon
        clean_site = (site_name or "").strip()
        first_char = clean_site[0].upper() if clean_site and clean_site[0].isalnum() else None

        icon_tile = ctk.CTkFrame(
            card,
            width=38,
            height=38,
            corner_radius=8,
            fg_color=COLOR_SURFACE_ELEVATED if not is_selected else COLOR_INPUT,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        icon_tile.grid(row=0, column=0, padx=(14, 12), pady=12)
        icon_tile.pack_propagate(False)

        if first_char:
            ctk.CTkLabel(
                icon_tile,
                text=first_char,
                font=(FONT_FAMILY, 13, "bold"),
                text_color=COLOR_PRIMARY,
                fg_color="transparent",
            ).pack(expand=True)
        else:
            ctk.CTkLabel(
                icon_tile,
                text=self._icon_glyph("globe"),
                font=self._icon_font_tuple(15),
                text_color=COLOR_TEXT_SECONDARY,
                fg_color="transparent",
            ).pack(expand=True)

        # Column 1: Site / App name + Username / Email
        meta_box = ctk.CTkFrame(card, fg_color="transparent", corner_radius=0)
        meta_box.grid(row=0, column=1, sticky="ew", pady=10)

        site_lbl = ctk.CTkLabel(
            meta_box,
            text=_truncate_text(site_name, 46),
            font=(FONT_FAMILY, 12, "bold"),
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w",
        )
        site_lbl.pack(anchor="w")

        user_lbl = ctk.CTkLabel(
            meta_box,
            text=_truncate_text(username_field, 52),
            font=(FONT_FAMILY, 10),
            text_color=COLOR_TEXT_SECONDARY,
            anchor="w",
        )
        user_lbl.pack(anchor="w")

        # Column 2: Subtle Last Updated date
        date_text = _format_updated_date(updated_at)
        date_lbl = ctk.CTkLabel(
            card,
            text=date_text,
            font=(FONT_FAMILY, 10),
            text_color=COLOR_TEXT_MUTED,
            anchor="e",
        )
        date_lbl.grid(row=0, column=2, padx=(12, 10))

        # Column 3: Subtle chevron affordance (row click selects; Milestone 3 opens detail view)
        chevron_lbl = ctk.CTkLabel(
            card,
            text=self._icon_glyph("chevron"),
            font=self._icon_font_tuple(11),
            text_color=COLOR_PRIMARY if is_selected else COLOR_TEXT_MUTED,
            width=20,
        )
        chevron_lbl.grid(row=0, column=3, padx=(0, 14))
        _ToolTip(chevron_lbl, "Select credential")

        # Store metadata-only widget references (never store passwords)
        self.row_widgets[entry_id] = {
            "card": card,
            "icon_tile": icon_tile,
            "chevron": chevron_lbl,
            "site_name": site_name,
            "username_field": username_field,
            "updated_at": updated_at,
        }

        def on_enter(_event=None):
            if self.selected_entry_id != entry_id:
                card.configure(fg_color=COLOR_SURFACE_ELEVATED)
                chevron_lbl.configure(text_color=COLOR_TEXT_PRIMARY)

        def on_leave(_event=None):
            if self.selected_entry_id == entry_id:
                return
            try:
                px, py = card.winfo_pointerxy()
                cx, cy = card.winfo_rootx(), card.winfo_rooty()
                if cx <= px <= cx + card.winfo_width() and cy <= py <= cy + card.winfo_height():
                    return
            except tk.TclError:
                return
            card.configure(fg_color=COLOR_SURFACE)
            chevron_lbl.configure(text_color=COLOR_TEXT_MUTED)

        def on_click(_event=None):
            self.handle_row_click(entry_id)

        # Bind click & hover cleanly across the entire row card
        bind_targets = [card, icon_tile, meta_box, site_lbl, user_lbl, date_lbl, chevron_lbl]
        for child in icon_tile.winfo_children():
            bind_targets.append(child)
        for target in bind_targets:
            target.configure(cursor="hand2")
            target.bind("<Enter>", on_enter, add="+")
            target.bind("<Leave>", on_leave, add="+")
            target.bind("<Button-1>", on_click, add="+")

    def refresh_credential_list(self, entries=None, is_filtered=False):
        """
        Populates the modern CustomTkinter credential list without decrypting passwords.
        """
        if not hasattr(self, "credential_rows_frame"):
            return

        self.selected_entry_id = None
        self.row_widgets = {}

        for widget in self.credential_rows_frame.winfo_children():
            widget.destroy()

        if entries is None:
            self._last_search_query = ""
            if hasattr(self, "search_entry") and self.search_entry.winfo_exists():
                if self.search_entry.get():
                    self.search_entry.delete(0, tk.END)
            entries = vault.get_credentials(self.current_user_id)
            self._total_credential_count = len(entries)
            is_filtered = False

        self.displayed_entries = list(entries)

        if len(self.displayed_entries) == 0:
            self.list_viewport_frame.pack_forget()
            if is_filtered:
                self.empty_icon_label.configure(text=self._icon_glyph("search"))
                self.empty_title_label.configure(text="No matching credentials")
                query_preview = _truncate_text(self._last_search_query.strip(), 32)
                self.empty_desc_label.configure(
                    text=f'No saved credentials match "{query_preview}".'
                )
                self.empty_action_btn.configure(
                    text="Clear Search",
                    command=self.clear_search,
                )
            else:
                self.empty_icon_label.configure(text=self._icon_glyph("shield_check"))
                self.empty_title_label.configure(text="Your vault is empty")
                self.empty_desc_label.configure(
                    text="Add your first credential to keep logins encrypted and accessible only on this device."
                )
                self.empty_action_btn.configure(
                    text="+  Add Your First Credential",
                    command=self.open_add_dialog,
                )
            self.empty_state_frame.pack(fill="both", expand=True)
        else:
            self.empty_state_frame.pack_forget()
            self.list_viewport_frame.pack(fill="both", expand=True)
            for entry in self.displayed_entries:
                self._create_credential_row(entry)
            if self._list_canvas is not None:
                self._list_canvas.yview_moveto(0)

        if hasattr(self, "count_badge"):
            shown_count = len(self.displayed_entries)
            if is_filtered:
                self.count_badge.configure(
                    text=f"{shown_count} of {self._total_credential_count} Saved"
                )
            else:
                self.count_badge.configure(text=f"{shown_count} Saved")

    def handle_search(self, event=None):
        """Filters displayed credentials via vault.search_credentials without decryption."""
        query = self.search_entry.get()
        if event is not None and query == self._last_search_query:
            return
        self._last_search_query = query

        stripped = query.strip()
        if not stripped:
            self.refresh_credential_list()
            return

        entries = vault.search_credentials(self.current_user_id, stripped)
        self.refresh_credential_list(entries, is_filtered=True)

    def clear_search(self):
        """Clears the search input and restores the full credential list."""
        self._last_search_query = ""
        if hasattr(self, "search_entry") and self.search_entry.winfo_exists():
            self.search_entry.delete(0, tk.END)
        self.refresh_credential_list()

    def handle_row_click(self, entry_id):
        """Selects a credential row and invokes the Milestone 3 detail hook."""
        prev_id = self.selected_entry_id
        if prev_id is not None and prev_id in self.row_widgets and prev_id != entry_id:
            prev_row = self.row_widgets[prev_id]
            prev_row["card"].configure(fg_color=COLOR_SURFACE, border_color=COLOR_BORDER)
            prev_row["icon_tile"].configure(fg_color=COLOR_SURFACE_ELEVATED)
            prev_row["chevron"].configure(text_color=COLOR_TEXT_MUTED)

        self.selected_entry_id = entry_id
        if entry_id in self.row_widgets:
            cur_row = self.row_widgets[entry_id]
            cur_row["card"].configure(fg_color=COLOR_SURFACE_ELEVATED, border_color=COLOR_PRIMARY)
            cur_row["icon_tile"].configure(fg_color=COLOR_INPUT)
            cur_row["chevron"].configure(text_color=COLOR_PRIMARY)

        self.on_credential_row_click(entry_id)

    def on_credential_row_click(self, entry_id):
        """
        Extension hook wired to credential row clicks.
        Milestone 3 will open the dedicated credential detail page from here.
        """
        return None

    def update_action_button_states(self):
        """Retained for compatibility; dashboard row selection manages visual state."""
        return None

    # ----------------------------------------------------------------------
    # 4. Add Credential Dialog
    # ----------------------------------------------------------------------
    def open_add_dialog(self):
        if self.active_dialog and self.active_dialog.winfo_exists():
            self.active_dialog.destroy()

        dialog = tk.Toplevel(self.root)
        dialog.title("Onesium — Add Credential")
        dialog.resizable(False, False)
        dialog.configure(bg=COLOR_BG)
        dialog.transient(self.root)
        dialog.grab_set()
        self.active_dialog = dialog
        center_window(dialog, 430, 490, self.root)

        frame = ttk.Frame(dialog, padding=20)
        frame.pack(fill="both", expand=True)

        # Header
        header_box = tk.Frame(frame, bg=COLOR_BG)
        header_box.pack(fill="x", pady=(0, 10))
        tk.Label(header_box, text="Add Credential", font=(FONT_FAMILY, 12, "bold"), bg=COLOR_BG, fg=COLOR_TEXT_PRIMARY).pack(anchor="w")
        tk.Label(header_box, text="Store credentials locally on this device.", font=(FONT_FAMILY, 8), bg=COLOR_BG, fg=COLOR_TEXT_MUTED).pack(anchor="w")

        # Field 1: Site / App (Direct child of frame)
        ttk.Label(frame, text="Site / App:").pack(anchor="w", pady=(0, 2))
        site_entry = ttk.Entry(frame, width=35)
        site_entry.pack(fill="x", pady=(0, 8))
        site_entry.focus()

        # Field 2: Username / Identifier (Direct child of frame)
        ttk.Label(frame, text="Username / Identifier:").pack(anchor="w", pady=(0, 2))
        user_entry = ttk.Entry(frame, width=35)
        user_entry.pack(fill="x", pady=(0, 8))

        # Field 3: Password Header + Generate & Eye Buttons
        pwd_header_frame = ttk.Frame(frame)
        pwd_header_frame.pack(fill="x", pady=(0, 2))

        ttk.Label(pwd_header_frame, text="Password:").pack(side="left")

        def generate_pwd():
            gen = password_utils.generate_password()
            pwd_entry.delete(0, tk.END)
            pwd_entry.insert(0, gen)

        gen_btn = ttk.Button(pwd_header_frame, text="Generate", command=generate_pwd)
        gen_btn.pack(side="right")

        eye_btn = tk.Button(
            pwd_header_frame,
            text="Show",
            font=(FONT_FAMILY, 8),
            bg=COLOR_SURFACE_ELEVATED,
            fg=COLOR_TEXT_MUTED,
            activebackground="#2A344A",
            activeforeground=COLOR_TEXT_PRIMARY,
            bd=1,
            relief="solid",
            padx=5,
            pady=0,
            cursor="hand2",
            command=lambda: self._toggle_show(pwd_entry, eye_btn),
        )
        eye_btn.pack(side="right", padx=(0, 6))

        # Password Entry Field (Direct child of frame with show="*")
        pwd_var = tk.StringVar()
        pwd_entry = ttk.Entry(frame, textvariable=pwd_var, show="*", width=35)
        pwd_entry.pack(fill="x", pady=(0, 2))

        # Strength & Common Warning Indicator (Direct children of frame)
        strength_label = ttk.Label(frame, text="Strength: Very Weak", font=("Helvetica", 8, "bold"))
        strength_label.pack(anchor="w", pady=(2, 1))

        common_warn_label = tk.Label(frame, text="", fg="#d9534f", bg=COLOR_BG, font=("Helvetica", 8))
        common_warn_label.pack(anchor="w", pady=(0, 6))

        def update_pwd_feedback(*args):
            val = pwd_var.get()
            strength_res = password_utils.check_password_strength(val)
            strength_label.config(text=f"Strength: {strength_res['label']}")
            if password_utils.is_common_password(val):
                common_warn_label.config(text="Warning: This is a commonly used password.")
            else:
                common_warn_label.config(text="")

        pwd_var.trace_add("write", update_pwd_feedback)

        # Field 4: Notes (Direct child of frame)
        ttk.Label(frame, text="Notes (Optional):").pack(anchor="w", pady=(0, 2))
        notes_entry = ttk.Entry(frame, width=35)
        notes_entry.pack(fill="x", pady=(0, 8))

        # Status & Error Message Label
        status_label = tk.Label(frame, text="", fg="red", bg=COLOR_BG, font=("Helvetica", 9), wraplength=360)
        status_label.pack(pady=(0, 8))

        # Action Buttons Row
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x")

        def save_add():
            site_name = site_entry.get().strip()
            username = user_entry.get().strip()
            password = pwd_entry.get()
            notes = notes_entry.get().strip()

            if not site_name:
                status_label.config(text="Site name cannot be empty.")
                return
            if not username:
                status_label.config(text="Username cannot be empty.")
                return
            if not password:
                status_label.config(text="Password cannot be empty.")
                return

            try:
                vault.add_credential(
                    user_id=self.current_user_id,
                    key=self.current_encryption_key,
                    site_name=site_name,
                    username=username,
                    password=password,
                    notes=notes,
                )
            except (ValueError, TypeError) as e:
                status_label.config(text=str(e))
                return

            dialog.destroy()
            self.active_dialog = None
            self.refresh_credential_list()

        def cancel_add():
            dialog.destroy()
            self.active_dialog = None

        dialog.protocol("WM_DELETE_WINDOW", cancel_add)

        save_btn = ttk.Button(btn_frame, text="Save", style="Primary.TButton", command=save_add)
        save_btn.pack(side="left", padx=(0, 6))

        cancel_btn = ttk.Button(btn_frame, text="Cancel", command=cancel_add)
        cancel_btn.pack(side="left")

    # ----------------------------------------------------------------------
    # 5. Edit Credential Dialog
    # ----------------------------------------------------------------------
    def open_edit_dialog(self):
        if self.selected_entry_id is None:
            return

        entries = vault.get_credentials(self.current_user_id)
        target = None
        for entry in entries:
            if entry["entry_id"] == self.selected_entry_id:
                target = entry
                break

        if target is None:
            return

        if self.active_dialog and self.active_dialog.winfo_exists():
            self.active_dialog.destroy()

        dialog = tk.Toplevel(self.root)
        dialog.title("Onesium — Edit Credential")
        dialog.resizable(False, False)
        dialog.configure(bg=COLOR_BG)
        dialog.transient(self.root)
        dialog.grab_set()
        self.active_dialog = dialog
        center_window(dialog, 430, 510, self.root)

        def cancel_edit():
            dialog.destroy()
            self.active_dialog = None

        dialog.protocol("WM_DELETE_WINDOW", cancel_edit)

        frame = ttk.Frame(dialog, padding=20)
        frame.pack(fill="both", expand=True)

        # Header
        header_box = tk.Frame(frame, bg=COLOR_BG)
        header_box.pack(fill="x", pady=(0, 10))
        tk.Label(header_box, text="Edit Credential", font=(FONT_FAMILY, 12, "bold"), bg=COLOR_BG, fg=COLOR_TEXT_PRIMARY).pack(anchor="w")
        tk.Label(header_box, text="Update credential stored in encrypted local vault.", font=(FONT_FAMILY, 8), bg=COLOR_BG, fg=COLOR_TEXT_MUTED).pack(anchor="w")

        # Field 1: Site / App (Direct child of frame)
        ttk.Label(frame, text="Site / App:").pack(anchor="w", pady=(0, 2))
        site_entry = ttk.Entry(frame, width=35)
        site_entry.insert(0, target["site_name"])
        site_entry.pack(fill="x", pady=(0, 8))
        site_entry.focus()

        # Field 2: Username / Identifier (Direct child of frame)
        ttk.Label(frame, text="Username / Identifier:").pack(anchor="w", pady=(0, 2))
        user_entry = ttk.Entry(frame, width=35)
        user_entry.insert(0, target["username_field"])
        user_entry.pack(fill="x", pady=(0, 8))

        # Field 3: Password Header + Regenerate & Eye Buttons
        pwd_header_frame = ttk.Frame(frame)
        pwd_header_frame.pack(fill="x", pady=(0, 2))

        ttk.Label(pwd_header_frame, text="New Password:").pack(side="left")

        def regenerate_pwd():
            gen = password_utils.generate_password()
            pwd_entry.delete(0, tk.END)
            pwd_entry.insert(0, gen)

        gen_btn = ttk.Button(pwd_header_frame, text="Generate", command=regenerate_pwd)
        gen_btn.pack(side="right")

        eye_btn = tk.Button(
            pwd_header_frame,
            text="Show",
            font=(FONT_FAMILY, 8),
            bg=COLOR_SURFACE_ELEVATED,
            fg=COLOR_TEXT_MUTED,
            activebackground="#2A344A",
            activeforeground=COLOR_TEXT_PRIMARY,
            bd=1,
            relief="solid",
            padx=5,
            pady=0,
            cursor="hand2",
            command=lambda: self._toggle_show(pwd_entry, eye_btn),
        )
        eye_btn.pack(side="right", padx=(0, 6))

        # Password Entry Field (Direct child of frame with show="*")
        pwd_var = tk.StringVar()
        pwd_entry = ttk.Entry(frame, textvariable=pwd_var, show="*", width=35)
        pwd_entry.pack(fill="x", pady=(0, 2))

        # Subtitle reminder that existing password is never decrypted
        info_lbl = tk.Label(frame, text="(Enter replacement password to save changes)", font=(FONT_FAMILY, 8), bg=COLOR_BG, fg=COLOR_TEXT_MUTED)
        info_lbl.pack(anchor="w", pady=(0, 2))

        # Strength & Common Warning Indicator (Direct children of frame)
        strength_label = ttk.Label(frame, text="Strength: Very Weak", font=("Helvetica", 8, "bold"))
        strength_label.pack(anchor="w", pady=(2, 1))

        common_warn_label = tk.Label(frame, text="", fg="#d9534f", bg=COLOR_BG, font=("Helvetica", 8))
        common_warn_label.pack(anchor="w", pady=(0, 6))

        def update_pwd_feedback(*args):
            val = pwd_var.get()
            strength_res = password_utils.check_password_strength(val)
            strength_label.config(text=f"Strength: {strength_res['label']}")
            if password_utils.is_common_password(val):
                common_warn_label.config(text="Warning: This is a commonly used password.")
            else:
                common_warn_label.config(text="")

        pwd_var.trace_add("write", update_pwd_feedback)

        # Field 4: Notes (Direct child of frame)
        ttk.Label(frame, text="Notes (Optional):").pack(anchor="w", pady=(0, 2))
        notes_entry = ttk.Entry(frame, width=35)
        notes_entry.insert(0, target["notes"] or "")
        notes_entry.pack(fill="x", pady=(0, 8))

        # Status & Error Message Label
        status_label = tk.Label(frame, text="", fg="red", bg=COLOR_BG, font=("Helvetica", 9), wraplength=360)
        status_label.pack(pady=(0, 8))

        # Action Buttons Row
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x")

        def save_edit():
            site_name = site_entry.get().strip()
            username = user_entry.get().strip()
            password = pwd_entry.get()
            notes = notes_entry.get().strip()

            if not site_name:
                status_label.config(text="Site name cannot be empty.")
                return
            if not username:
                status_label.config(text="Username cannot be empty.")
                return
            if not password:
                status_label.config(text="Password cannot be empty.")
                return

            try:
                ok = vault.update_credential(
                    user_id=self.current_user_id,
                    entry_id=target["entry_id"],
                    key=self.current_encryption_key,
                    site_name=site_name,
                    username=username,
                    password=password,
                    notes=notes,
                )
            except (ValueError, TypeError) as e:
                status_label.config(text=str(e))
                return

            if not ok:
                status_label.config(text="Failed to update credential.")
                return

            dialog.destroy()
            self.active_dialog = None
            self.refresh_credential_list()

        save_btn = ttk.Button(btn_frame, text="Save", style="Primary.TButton", command=save_edit)
        save_btn.pack(side="left", padx=(0, 6))

        cancel_btn = ttk.Button(btn_frame, text="Cancel", command=cancel_edit)
        cancel_btn.pack(side="left")

    # ----------------------------------------------------------------------
    # 6. Standalone Password Generator Tool Dialog
    # ----------------------------------------------------------------------
    def open_generator_dialog(self):
        """Opens a dedicated generator modal styled with the Onesium palette."""
        if self.active_dialog and self.active_dialog.winfo_exists():
            self.active_dialog.destroy()

        dialog = tk.Toplevel(self.root)
        dialog.title("Onesium — Password Generator")
        dialog.resizable(False, False)
        dialog.configure(bg=COLOR_BG)
        dialog.transient(self.root)
        dialog.grab_set()
        self.active_dialog = dialog
        center_window(dialog, 400, 320, self.root)

        def close_generator():
            dialog.destroy()
            self.active_dialog = None

        dialog.protocol("WM_DELETE_WINDOW", close_generator)

        frame = tk.Frame(
            dialog,
            bg=COLOR_SURFACE,
            padx=18,
            pady=16,
            bd=1,
            relief="solid",
            highlightbackground=COLOR_BORDER,
            highlightthickness=1,
        )
        frame.pack(fill="both", expand=True, padx=14, pady=14)

        tk.Label(frame, text="Password Generator", font=(FONT_FAMILY, 12, "bold"), bg=COLOR_SURFACE, fg=COLOR_TEXT_PRIMARY).pack(anchor="w", pady=(0, 8))

        # Result field
        pwd_box = tk.Entry(
            frame,
            font=(FONT_MONO, 11, "bold"),
            bg=COLOR_INPUT,
            fg=COLOR_SUCCESS,
            insertbackground=COLOR_TEXT_PRIMARY,
            bd=1,
            relief="solid",
            highlightbackground=COLOR_BORDER,
            highlightthickness=1,
            justify="center",
        )
        pwd_box.pack(fill="x", pady=(0, 10), ipady=4)

        # Length selector
        len_row = tk.Frame(frame, bg=COLOR_SURFACE)
        len_row.pack(fill="x", pady=(0, 10))

        tk.Label(len_row, text="Length:", font=(FONT_FAMILY, 9), bg=COLOR_SURFACE, fg=COLOR_TEXT_MUTED).pack(side="left")
        len_var = tk.IntVar(value=16)
        len_spin = ttk.Spinbox(len_row, from_=8, to=64, textvariable=len_var, width=5)
        len_spin.pack(side="left", padx=(8, 0))

        # Strength readout
        gen_strength_lbl = tk.Label(frame, text="Strength: Very Strong", font=(FONT_FAMILY, 9, "bold"), bg=COLOR_SURFACE, fg=COLOR_SUCCESS)
        gen_strength_lbl.pack(anchor="w", pady=(0, 10))

        def generate_new():
            try:
                l = len_var.get()
                p = password_utils.generate_password(l)
                pwd_box.delete(0, tk.END)
                pwd_box.insert(0, p)
                st = password_utils.check_password_strength(p)
                gen_strength_lbl.config(text=f"Strength: {st['label']}")
            except Exception as e:
                gen_strength_lbl.config(text=f"Error: {e}")

        def copy_generated():
            val = pwd_box.get()
            if val:
                self.root.clipboard_clear()
                self.root.clipboard_append(val)
                self.root.update()
                copy_btn.config(text="Copied!")
                dialog.after(1500, lambda: copy_btn.config(text="Copy to Clipboard"))

        generate_new()

        btn_row = tk.Frame(frame, bg=COLOR_SURFACE)
        btn_row.pack(fill="x", pady=(4, 0))

        regen_btn = ttk.Button(btn_row, text="Regenerate", command=generate_new)
        regen_btn.pack(side="left", padx=(0, 6))

        copy_btn = ttk.Button(btn_row, text="Copy to Clipboard", style="Primary.TButton", command=copy_generated)
        copy_btn.pack(side="left", padx=(0, 6))

        close_btn = ttk.Button(btn_row, text="Close", command=close_generator)
        close_btn.pack(side="right")

    # ----------------------------------------------------------------------
    # 7. Delete Credential
    # ----------------------------------------------------------------------
    def handle_delete_credential(self):
        if self.selected_entry_id is None:
            return

        confirmed = messagebox.askyesno(
            "Confirm Deletion",
            "Delete this credential?\nThis action cannot be undone.",
            parent=self.root,
        )
        if not confirmed:
            return

        ok = vault.delete_credential(self.current_user_id, self.selected_entry_id)
        if ok:
            self.selected_entry_id = None
            self.refresh_credential_list()
        else:
            messagebox.showerror("Error", "Failed to delete credential.", parent=self.root)

    # ----------------------------------------------------------------------
    # 8. Show & Copy Password Actions
    # ----------------------------------------------------------------------
    def handle_show_password(self):
        if self.selected_entry_id is None:
            return

        password = vault.get_credential_password(
            self.current_user_id,
            self.selected_entry_id,
            self.current_encryption_key,
        )

        if password is None:
            messagebox.showerror("Error", "Failed to retrieve password.", parent=self.root)
            return

        messagebox.showinfo("Password", f"Password:\n{password}", parent=self.root)

    def handle_copy_password(self):
        if self.selected_entry_id is None:
            return

        password = vault.get_credential_password(
            self.current_user_id,
            self.selected_entry_id,
            self.current_encryption_key,
        )

        if password is None:
            messagebox.showerror("Error", "Failed to retrieve password.", parent=self.root)
            return

        self.root.clipboard_clear()
        self.root.clipboard_append(password)
        self.root.update()
        messagebox.showinfo("Success", "Password copied to clipboard.", parent=self.root)

    # ----------------------------------------------------------------------
    # 9. Backup & Restore Actions
    # ----------------------------------------------------------------------
    def handle_backup(self):
        if self.current_user_id is None or self.current_encryption_key is None:
            return

        file_path = filedialog.asksaveasfilename(
            title="Backup Vault",
            defaultextension=".pmv",
            filetypes=[("Onesium Vault Backup", "*.pmv"), ("All Files", "*.*")],
            initialfile="onesium_vault_backup.pmv",
            parent=self.root,
        )
        if not file_path:
            return

        try:
            ok = vault.backup_user_vault(
                self.current_user_id,
                self.current_encryption_key,
                file_path,
            )
        except Exception:
            ok = False

        if ok:
            messagebox.showinfo("Success", "Vault backup created successfully.", parent=self.root)
        else:
            messagebox.showerror("Error", "Failed to create vault backup.", parent=self.root)

    def handle_restore(self):
        if self.current_user_id is None or self.current_encryption_key is None:
            return

        file_path = filedialog.askopenfilename(
            title="Restore Vault",
            filetypes=[("Onesium Vault Backup", "*.pmv"), ("All Files", "*.*")],
            parent=self.root,
        )
        if not file_path:
            return

        try:
            ok = vault.restore_user_vault(
                self.current_user_id,
                self.current_encryption_key,
                file_path,
            )
        except Exception:
            ok = False

        if ok:
            messagebox.showinfo("Success", "Vault restored successfully.", parent=self.root)
            self.refresh_credential_list()
        else:
            messagebox.showerror(
                "Error",
                "Failed to restore vault backup. File may be invalid, corrupted, or created with a different key.",
                parent=self.root,
            )

    # ----------------------------------------------------------------------
    # 10. Auto-Lock Timer Management
    # ----------------------------------------------------------------------
    def reset_auto_lock_timer(self, event=None):
        """Resets the auto-lock countdown timer on user activity while authenticated."""
        if self.current_user_id is None:
            return
        if self.auto_lock_job is not None:
            self.root.after_cancel(self.auto_lock_job)
        self.auto_lock_job = self.root.after(AUTO_LOCK_MS, self.handle_auto_lock)

    def cancel_auto_lock_timer(self):
        """Cancels any running auto-lock countdown."""
        if self.auto_lock_job is not None:
            self.root.after_cancel(self.auto_lock_job)
            self.auto_lock_job = None

    def _clear_session_state(self):
        """Clears active dialogs, in-memory credentials, displayed metadata, and clipboard."""
        self.cancel_auto_lock_timer()

        if self.active_dialog and self.active_dialog.winfo_exists():
            self.active_dialog.destroy()
        self.active_dialog = None

        self.current_user_id = None
        self.current_encryption_key = None
        self.current_username = None
        self.selected_entry_id = None
        self.displayed_entries = []
        self.row_widgets = {}
        self._total_credential_count = 0
        self._last_search_query = ""

        try:
            self.root.clipboard_clear()
        except Exception:
            pass

    def handle_auto_lock(self):
        """Locks the session upon inactivity timeout."""
        self._clear_session_state()

        self.show_login_screen(
            initial_message="Session locked due to inactivity. Please login again.",
            is_success=False,
        )

    # ----------------------------------------------------------------------
    # 11. Logout Handling
    # ----------------------------------------------------------------------
    def handle_logout(self):
        self._clear_session_state()

        self.show_login_screen(
            initial_message="You have been logged out.",
            is_success=True,
        )


def start_app(root=None):
    """Entry helper to launch GUI application."""
    if root is None:
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        root = ctk.CTk()
    app = PasswordManagerApp(root)
    return app
