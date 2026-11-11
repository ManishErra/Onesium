import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, font as tkfont
from datetime import datetime
import hashlib
import secrets
import auth
import vault
import password_utils

# Configure CustomTkinter appearance (must precede any CTk widget creation)
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

AUTO_LOCK_MS = 5 * 60 * 1000  # 5 minutes in milliseconds
CLIPBOARD_CLEAR_MS = 30 * 1000  # 30 seconds automatic clipboard clear timeout

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
MASKED_PASSWORD = "\u2022" * 12

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
    "back": "\uE72B",
    "edit": "\uE70F",
    "delete": "\uE74D",
    "copy": "\uE8C8",
    "eye": "\uE7B3",
    "hide": "\uED1A",
    "check": "\uE73E",
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
    "back": "\u2190",
    "edit": "\u270E",
    "delete": "\U0001f5d1",
    "copy": "\u2398",
    "eye": "\U0001f441",
    "hide": "\u2715",
    "check": "\u2713",
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


def _format_detail_timestamp(timestamp_str):
    """Formats an ISO/SQLite timestamp with time for credential details metadata."""
    if not timestamp_str:
        return "Unavailable"
    raw = str(timestamp_str).strip()
    for fmt, out_fmt in (("%Y-%m-%d %H:%M:%S", "%b %d, %Y  %H:%M"), ("%Y-%m-%d", "%b %d, %Y")):
        try:
            dt = datetime.strptime(raw[:19], fmt)
            return dt.strftime(out_fmt)
        except ValueError:
            continue
    return raw[:19]


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

    def __init__(self, root, startup_notice="", startup_notice_is_success=False):
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
        self._clipboard_clear_job = None
        self._clipboard_expected_digest = None

        # Dashboard view state (never stores plaintext passwords)
        self.row_widgets = {}
        self.displayed_entries = []
        self._total_credential_count = 0
        self._last_search_query = ""
        self._list_canvas = None
        self._list_canvas_window = None
        self._dashboard_main_area = None
        self._vault_list_view = None
        self._details_view = None
        self._details_entry_id = None
        self._details_password_revealed = False
        self._details_feedback_job = None

        # Bind user activity to reset auto-lock timer & single global wheel handler
        self.root.bind_all("<Key>", self.reset_auto_lock_timer)
        self.root.bind_all("<Button>", self.reset_auto_lock_timer)
        self.root.bind_all("<MouseWheel>", self._on_dashboard_mousewheel)

        # Container frame for switching views (CTkFrame replaces ttk.Frame)
        self.container = ctk.CTkFrame(self.root, corner_radius=0, fg_color=COLOR_BG)
        self.container.pack(fill="both", expand=True)

        # Centre window on screen before showing first view
        center_window(self.root, 460, 560)

        self.show_login_screen(
            initial_message=startup_notice,
            is_success=startup_notice_is_success,
        )

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
        if self._details_feedback_job is not None:
            try:
                self.root.after_cancel(self._details_feedback_job)
            except tk.TclError:
                pass
            self._details_feedback_job = None
        self._mask_details_password()
        self._dashboard_main_area = None
        self._vault_list_view = None
        self._details_view = None
        self._details_entry_id = None
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
            self.reg_confirm_entry.delete(0, tk.END)
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
            self.reg_password_entry.delete(0, tk.END)
            self.reg_confirm_entry.delete(0, tk.END)
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
            command=self._on_nav_vault_clicked,
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
        self._dashboard_main_area = ctk.CTkFrame(parent, fg_color=COLOR_BG, corner_radius=0)
        self._dashboard_main_area.pack(side="left", fill="both", expand=True, padx=24, pady=20)

        self._vault_list_view = ctk.CTkFrame(self._dashboard_main_area, fg_color=COLOR_BG, corner_radius=0)
        self._vault_list_view.pack(fill="both", expand=True)
        main_area = self._vault_list_view

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
            text=_truncate_text(site_name, 38),
            font=(FONT_FAMILY, 12, "bold"),
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w",
        )
        site_lbl.pack(anchor="w")

        user_lbl = ctk.CTkLabel(
            meta_box,
            text=_truncate_text(username_field, 44),
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
        date_lbl.grid(row=0, column=2, padx=(8, 8))

        # Column 3 & 4: Compact icon-only Edit and Delete actions (isolated from row click)
        edit_btn = ctk.CTkButton(
            card,
            text=self._icon_glyph("edit"),
            font=self._icon_font_tuple(13),
            width=30,
            height=30,
            corner_radius=6,
            fg_color="transparent",
            hover_color=COLOR_BORDER,
            text_color=COLOR_TEXT_MUTED,
            command=lambda eid=entry_id: self.open_edit_dialog(eid),
        )
        edit_btn.grid(row=0, column=3, padx=(0, 4))
        _ToolTip(edit_btn, "Edit credential")
        edit_btn.bind("<Enter>", lambda _e: edit_btn.configure(text_color=COLOR_TEXT_PRIMARY), add="+")
        edit_btn.bind("<Leave>", lambda _e: edit_btn.configure(text_color=COLOR_TEXT_MUTED), add="+")

        delete_btn = ctk.CTkButton(
            card,
            text=self._icon_glyph("delete"),
            font=self._icon_font_tuple(13),
            width=30,
            height=30,
            corner_radius=6,
            fg_color="transparent",
            hover_color="#3B1A22",
            text_color=COLOR_TEXT_MUTED,
            command=lambda eid=entry_id: self.handle_delete_credential(eid),
        )
        delete_btn.grid(row=0, column=4, padx=(0, 4))
        _ToolTip(delete_btn, "Delete credential")
        delete_btn.bind("<Enter>", lambda _e: delete_btn.configure(text_color=COLOR_DANGER), add="+")
        delete_btn.bind("<Leave>", lambda _e: delete_btn.configure(text_color=COLOR_TEXT_MUTED), add="+")

        # Column 5: Subtle chevron affordance to open details
        chevron_lbl = ctk.CTkLabel(
            card,
            text=self._icon_glyph("chevron"),
            font=self._icon_font_tuple(11),
            text_color=COLOR_PRIMARY if is_selected else COLOR_TEXT_MUTED,
            width=18,
        )
        chevron_lbl.grid(row=0, column=5, padx=(0, 12))
        _ToolTip(chevron_lbl, "Open details")

        # Store metadata-only widget references (never store passwords)
        self.row_widgets[entry_id] = {
            "card": card,
            "icon_tile": icon_tile,
            "edit_btn": edit_btn,
            "delete_btn": delete_btn,
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

        # Bind row-click navigation only on non-action-button elements
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

    def _on_nav_vault_clicked(self):
        """Returns to the vault list from details (if open) and clears any active search."""
        self.close_credential_details()
        self.clear_search()

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
        """Selects a credential row and opens its dedicated credential details view."""
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
        """Opens the dedicated in-window credential details view (without decrypting)."""
        self.open_credential_details(entry_id)

    # ----------------------------------------------------------------------
    # 3B. Credential Details View  (CustomTkinter, Zero-Auto-Decrypt)
    # ----------------------------------------------------------------------
    def _find_user_credential(self, entry_id):
        """Returns sqlite3.Row metadata for entry_id scoped strictly to current_user_id."""
        if self.current_user_id is None or entry_id is None:
            return None
        for entry in vault.get_credentials(self.current_user_id):
            if entry["entry_id"] == entry_id:
                return entry
        return None

    def open_credential_details(self, entry_id):
        """
        Displays the dedicated credential details screen inside the main application.
        Password remains masked by default and is never decrypted when opening details.
        """
        if self._dashboard_main_area is None or not self._dashboard_main_area.winfo_exists():
            return

        target = self._find_user_credential(entry_id)
        if target is None:
            return

        # Tear down any prior details view and ensure password display is cleared
        self._mask_details_password()
        if self._details_feedback_job is not None:
            try:
                self.root.after_cancel(self._details_feedback_job)
            except tk.TclError:
                pass
            self._details_feedback_job = None
        if self._details_view is not None and self._details_view.winfo_exists():
            self._details_view.destroy()

        self._details_entry_id = entry_id
        self._details_password_revealed = False

        if self._vault_list_view is not None and self._vault_list_view.winfo_exists():
            self._vault_list_view.pack_forget()

        view = ctk.CTkFrame(self._dashboard_main_area, fg_color=COLOR_BG, corner_radius=0)
        view.pack(fill="both", expand=True)
        self._details_view = view

        site_name = target["site_name"]
        username_field = target["username_field"]
        notes = (target["notes"] or "").strip()
        created_at = target["created_at"]
        updated_at = target["updated_at"]

        # ---- Top Bar: Back to Vault + Edit / Delete ----
        top_bar = ctk.CTkFrame(view, fg_color="transparent", corner_radius=0)
        top_bar.pack(fill="x", pady=(0, 10))

        back_btn_wrap = ctk.CTkFrame(
            top_bar,
            height=34,
            corner_radius=8,
            fg_color=COLOR_SURFACE,
            border_width=1,
            border_color=COLOR_BORDER,
            cursor="hand2",
        )
        back_btn_wrap.pack(side="left")

        back_inner = ctk.CTkFrame(back_btn_wrap, fg_color="transparent", corner_radius=0)
        back_inner.pack(padx=12, pady=6)

        back_icon = ctk.CTkLabel(
            back_inner,
            text=self._icon_glyph("back"),
            font=self._icon_font_tuple(12),
            text_color=COLOR_TEXT_SECONDARY,
            fg_color=COLOR_SURFACE,
        )
        back_icon.pack(side="left", padx=(0, 6))

        back_lbl = ctk.CTkLabel(
            back_inner,
            text="Back to Vault",
            font=(FONT_FAMILY, 11, "bold"),
            text_color=COLOR_TEXT_PRIMARY,
            fg_color=COLOR_SURFACE,
        )
        back_lbl.pack(side="left")

        def _back_enter(_e=None):
            back_btn_wrap.configure(fg_color=COLOR_SURFACE_ELEVATED)
            back_icon.configure(fg_color=COLOR_SURFACE_ELEVATED, text_color=COLOR_TEXT_PRIMARY)
            back_lbl.configure(fg_color=COLOR_SURFACE_ELEVATED)

        def _back_leave(_e=None):
            try:
                px, py = back_btn_wrap.winfo_pointerxy()
                bx, by = back_btn_wrap.winfo_rootx(), back_btn_wrap.winfo_rooty()
                if bx <= px <= bx + back_btn_wrap.winfo_width() and by <= py <= by + back_btn_wrap.winfo_height():
                    return
            except tk.TclError:
                return
            back_btn_wrap.configure(fg_color=COLOR_SURFACE)
            back_icon.configure(fg_color=COLOR_SURFACE, text_color=COLOR_TEXT_SECONDARY)
            back_lbl.configure(fg_color=COLOR_SURFACE)

        for w in (back_btn_wrap, back_inner, back_icon, back_lbl):
            w.configure(cursor="hand2")
            w.bind("<Enter>", _back_enter, add="+")
            w.bind("<Leave>", _back_leave, add="+")
            w.bind("<Button-1>", lambda _e: self.close_credential_details(), add="+")
        back_btn_wrap.invoke = self.close_credential_details
        self.details_back_btn = back_btn_wrap
        _ToolTip(back_btn_wrap, "Return to vault list")

        # Right-side Edit & Delete buttons
        actions_right = ctk.CTkFrame(top_bar, fg_color="transparent", corner_radius=0)
        actions_right.pack(side="right")

        self.details_edit_btn = ctk.CTkButton(
            actions_right,
            text="Edit",
            width=76,
            height=34,
            corner_radius=8,
            fg_color=COLOR_SURFACE,
            hover_color=COLOR_SURFACE_ELEVATED,
            border_width=1,
            border_color=COLOR_BORDER,
            text_color=COLOR_TEXT_PRIMARY,
            font=(FONT_FAMILY, 11, "bold"),
            command=lambda eid=entry_id: self.open_edit_dialog(eid),
        )
        self.details_edit_btn.pack(side="left", padx=(0, 8))
        _ToolTip(self.details_edit_btn, "Edit this credential")

        self.details_delete_btn = ctk.CTkButton(
            actions_right,
            text="Delete",
            width=82,
            height=34,
            corner_radius=8,
            fg_color=COLOR_SURFACE,
            hover_color="#3B1A22",
            border_width=1,
            border_color=COLOR_BORDER,
            text_color=COLOR_DANGER,
            font=(FONT_FAMILY, 11, "bold"),
            command=lambda eid=entry_id: self.handle_delete_credential(eid),
        )
        self.details_delete_btn.pack(side="left")
        _ToolTip(self.details_delete_btn, "Delete this credential")

        # ---- Identity Header ----
        id_row = ctk.CTkFrame(view, fg_color="transparent", corner_radius=0)
        id_row.pack(fill="x", pady=(0, 10))

        clean_site = (site_name or "").strip()
        first_char = clean_site[0].upper() if clean_site and clean_site[0].isalnum() else None

        icon_badge = ctk.CTkFrame(
            id_row,
            width=46,
            height=46,
            corner_radius=10,
            fg_color=COLOR_SURFACE_ELEVATED,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        icon_badge.pack(side="left", padx=(0, 14))
        icon_badge.pack_propagate(False)

        if first_char:
            ctk.CTkLabel(
                icon_badge,
                text=first_char,
                font=(FONT_FAMILY, 18, "bold"),
                text_color=COLOR_PRIMARY,
                fg_color="transparent",
            ).pack(expand=True)
        else:
            ctk.CTkLabel(
                icon_badge,
                text=self._icon_glyph("globe"),
                font=self._icon_font_tuple(18),
                text_color=COLOR_TEXT_SECONDARY,
                fg_color="transparent",
            ).pack(expand=True)

        id_meta = ctk.CTkFrame(id_row, fg_color="transparent", corner_radius=0)
        id_meta.pack(side="left", fill="x", expand=True)

        self.details_site_title = ctk.CTkLabel(
            id_meta,
            text=site_name,
            font=(FONT_FAMILY, 19, "bold"),
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w",
        )
        self.details_site_title.pack(anchor="w")

        ctk.CTkLabel(
            id_meta,
            text="\u25cf  Stored locally  \u2022  Fernet encrypted",
            font=(FONT_FAMILY, 10),
            text_color=COLOR_SUCCESS,
            anchor="w",
        ).pack(anchor="w", pady=(2, 0))

        # ---- Main Details Card ----
        card = ctk.CTkFrame(
            view,
            corner_radius=12,
            fg_color=COLOR_SURFACE,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        card.pack(fill="both", expand=True)

        ci = ctk.CTkFrame(card, fg_color="transparent", corner_radius=0)
        ci.pack(fill="both", expand=True, padx=22, pady=10)

        # Field 1: Website / Application Name
        ctk.CTkLabel(
            ci,
            text="WEBSITE / APPLICATION",
            font=(FONT_FAMILY, 9, "bold"),
            text_color=COLOR_TEXT_MUTED,
            height=16,
            anchor="w",
        ).pack(anchor="w", pady=(0, 2))

        self.details_site_value = ctk.CTkLabel(
            ci,
            text=site_name,
            font=(FONT_FAMILY, 13, "bold"),
            text_color=COLOR_TEXT_PRIMARY,
            height=22,
            anchor="w",
        )
        self.details_site_value.pack(anchor="w", pady=(0, 10))

        # Field 2: Username / Identifier + Copy Username button
        ctk.CTkLabel(
            ci,
            text="USERNAME / IDENTIFIER",
            font=(FONT_FAMILY, 9, "bold"),
            text_color=COLOR_TEXT_MUTED,
            height=16,
            anchor="w",
        ).pack(anchor="w", pady=(0, 4))

        user_box = ctk.CTkFrame(
            ci,
            height=38,
            corner_radius=8,
            fg_color=COLOR_INPUT,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        user_box.pack(fill="x", pady=(0, 8))
        user_box.pack_propagate(False)

        self.details_username_value = ctk.CTkLabel(
            user_box,
            text=username_field,
            font=(FONT_FAMILY, 12),
            text_color=COLOR_TEXT_PRIMARY,
            fg_color=COLOR_INPUT,
            anchor="w",
        )
        self.details_username_value.pack(side="left", fill="x", expand=True, padx=(12, 6), pady=4)

        self.details_copy_user_btn = ctk.CTkButton(
            user_box,
            text=self._icon_glyph("copy"),
            font=self._icon_font_tuple(13),
            width=30,
            height=28,
            corner_radius=6,
            fg_color=COLOR_INPUT,
            hover_color=COLOR_SURFACE_ELEVATED,
            text_color=COLOR_TEXT_SECONDARY,
            command=lambda u=username_field: self.copy_details_username(u),
        )
        self.details_copy_user_btn.pack(side="right", padx=(0, 6), pady=4)
        _ToolTip(self.details_copy_user_btn, "Copy username")

        # Field 3: Password (Masked by Default, Reveal/Hide + Copy)
        pwd_header = ctk.CTkFrame(ci, fg_color="transparent", corner_radius=0)
        pwd_header.pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(
            pwd_header,
            text="PASSWORD",
            font=(FONT_FAMILY, 9, "bold"),
            text_color=COLOR_TEXT_MUTED,
            height=16,
            anchor="w",
        ).pack(side="left")

        self.details_feedback_label = ctk.CTkLabel(
            pwd_header,
            text="",
            font=(FONT_FAMILY, 10, "bold"),
            text_color=COLOR_SUCCESS,
            height=16,
            anchor="e",
        )
        self.details_feedback_label.pack(side="right")

        pwd_box = ctk.CTkFrame(
            ci,
            height=38,
            corner_radius=8,
            fg_color=COLOR_INPUT,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        pwd_box.pack(fill="x", pady=(0, 8))
        pwd_box.pack_propagate(False)

        self.details_password_label = ctk.CTkLabel(
            pwd_box,
            text=MASKED_PASSWORD,
            font=(FONT_MONO, 13),
            text_color=COLOR_TEXT_SECONDARY,
            fg_color=COLOR_INPUT,
            anchor="w",
        )
        self.details_password_label.pack(side="left", fill="x", expand=True, padx=(12, 6), pady=4)

        self.details_copy_pw_btn = ctk.CTkButton(
            pwd_box,
            text=self._icon_glyph("copy"),
            font=self._icon_font_tuple(13),
            width=30,
            height=28,
            corner_radius=6,
            fg_color=COLOR_INPUT,
            hover_color=COLOR_SURFACE_ELEVATED,
            text_color=COLOR_TEXT_SECONDARY,
            command=self.copy_details_password,
        )
        self.details_copy_pw_btn.pack(side="right", padx=(2, 6), pady=4)
        _ToolTip(self.details_copy_pw_btn, "Copy password")

        self.details_toggle_pw_btn = ctk.CTkButton(
            pwd_box,
            text=self._icon_glyph("eye"),
            font=self._icon_font_tuple(13),
            width=30,
            height=28,
            corner_radius=6,
            fg_color=COLOR_INPUT,
            hover_color=COLOR_SURFACE_ELEVATED,
            text_color=COLOR_TEXT_SECONDARY,
            command=self.toggle_details_password,
        )
        self.details_toggle_pw_btn.pack(side="right", padx=(4, 2), pady=4)
        self._details_toggle_tooltip = _ToolTip(self.details_toggle_pw_btn, "Show password")

        # Field 4: Notes (read-only)
        ctk.CTkLabel(
            ci,
            text="NOTES",
            font=(FONT_FAMILY, 9, "bold"),
            text_color=COLOR_TEXT_MUTED,
            height=16,
            anchor="w",
        ).pack(anchor="w", pady=(0, 4))

        notes_box = ctk.CTkTextbox(
            ci,
            height=54,
            corner_radius=8,
            fg_color=COLOR_INPUT,
            border_width=1,
            border_color=COLOR_BORDER,
            text_color=COLOR_TEXT_PRIMARY if notes else COLOR_TEXT_MUTED,
            font=(FONT_FAMILY, 11),
            wrap="word",
        )
        notes_box.pack(fill="x", pady=(0, 10))
        notes_box.insert("1.0", notes if notes else "No notes added.")
        notes_box.configure(state="disabled")
        self.details_notes_box = notes_box

        # Field 5: Created & Last Updated Metadata Footer
        ctk.CTkFrame(ci, height=1, fg_color=COLOR_BORDER, corner_radius=0).pack(
            fill="x", pady=(0, 8)
        )

        dates_row = ctk.CTkFrame(ci, fg_color="transparent", corner_radius=0)
        dates_row.pack(fill="x")
        dates_row.grid_columnconfigure(0, weight=1)
        dates_row.grid_columnconfigure(1, weight=1)

        created_col = ctk.CTkFrame(dates_row, fg_color="transparent", corner_radius=0)
        created_col.grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            created_col,
            text="CREATED",
            font=(FONT_FAMILY, 8, "bold"),
            text_color=COLOR_TEXT_MUTED,
            height=14,
        ).pack(anchor="w")
        self.details_created_value = ctk.CTkLabel(
            created_col,
            text=_format_detail_timestamp(created_at),
            font=(FONT_FAMILY, 10),
            text_color=COLOR_TEXT_SECONDARY,
            height=18,
        )
        self.details_created_value.pack(anchor="w")

        updated_col = ctk.CTkFrame(dates_row, fg_color="transparent", corner_radius=0)
        updated_col.grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(
            updated_col,
            text="LAST UPDATED",
            font=(FONT_FAMILY, 8, "bold"),
            text_color=COLOR_TEXT_MUTED,
            height=14,
        ).pack(anchor="w")
        self.details_updated_value = ctk.CTkLabel(
            updated_col,
            text=_format_detail_timestamp(updated_at),
            font=(FONT_FAMILY, 10),
            text_color=COLOR_TEXT_SECONDARY,
            height=18,
        )
        self.details_updated_value.pack(anchor="w")

    def _mask_details_password(self):
        """Masks the details password display and clears any revealed plaintext from the label."""
        self._details_password_revealed = False
        if hasattr(self, "details_password_label") and self.details_password_label is not None:
            try:
                if self.details_password_label.winfo_exists():
                    self.details_password_label.configure(
                        text=MASKED_PASSWORD,
                        font=(FONT_MONO, 13),
                        text_color=COLOR_TEXT_SECONDARY,
                    )
            except tk.TclError:
                pass
        if hasattr(self, "details_toggle_pw_btn") and self.details_toggle_pw_btn is not None:
            try:
                if self.details_toggle_pw_btn.winfo_exists():
                    self.details_toggle_pw_btn.configure(text=self._icon_glyph("eye"))
            except tk.TclError:
                pass
        if hasattr(self, "_details_toggle_tooltip") and self._details_toggle_tooltip is not None:
            self._details_toggle_tooltip.text = "Show password"

    def _show_details_feedback(self, message, color=COLOR_SUCCESS):
        """Displays brief inline feedback in the details view without using messagebox."""
        if self._details_feedback_job is not None:
            try:
                self.root.after_cancel(self._details_feedback_job)
            except tk.TclError:
                pass
            self._details_feedback_job = None

        if hasattr(self, "details_feedback_label") and self.details_feedback_label is not None:
            try:
                if self.details_feedback_label.winfo_exists():
                    self.details_feedback_label.configure(text=message, text_color=color)
                    self._details_feedback_job = self.root.after(1500, self._clear_details_feedback)
            except tk.TclError:
                pass

    def _clear_details_feedback(self):
        self._details_feedback_job = None
        if hasattr(self, "details_feedback_label") and self.details_feedback_label is not None:
            try:
                if self.details_feedback_label.winfo_exists():
                    self.details_feedback_label.configure(text="")
            except tk.TclError:
                pass

    def toggle_details_password(self):
        """Explicitly decrypts and reveals only the active entry's password, or masks it again."""
        if self._details_entry_id is None:
            return
        if self._details_password_revealed:
            self._mask_details_password()
            return

        password = vault.get_credential_password(
            self.current_user_id,
            self._details_entry_id,
            self.current_encryption_key,
        )
        if password is None:
            self._show_details_feedback("Failed to retrieve password.", color=COLOR_DANGER)
            return

        if hasattr(self, "details_password_label") and self.details_password_label.winfo_exists():
            self.details_password_label.configure(
                text=password,
                font=(FONT_MONO, 13, "bold"),
                text_color=COLOR_TEXT_PRIMARY,
            )
            self._details_password_revealed = True
            if hasattr(self, "details_toggle_pw_btn") and self.details_toggle_pw_btn.winfo_exists():
                self.details_toggle_pw_btn.configure(text=self._icon_glyph("hide"))
            if hasattr(self, "_details_toggle_tooltip") and self._details_toggle_tooltip is not None:
                self._details_toggle_tooltip.text = "Hide password"

    def copy_details_password(self):
        """Explicitly retrieves and copies only the active entry's password to clipboard."""
        if self._details_entry_id is None:
            return
        self.handle_copy_password(self._details_entry_id)

    def copy_details_username(self, username_text):
        """Copies the displayed username/identifier to clipboard with inline feedback."""
        if not username_text:
            return
        self._cancel_clipboard_clear_timer()
        self.root.clipboard_clear()
        self.root.clipboard_append(username_text)
        self.root.update()
        self._show_details_feedback("Username copied to clipboard", color=COLOR_SUCCESS)

    def close_credential_details(self):
        """Masks/clears password state, closes details view, and returns to the vault list."""
        self._mask_details_password()
        if self._details_feedback_job is not None:
            try:
                self.root.after_cancel(self._details_feedback_job)
            except tk.TclError:
                pass
            self._details_feedback_job = None

        if self._details_view is not None:
            try:
                if self._details_view.winfo_exists():
                    self._details_view.destroy()
            except tk.TclError:
                pass
            self._details_view = None

        self._details_entry_id = None
        if self._vault_list_view is not None:
            try:
                if self._vault_list_view.winfo_exists() and not self._vault_list_view.winfo_manager():
                    self._vault_list_view.pack(fill="both", expand=True)
            except tk.TclError:
                pass

    def update_action_button_states(self):
        """Retained for compatibility; dashboard row selection manages visual state."""
        return None

    # ----------------------------------------------------------------------
    # 4 & 5. Add / Edit Credential Dialogs  (CustomTkinter)
    # ----------------------------------------------------------------------
    def _open_credential_dialog(self, mode="add", target=None):
        """
        Shared CustomTkinter modal for adding or editing a credential.
        Editing never decrypts or reads the existing password.
        """
        is_edit = mode == "edit"
        if is_edit and target is None:
            return

        if self.active_dialog and self.active_dialog.winfo_exists():
            self.active_dialog.destroy()

        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Onesium — Edit Credential" if is_edit else "Onesium — Add Credential")
        dialog.configure(fg_color=COLOR_BG)
        dialog.transient(self.root)
        dialog.grab_set()
        self.active_dialog = dialog
        dlg_h = 600 if is_edit else 575
        center_window(dialog, 450, dlg_h, self.root)
        dialog.resizable(False, False)

        def close_dialog():
            dialog.destroy()
            self.active_dialog = None

        dialog.protocol("WM_DELETE_WINDOW", close_dialog)

        outer = ctk.CTkFrame(dialog, fg_color=COLOR_BG, corner_radius=0)
        outer.pack(fill="both", expand=True, padx=22, pady=18)

        # Header
        ctk.CTkLabel(
            outer,
            text="Edit Credential" if is_edit else "Add Credential",
            font=(FONT_FAMILY, 17, "bold"),
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w",
        ).pack(anchor="w")
        ctk.CTkLabel(
            outer,
            text=(
                "Update credential metadata and set a replacement password."
                if is_edit
                else "Store credentials encrypted locally on this device."
            ),
            font=(FONT_FAMILY, 10),
            text_color=COLOR_TEXT_SECONDARY,
            anchor="w",
        ).pack(anchor="w", pady=(2, 12))

        card = ctk.CTkFrame(
            outer,
            corner_radius=12,
            fg_color=COLOR_SURFACE,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        card.pack(fill="both", expand=True)

        ci = ctk.CTkFrame(card, fg_color="transparent", corner_radius=0)
        ci.pack(fill="both", expand=True, padx=18, pady=16)

        # Field 1: Site / App
        ctk.CTkLabel(
            ci, text="Site / App",
            font=(FONT_FAMILY, 10, "bold"),
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(anchor="w", pady=(0, 4))
        site_entry = ctk.CTkEntry(
            ci,
            height=36,
            corner_radius=8,
            fg_color=COLOR_INPUT,
            border_color=COLOR_BORDER,
            text_color=COLOR_TEXT_PRIMARY,
        )
        if is_edit:
            site_entry.insert(0, target["site_name"])
        site_entry.pack(fill="x", pady=(0, 10))
        site_entry.focus()

        # Field 2: Username / Identifier
        ctk.CTkLabel(
            ci, text="Username / Identifier",
            font=(FONT_FAMILY, 10, "bold"),
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(anchor="w", pady=(0, 4))
        user_entry = ctk.CTkEntry(
            ci,
            height=36,
            corner_radius=8,
            fg_color=COLOR_INPUT,
            border_color=COLOR_BORDER,
            text_color=COLOR_TEXT_PRIMARY,
        )
        if is_edit:
            user_entry.insert(0, target["username_field"])
        user_entry.pack(fill="x", pady=(0, 10))

        # Field 3: Password Header + Show/Hide + Generate
        pwd_header = ctk.CTkFrame(ci, fg_color="transparent", corner_radius=0)
        pwd_header.pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(
            pwd_header,
            text="New Password" if is_edit else "Password",
            font=(FONT_FAMILY, 10, "bold"),
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(side="left")

        pwd_var = tk.StringVar()
        _pw_shown = [False]

        def toggle_dlg_pw():
            if _pw_shown[0]:
                pwd_entry.configure(show="*")
                eye_btn.configure(text="Show")
                _pw_shown[0] = False
            else:
                pwd_entry.configure(show="")
                eye_btn.configure(text="Hide")
                _pw_shown[0] = True

        def generate_pwd():
            gen = password_utils.generate_password()
            pwd_entry.delete(0, tk.END)
            pwd_entry.insert(0, gen)

        gen_btn = ctk.CTkButton(
            pwd_header,
            text="Generate",
            width=74,
            height=24,
            corner_radius=5,
            fg_color=COLOR_SURFACE_ELEVATED,
            hover_color=COLOR_BORDER,
            text_color=COLOR_TEXT_PRIMARY,
            font=(FONT_FAMILY, 9, "bold"),
            command=generate_pwd,
        )
        gen_btn.pack(side="right")

        eye_btn = ctk.CTkButton(
            pwd_header,
            text="Show",
            width=54,
            height=24,
            corner_radius=5,
            fg_color=COLOR_SURFACE_ELEVATED,
            hover_color=COLOR_BORDER,
            text_color=COLOR_TEXT_SECONDARY,
            font=(FONT_FAMILY, 9),
            command=toggle_dlg_pw,
        )
        eye_btn.pack(side="right", padx=(0, 6))

        pwd_entry = ctk.CTkEntry(
            ci,
            textvariable=pwd_var,
            height=36,
            corner_radius=8,
            fg_color=COLOR_INPUT,
            border_color=COLOR_BORDER,
            text_color=COLOR_TEXT_PRIMARY,
        )
        pwd_entry.pack(fill="x", pady=(0, 4))
        pwd_entry.configure(show="*")

        if is_edit:
            ctk.CTkLabel(
                ci,
                text="Existing password is never decrypted. Enter a replacement to save.",
                font=(FONT_FAMILY, 9),
                text_color=COLOR_TEXT_MUTED,
            ).pack(anchor="w", pady=(0, 2))

        strength_label = ctk.CTkLabel(
            ci,
            text="Strength: Very Weak",
            font=(FONT_FAMILY, 9, "bold"),
            text_color=COLOR_DANGER,
        )
        strength_label.pack(anchor="w", pady=(2, 1))

        common_warn_label = ctk.CTkLabel(
            ci,
            text="",
            font=(FONT_FAMILY, 9),
            text_color=COLOR_DANGER,
        )
        common_warn_label.pack(anchor="w", pady=(0, 6))

        def update_pwd_feedback(*_args):
            val = pwd_var.get()
            res = password_utils.check_password_strength(val)
            color = _STRENGTH_COLORS.get(res["label"], COLOR_TEXT_SECONDARY)
            strength_label.configure(text=f"Strength: {res['label']}", text_color=color)
            if password_utils.is_common_password(val):
                common_warn_label.configure(text="\u26a0  This is a commonly used password.")
            else:
                common_warn_label.configure(text="")

        pwd_var.trace_add("write", update_pwd_feedback)

        # Field 4: Notes
        ctk.CTkLabel(
            ci, text="Notes (Optional)",
            font=(FONT_FAMILY, 10, "bold"),
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(anchor="w", pady=(0, 4))
        notes_entry = ctk.CTkEntry(
            ci,
            height=36,
            corner_radius=8,
            fg_color=COLOR_INPUT,
            border_color=COLOR_BORDER,
            text_color=COLOR_TEXT_PRIMARY,
        )
        if is_edit:
            notes_entry.insert(0, target["notes"] or "")
        notes_entry.pack(fill="x", pady=(0, 8))

        status_label = ctk.CTkLabel(
            ci,
            text="",
            text_color=COLOR_DANGER,
            font=(FONT_FAMILY, 9),
            wraplength=360,
        )
        status_label.pack(pady=(0, 8))

        btn_row = ctk.CTkFrame(ci, fg_color="transparent", corner_radius=0)
        btn_row.pack(fill="x", pady=(2, 0))

        def save_credential():
            site_name = site_entry.get().strip()
            username = user_entry.get().strip()
            password = pwd_entry.get()
            notes = notes_entry.get().strip()

            if not site_name:
                status_label.configure(text="Site name cannot be empty.")
                return
            if not username:
                status_label.configure(text="Username cannot be empty.")
                return
            if not password:
                status_label.configure(text="Password cannot be empty.")
                return

            try:
                if is_edit:
                    ok = vault.update_credential(
                        user_id=self.current_user_id,
                        entry_id=target["entry_id"],
                        key=self.current_encryption_key,
                        site_name=site_name,
                        username=username,
                        password=password,
                        notes=notes,
                    )
                    if not ok:
                        status_label.configure(text="Failed to update credential.")
                        return
                else:
                    vault.add_credential(
                        user_id=self.current_user_id,
                        key=self.current_encryption_key,
                        site_name=site_name,
                        username=username,
                        password=password,
                        notes=notes,
                    )
            except (ValueError, TypeError) as e:
                status_label.configure(text=str(e))
                return

            editing_id = target["entry_id"] if is_edit else None
            was_viewing_details = (
                is_edit
                and self._details_view is not None
                and self._details_view.winfo_exists()
                and self._details_entry_id == editing_id
            )
            close_dialog()
            self.refresh_credential_list()
            if was_viewing_details and editing_id is not None:
                self.selected_entry_id = editing_id
                self.open_credential_details(editing_id)

        save_btn = ctk.CTkButton(
            btn_row,
            text="Save",
            height=38,
            width=120,
            corner_radius=8,
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            text_color="#FFFFFF",
            font=(FONT_FAMILY, 11, "bold"),
            command=save_credential,
        )
        save_btn.pack(side="left", padx=(0, 8))

        cancel_btn = ctk.CTkButton(
            btn_row,
            text="Cancel",
            height=38,
            width=100,
            corner_radius=8,
            fg_color=COLOR_SURFACE_ELEVATED,
            hover_color=COLOR_BORDER,
            border_width=1,
            border_color=COLOR_BORDER,
            text_color=COLOR_TEXT_PRIMARY,
            font=(FONT_FAMILY, 11),
            command=close_dialog,
        )
        cancel_btn.pack(side="left")

    def open_add_dialog(self):
        self._open_credential_dialog(mode="add")

    def open_edit_dialog(self, entry_id=None):
        target_id = entry_id if entry_id is not None else self.selected_entry_id
        if target_id is None:
            return
        target = self._find_user_credential(target_id)
        if target is None:
            return
        self._open_credential_dialog(mode="edit", target=target)

    # ----------------------------------------------------------------------
    # 6. Standalone Password Generator Tool Dialog  (CustomTkinter)
    # ----------------------------------------------------------------------
    def open_generator_dialog(self):
        """Opens a dedicated generator modal styled with the Onesium palette."""
        if self.active_dialog and self.active_dialog.winfo_exists():
            self.active_dialog.destroy()

        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Onesium — Password Generator")
        dialog.configure(fg_color=COLOR_BG)
        dialog.transient(self.root)
        dialog.grab_set()
        self.active_dialog = dialog
        center_window(dialog, 420, 320, self.root)
        dialog.resizable(False, False)

        def close_generator():
            dialog.destroy()
            self.active_dialog = None

        dialog.protocol("WM_DELETE_WINDOW", close_generator)

        card = ctk.CTkFrame(
            dialog,
            corner_radius=12,
            fg_color=COLOR_SURFACE,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        card.pack(fill="both", expand=True, padx=18, pady=18)

        ci = ctk.CTkFrame(card, fg_color="transparent", corner_radius=0)
        ci.pack(fill="both", expand=True, padx=18, pady=16)

        ctk.CTkLabel(
            ci,
            text="Password Generator",
            font=(FONT_FAMILY, 15, "bold"),
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w",
        ).pack(anchor="w", pady=(0, 12))

        pwd_box = ctk.CTkEntry(
            ci,
            height=42,
            corner_radius=8,
            fg_color=COLOR_INPUT,
            border_color=COLOR_BORDER,
            text_color=COLOR_SUCCESS,
            font=(FONT_MONO, 13, "bold"),
            justify="center",
        )
        pwd_box.pack(fill="x", pady=(0, 12))

        len_row = ctk.CTkFrame(ci, fg_color="transparent", corner_radius=0)
        len_row.pack(fill="x", pady=(0, 10))

        len_var = tk.IntVar(value=16)
        len_value_lbl = ctk.CTkLabel(
            len_row,
            text="Length: 16",
            font=(FONT_FAMILY, 10, "bold"),
            text_color=COLOR_TEXT_SECONDARY,
            width=76,
            anchor="w",
        )
        len_value_lbl.pack(side="left", padx=(0, 10))

        gen_strength_lbl = ctk.CTkLabel(
            ci,
            text="Strength: Very Strong",
            font=(FONT_FAMILY, 10, "bold"),
            text_color=COLOR_SUCCESS,
            anchor="w",
        )
        gen_strength_lbl.pack(anchor="w", pady=(0, 14))

        def generate_new(*_args):
            try:
                length = int(len_var.get())
                len_value_lbl.configure(text=f"Length: {length}")
                p = password_utils.generate_password(length)
                pwd_box.delete(0, tk.END)
                pwd_box.insert(0, p)
                st = password_utils.check_password_strength(p)
                color = _STRENGTH_COLORS.get(st["label"], COLOR_SUCCESS)
                gen_strength_lbl.configure(text=f"Strength: {st['label']}", text_color=color)
            except Exception as e:
                gen_strength_lbl.configure(text=f"Error: {e}", text_color=COLOR_DANGER)

        len_slider = ctk.CTkSlider(
            len_row,
            from_=8,
            to=64,
            number_of_steps=56,
            variable=len_var,
            button_color=COLOR_PRIMARY,
            button_hover_color=COLOR_PRIMARY_HOVER,
            progress_color=COLOR_PRIMARY,
            command=lambda _v: generate_new(),
        )
        len_slider.pack(side="left", fill="x", expand=True)

        def copy_generated():
            val = pwd_box.get()
            if val:
                self._copy_secret_to_clipboard(val)
                copy_btn.configure(text="Copied!")
                dialog.after(
                    1500,
                    lambda: copy_btn.configure(text="Copy to Clipboard")
                    if copy_btn.winfo_exists()
                    else None,
                )

        generate_new()

        btn_row = ctk.CTkFrame(ci, fg_color="transparent", corner_radius=0)
        btn_row.pack(fill="x", pady=(4, 0))

        regen_btn = ctk.CTkButton(
            btn_row,
            text="Regenerate",
            height=36,
            width=102,
            corner_radius=8,
            fg_color=COLOR_SURFACE_ELEVATED,
            hover_color=COLOR_BORDER,
            border_width=1,
            border_color=COLOR_BORDER,
            text_color=COLOR_TEXT_PRIMARY,
            font=(FONT_FAMILY, 10, "bold"),
            command=generate_new,
        )
        regen_btn.pack(side="left", padx=(0, 8))

        copy_btn = ctk.CTkButton(
            btn_row,
            text="Copy to Clipboard",
            height=36,
            width=142,
            corner_radius=8,
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            text_color="#FFFFFF",
            font=(FONT_FAMILY, 10, "bold"),
            command=copy_generated,
        )
        copy_btn.pack(side="left", padx=(0, 8))

        close_btn = ctk.CTkButton(
            btn_row,
            text="Close",
            height=36,
            width=76,
            corner_radius=8,
            fg_color=COLOR_SURFACE_ELEVATED,
            hover_color=COLOR_BORDER,
            border_width=1,
            border_color=COLOR_BORDER,
            text_color=COLOR_TEXT_PRIMARY,
            font=(FONT_FAMILY, 10),
            command=close_generator,
        )
        close_btn.pack(side="right")

    # ----------------------------------------------------------------------
    # 7. Delete Credential
    # ----------------------------------------------------------------------
    def handle_delete_credential(self, entry_id=None):
        target_id = entry_id if entry_id is not None else self.selected_entry_id
        if target_id is None:
            return

        site_label = "this credential"
        if target_id in self.row_widgets:
            site_label = f"'{self.row_widgets[target_id]['site_name']}'"
        else:
            target = self._find_user_credential(target_id)
            if target is not None:
                site_label = f"'{target['site_name']}'"

        confirmed = messagebox.askyesno(
            "Confirm Deletion",
            f"Delete {site_label}?\nThis action cannot be undone.",
            parent=self.root,
        )
        if not confirmed:
            return

        ok = vault.delete_credential(self.current_user_id, target_id)
        if ok:
            if self._details_entry_id == target_id or self._details_view is not None:
                self.close_credential_details()
            self.selected_entry_id = None
            self.refresh_credential_list()
        else:
            messagebox.showerror("Error", "Failed to delete credential.", parent=self.root)

    # ----------------------------------------------------------------------
    # 8. Copy Password Action & Safe Clipboard Auto-Clear
    # ----------------------------------------------------------------------
    def _cancel_clipboard_clear_timer(self):
        """Cancels any pending clipboard clear timeout and forgets the expected digest."""
        if self._clipboard_clear_job is not None:
            try:
                self.root.after_cancel(self._clipboard_clear_job)
            except tk.TclError:
                pass
            self._clipboard_clear_job = None
        self._clipboard_expected_digest = None

    def _copy_secret_to_clipboard(self, secret_text):
        """
        Copies a secret to the clipboard and schedules automatic clearing after
        CLIPBOARD_CLEAR_MS using a one-way SHA-256 digest (never retaining plaintext).
        """
        self._cancel_clipboard_clear_timer()
        self.root.clipboard_clear()
        self.root.clipboard_append(secret_text)
        self.root.update()
        self._clipboard_expected_digest = hashlib.sha256(secret_text.encode("utf-8")).digest()
        self._clipboard_clear_job = self.root.after(CLIPBOARD_CLEAR_MS, self._auto_clear_clipboard)

    def _auto_clear_clipboard(self):
        """Clears the clipboard only if its current contents still match the copied secret."""
        self._clipboard_clear_job = None
        expected = self._clipboard_expected_digest
        self._clipboard_expected_digest = None
        if expected is None:
            return
        try:
            current = self.root.clipboard_get()
        except tk.TclError:
            return
        current_digest = hashlib.sha256(current.encode("utf-8")).digest()
        if secrets.compare_digest(current_digest, expected):
            try:
                self.root.clipboard_clear()
                self.root.update()
            except tk.TclError:
                pass

    def handle_copy_password(self, entry_id=None):
        target_id = entry_id if entry_id is not None else self.selected_entry_id
        if target_id is None:
            return False

        password = vault.get_credential_password(
            self.current_user_id,
            target_id,
            self.current_encryption_key,
        )

        if password is None:
            if self._details_view is not None and self._details_view.winfo_exists():
                self._show_details_feedback("Failed to retrieve password.", color=COLOR_DANGER)
            return False

        self._copy_secret_to_clipboard(password)
        if self._details_view is not None and self._details_view.winfo_exists():
            self._show_details_feedback("Password copied (clears in 30s)", color=COLOR_SUCCESS)
        return True

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
        """Clears active dialogs, details view, in-memory credentials, metadata, and clipboard."""
        self.cancel_auto_lock_timer()
        self._cancel_clipboard_clear_timer()

        self._mask_details_password()
        if self._details_feedback_job is not None:
            try:
                self.root.after_cancel(self._details_feedback_job)
            except tk.TclError:
                pass
            self._details_feedback_job = None

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
        self._details_view = None
        self._details_entry_id = None
        self._details_password_revealed = False

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
