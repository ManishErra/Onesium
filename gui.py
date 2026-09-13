import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import auth
import vault
import password_utils

AUTO_LOCK_MS = 5 * 60 * 1000  # 5 minutes in milliseconds

# ---------------------------------------------------------------------------
# Onesium Design System - Precision Vault Palette
# ---------------------------------------------------------------------------
COLOR_BG = "#0F1117"              # Deep canvas background
COLOR_SURFACE = "#171B23"         # Cards, modal dialogs, panels, sidebar
COLOR_SURFACE_ELEVATED = "#202632"# Elevated surface, table headers, active items
COLOR_INPUT = "#0B0E14"           # Input field background
COLOR_BORDER = "#2A3140"          # 1px structural boundaries & outlines
COLOR_PRIMARY = "#2563EB"         # Primary blue interactive buttons
COLOR_PRIMARY_HOVER = "#1D4ED8"   # Primary button hover
COLOR_PRIMARY_ACTIVE = "#1E40AF"  # Primary button active
COLOR_ACCENT = "#3B82F6"          # Bright focus accent ring
COLOR_TEXT_PRIMARY = "#F3F4F6"    # High contrast primary text
COLOR_TEXT_SECONDARY = "#9CA3AF"  # Secondary field labels & captions
COLOR_TEXT_MUTED = "#6B7280"      # Placeholders, status, timestamps
COLOR_TEXT_DIM = "#6B7280"        # Dim text alias
COLOR_SUCCESS = "#10B981"         # Green for cryptographic strength & offline status
COLOR_WARNING = "#F59E0B"         # Yellow for moderate strength
COLOR_DANGER = "#EF4444"          # Red for errors & common password warnings

FONT_FAMILY = "Segoe UI"
FONT_MONO = "Consolas"


def apply_vault_theme(root):
    """Configures modern dark ttk styles for the Onesium desktop interface."""
    root.configure(bg=COLOR_BG)
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


class PasswordManagerApp:
    """
    GUI Presentation Layer for ONESIUM — The Credential Vault.
    Manages view transitions, vault dashboard, credential operations, and in-memory session credentials.
    """

    def __init__(self, root):
        self.root = root
        self.root.title("Onesium — The Credential Vault")
        self.root.geometry("480x480")
        self.root.resizable(False, False)

        apply_vault_theme(self.root)

        # In-memory session state (cleared on logout / auto-lock)
        self.current_user_id = None
        self.current_encryption_key = None
        self.current_username = None
        self.selected_entry_id = None
        self.active_dialog = None
        self.auto_lock_job = None

        # Bind user activity to reset auto-lock timer
        self.root.bind_all("<Key>", self.reset_auto_lock_timer)
        self.root.bind_all("<Button>", self.reset_auto_lock_timer)

        # Container frame for switching views
        self.container = ttk.Frame(self.root, padding=0)
        self.container.pack(fill="both", expand=True)

        self.show_login_screen()

    def clear_container(self):
        """Removes all child widgets from the container."""
        for widget in self.container.winfo_children():
            widget.destroy()

    def _toggle_show(self, entry, btn):
        """Toggles password masking between '*' and plain text."""
        if entry.cget("show") == "*":
            entry.config(show="")
            btn.config(text="Hide")
        else:
            entry.config(show="*")
            btn.config(text="Show")

    # ----------------------------------------------------------------------
    # 1. Login Screen
    # ----------------------------------------------------------------------
    def show_login_screen(self, initial_message="", is_success=False):
        self.root.geometry("460x490")
        self.root.resizable(False, False)
        self.clear_container()

        main_frame = tk.Frame(self.container, bg=COLOR_BG, padx=28, pady=24)
        main_frame.pack(fill="both", expand=True)

        # Header Branding
        brand_frame = tk.Frame(main_frame, bg=COLOR_BG)
        brand_frame.pack(fill="x", pady=(4, 14))

        logo_lbl = tk.Label(
            brand_frame,
            text="🛡  ONESIUM",
            font=(FONT_FAMILY, 17, "bold"),
            bg=COLOR_BG,
            fg=COLOR_TEXT_PRIMARY,
        )
        logo_lbl.pack(pady=(0, 2))

        sub_lbl = tk.Label(
            brand_frame,
            text="The Credential Vault",
            font=(FONT_FAMILY, 10),
            bg=COLOR_BG,
            fg=COLOR_TEXT_MUTED,
        )
        sub_lbl.pack(pady=(0, 4))

        status_tag = tk.Label(
            brand_frame,
            text="● Offline • Private • Local",
            font=(FONT_FAMILY, 8, "bold"),
            bg=COLOR_SURFACE,
            fg=COLOR_SUCCESS,
            padx=10,
            pady=3,
            bd=1,
            relief="solid",
            highlightbackground=COLOR_BORDER,
            highlightthickness=1,
        )
        status_tag.pack(pady=(4, 0))

        # Form Card Frame
        card = tk.Frame(
            main_frame,
            bg=COLOR_SURFACE,
            bd=1,
            relief="solid",
            highlightbackground=COLOR_BORDER,
            highlightthickness=1,
            padx=20,
            pady=16,
        )
        card.pack(fill="x", pady=(6, 10))

        tk.Label(card, text="Welcome back", font=(FONT_FAMILY, 11, "bold"), bg=COLOR_SURFACE, fg=COLOR_TEXT_PRIMARY).pack(anchor="w", pady=(0, 1))
        tk.Label(card, text="Sign in to your vault", font=(FONT_FAMILY, 8), bg=COLOR_SURFACE, fg=COLOR_TEXT_SECONDARY).pack(anchor="w", pady=(0, 10))

        # Username Field
        tk.Label(card, text="Username", font=(FONT_FAMILY, 9, "bold"), bg=COLOR_SURFACE, fg=COLOR_TEXT_PRIMARY).pack(anchor="w", pady=(0, 3))
        self.login_username_entry = ttk.Entry(card, width=32)
        self.login_username_entry.pack(fill="x", pady=(0, 10))
        self.login_username_entry.focus()

        # Master Password Field with Show/Hide toggle
        pwd_top_row = tk.Frame(card, bg=COLOR_SURFACE)
        pwd_top_row.pack(fill="x", pady=(0, 3))
        tk.Label(pwd_top_row, text="Master Password", font=(FONT_FAMILY, 9, "bold"), bg=COLOR_SURFACE, fg=COLOR_TEXT_PRIMARY).pack(side="left")

        login_eye_btn = tk.Button(
            pwd_top_row,
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
            command=lambda: self._toggle_show(self.login_password_entry, login_eye_btn),
        )
        login_eye_btn.pack(side="right")

        self.login_password_entry = ttk.Entry(card, show="*", width=32)
        self.login_password_entry.pack(fill="x", pady=(0, 10))
        self.login_password_entry.bind("<Return>", lambda e: self.handle_login())

        # Status Message Label
        status_color = COLOR_SUCCESS if is_success else COLOR_DANGER
        self.login_status_label = tk.Label(
            card,
            text=initial_message,
            fg=status_color,
            bg=COLOR_SURFACE,
            wraplength=360,
            font=(FONT_FAMILY, 9),
        )
        self.login_status_label.pack(pady=(0, 6))

        # Unlock Vault Button (Login)
        login_btn = ttk.Button(
            card,
            text="Unlock Vault",
            style="Primary.TButton",
            command=self.handle_login,
        )
        login_btn.pack(fill="x", pady=(2, 4))

        # Switch to Register Link
        switch_frame = tk.Frame(main_frame, bg=COLOR_BG)
        switch_frame.pack(pady=(6, 0))
        tk.Label(switch_frame, text="Don't have a vault?", bg=COLOR_BG, fg=COLOR_TEXT_MUTED, font=(FONT_FAMILY, 9)).pack(side="left", padx=(0, 6))
        register_link = tk.Button(
            switch_frame,
            text="Create Account",
            bg=COLOR_BG,
            fg=COLOR_PRIMARY,
            activebackground=COLOR_BG,
            activeforeground=COLOR_ACCENT,
            bd=0,
            cursor="hand2",
            font=(FONT_FAMILY, 9, "bold underline"),
            command=self.show_register_screen,
        )
        register_link.pack(side="left")

    def handle_login(self):
        username = self.login_username_entry.get().strip()
        password = self.login_password_entry.get()

        if not username or not password:
            self.login_status_label.config(
                text="Please enter both username and master password.",
                fg=COLOR_DANGER,
            )
            return

        result = auth.login_user(username, password)
        if result is None:
            self.login_status_label.config(
                text="Invalid username or master password.",
                fg=COLOR_DANGER,
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
    # 2. Registration Screen
    # ----------------------------------------------------------------------
    def show_register_screen(self):
        self.root.geometry("460x550")
        self.root.resizable(False, False)
        self.clear_container()

        main_frame = tk.Frame(self.container, bg=COLOR_BG, padx=28, pady=20)
        main_frame.pack(fill="both", expand=True)

        # Header Branding
        brand_frame = tk.Frame(main_frame, bg=COLOR_BG)
        brand_frame.pack(fill="x", pady=(2, 10))

        tk.Label(brand_frame, text="🛡  ONESIUM", font=(FONT_FAMILY, 15, "bold"), bg=COLOR_BG, fg=COLOR_TEXT_PRIMARY).pack(pady=(0, 2))
        tk.Label(brand_frame, text="Create New Local Vault", font=(FONT_FAMILY, 9), bg=COLOR_BG, fg=COLOR_TEXT_MUTED).pack(pady=(0, 2))

        # Form Card Frame
        card = tk.Frame(
            main_frame,
            bg=COLOR_SURFACE,
            bd=1,
            relief="solid",
            highlightbackground=COLOR_BORDER,
            highlightthickness=1,
            padx=20,
            pady=14,
        )
        card.pack(fill="x", pady=(4, 6))

        # Username Field
        tk.Label(card, text="Username", font=(FONT_FAMILY, 9, "bold"), bg=COLOR_SURFACE, fg=COLOR_TEXT_PRIMARY).pack(anchor="w", pady=(0, 2))
        self.reg_username_entry = ttk.Entry(card, width=32)
        self.reg_username_entry.pack(fill="x", pady=(0, 8))
        self.reg_username_entry.focus()

        # Master Password Field with Show/Hide toggle
        pwd_top_row = tk.Frame(card, bg=COLOR_SURFACE)
        pwd_top_row.pack(fill="x", pady=(0, 2))
        tk.Label(pwd_top_row, text="Master Password", font=(FONT_FAMILY, 9, "bold"), bg=COLOR_SURFACE, fg=COLOR_TEXT_PRIMARY).pack(side="left")

        reg_eye1 = tk.Button(
            pwd_top_row,
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
            command=lambda: self._toggle_show(self.reg_password_entry, reg_eye1),
        )
        reg_eye1.pack(side="right")

        self.reg_pwd_var = tk.StringVar()
        self.reg_password_entry = ttk.Entry(card, textvariable=self.reg_pwd_var, show="*", width=32)
        self.reg_password_entry.pack(fill="x", pady=(0, 2))

        # Strength & Common Warning
        self.reg_strength_label = ttk.Label(card, text="Strength: Very Weak", font=(FONT_FAMILY, 8, "bold"), style="Card.TLabel")
        self.reg_strength_label.pack(anchor="w", pady=(2, 0))

        self.reg_common_warn = tk.Label(card, text="", fg=COLOR_DANGER, bg=COLOR_SURFACE, font=(FONT_FAMILY, 8))
        self.reg_common_warn.pack(anchor="w", pady=(0, 6))

        def update_reg_feedback(*args):
            val = self.reg_pwd_var.get()
            st = password_utils.check_password_strength(val)
            self.reg_strength_label.config(text=f"Strength: {st['label']}")
            if password_utils.is_common_password(val):
                self.reg_common_warn.config(text="Warning: This is a commonly used password.")
            else:
                self.reg_common_warn.config(text="")

        self.reg_pwd_var.trace_add("write", update_reg_feedback)

        # Confirm Master Password Field with Show/Hide toggle
        cpwd_top_row = tk.Frame(card, bg=COLOR_SURFACE)
        cpwd_top_row.pack(fill="x", pady=(0, 2))
        tk.Label(cpwd_top_row, text="Confirm Master Password", font=(FONT_FAMILY, 9, "bold"), bg=COLOR_SURFACE, fg=COLOR_TEXT_PRIMARY).pack(side="left")

        reg_eye2 = tk.Button(
            cpwd_top_row,
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
            command=lambda: self._toggle_show(self.reg_confirm_entry, reg_eye2),
        )
        reg_eye2.pack(side="right")

        self.reg_confirm_entry = ttk.Entry(card, show="*", width=32)
        self.reg_confirm_entry.pack(fill="x", pady=(0, 8))
        self.reg_confirm_entry.bind("<Return>", lambda e: self.handle_register())

        # Status Message Label
        self.reg_status_label = tk.Label(
            card,
            text="",
            fg=COLOR_DANGER,
            bg=COLOR_SURFACE,
            wraplength=360,
            font=(FONT_FAMILY, 9),
        )
        self.reg_status_label.pack(pady=(0, 6))

        # Create Vault Button (Register)
        register_btn = ttk.Button(
            card,
            text="Create Vault",
            style="Primary.TButton",
            command=self.handle_register,
        )
        register_btn.pack(fill="x", pady=(2, 4))

        # Back to Login Link
        switch_frame = tk.Frame(main_frame, bg=COLOR_BG)
        switch_frame.pack(pady=(4, 0))
        tk.Label(switch_frame, text="Already have a vault?", bg=COLOR_BG, fg=COLOR_TEXT_MUTED, font=(FONT_FAMILY, 9)).pack(side="left", padx=(0, 6))
        login_link = tk.Button(
            switch_frame,
            text="Back to Login",
            bg=COLOR_BG,
            fg=COLOR_PRIMARY,
            activebackground=COLOR_BG,
            activeforeground=COLOR_ACCENT,
            bd=0,
            cursor="hand2",
            font=(FONT_FAMILY, 9, "bold underline"),
            command=self.show_login_screen,
        )
        login_link.pack(side="left")

    def handle_register(self):
        username = self.reg_username_entry.get().strip()
        password = self.reg_password_entry.get()
        confirm_password = self.reg_confirm_entry.get()

        if not username:
            self.reg_status_label.config(text="Username cannot be empty.", fg=COLOR_DANGER)
            return

        if not password:
            self.reg_status_label.config(text="Master password cannot be empty.", fg=COLOR_DANGER)
            return

        if password != confirm_password:
            self.reg_status_label.config(text="Passwords do not match.", fg=COLOR_DANGER)
            return

        try:
            user_id = auth.register_user(username, password)
        except (ValueError, TypeError) as e:
            self.reg_status_label.config(text=str(e), fg=COLOR_DANGER)
            return

        if user_id is None:
            self.reg_status_label.config(
                text="Username already exists. Please choose another.",
                fg=COLOR_DANGER,
            )
            return

        # Registration successful -> return to login with green success banner
        self.show_login_screen(
            initial_message=f"Account '{username}' created successfully! Please login.",
            is_success=True,
        )

    # ----------------------------------------------------------------------
    # 3. Vault Dashboard Screen
    # ----------------------------------------------------------------------
    def show_dashboard_screen(self):
        self.root.geometry("880x540")
        self.root.resizable(True, True)
        self.clear_container()

        # ---------------- Top Navigation Bar ----------------
        top_bar = tk.Frame(
            self.container,
            bg=COLOR_SURFACE,
            height=48,
            bd=1,
            relief="solid",
            highlightbackground=COLOR_BORDER,
            highlightthickness=1,
        )
        top_bar.pack(fill="x", side="top")
        top_bar.pack_propagate(False)

        # Brand on Left
        brand_box = tk.Frame(top_bar, bg=COLOR_SURFACE)
        brand_box.pack(side="left", padx=16, pady=6)

        logo_title = tk.Label(
            brand_box,
            text="🛡  ONESIUM",
            font=(FONT_FAMILY, 11, "bold"),
            bg=COLOR_SURFACE,
            fg=COLOR_TEXT_PRIMARY,
        )
        logo_title.pack(side="left", padx=(0, 6))

        sub_title = tk.Label(
            brand_box,
            text="|  The Credential Vault",
            font=(FONT_FAMILY, 9),
            bg=COLOR_SURFACE,
            fg=COLOR_TEXT_MUTED,
        )
        sub_title.pack(side="left")

        # Session & Logout on Right
        right_box = tk.Frame(top_bar, bg=COLOR_SURFACE)
        right_box.pack(side="right", padx=16, pady=6)

        user_badge = tk.Label(
            right_box,
            text=f"User: {self.current_username}",
            font=(FONT_FAMILY, 9, "bold"),
            bg=COLOR_SURFACE_ELEVATED,
            fg=COLOR_TEXT_PRIMARY,
            padx=8,
            pady=3,
            bd=1,
            relief="solid",
            highlightbackground=COLOR_BORDER,
            highlightthickness=1,
        )
        user_badge.pack(side="left", padx=(0, 10))

        logout_btn = ttk.Button(
            right_box,
            text="Lock & Logout",
            command=self.handle_logout,
        )
        logout_btn.pack(side="left")

        # ---------------- Main Body Layout ----------------
        body_frame = tk.Frame(self.container, bg=COLOR_BG)
        body_frame.pack(fill="both", expand=True)

        # Left Sidebar
        sidebar = tk.Frame(
            body_frame,
            bg=COLOR_SURFACE,
            width=180,
            bd=1,
            relief="solid",
            highlightbackground=COLOR_BORDER,
            highlightthickness=1,
        )
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        side_content = tk.Frame(sidebar, bg=COLOR_SURFACE, padx=10, pady=14)
        side_content.pack(fill="both", expand=True)

        tk.Label(side_content, text="NAVIGATION", font=(FONT_FAMILY, 8, "bold"), bg=COLOR_SURFACE, fg=COLOR_TEXT_DIM).pack(anchor="w", pady=(0, 6))

        vault_tab_btn = ttk.Button(
            side_content,
            text="Your Vault",
            style="SidebarActive.TButton",
        )
        vault_tab_btn.pack(fill="x", pady=(0, 4))

        gen_tab_btn = ttk.Button(
            side_content,
            text="Password Generator",
            style="Sidebar.TButton",
            command=self.open_generator_dialog,
        )
        gen_tab_btn.pack(fill="x", pady=(0, 4))

        tk.Label(side_content, text="VAULT TOOLS", font=(FONT_FAMILY, 8, "bold"), bg=COLOR_SURFACE, fg=COLOR_TEXT_DIM).pack(anchor="w", pady=(14, 6))

        side_backup_btn = ttk.Button(
            side_content,
            text="Backup Vault",
            style="Sidebar.TButton",
            command=self.handle_backup,
        )
        side_backup_btn.pack(fill="x", pady=(0, 4))

        side_restore_btn = ttk.Button(
            side_content,
            text="Restore Vault",
            style="Sidebar.TButton",
            command=self.handle_restore,
        )
        side_restore_btn.pack(fill="x", pady=(0, 4))

        # Bottom status in sidebar
        side_status = tk.Label(
            side_content,
            text="● Offline Safe\nEncrypted Local DB",
            font=(FONT_FAMILY, 8),
            bg=COLOR_SURFACE,
            fg=COLOR_SUCCESS,
            justify="left",
        )
        side_status.pack(side="bottom", anchor="w", pady=(8, 0))

        # Main Content Area
        main_area = tk.Frame(body_frame, bg=COLOR_BG, padx=18, pady=14)
        main_area.pack(side="left", fill="both", expand=True)

        # Title and Subtitle Row
        title_row = tk.Frame(main_area, bg=COLOR_BG)
        title_row.pack(fill="x", pady=(0, 10))

        left_title = tk.Frame(title_row, bg=COLOR_BG)
        left_title.pack(side="left")

        tk.Label(left_title, text="Your Vault", font=(FONT_FAMILY, 15, "bold"), bg=COLOR_BG, fg=COLOR_TEXT_PRIMARY).pack(anchor="w")
        tk.Label(left_title, text="Your credentials stay on this device.", font=(FONT_FAMILY, 9), bg=COLOR_BG, fg=COLOR_TEXT_MUTED).pack(anchor="w")

        self.count_badge = tk.Label(
            title_row,
            text="0 Saved",
            font=(FONT_FAMILY, 9, "bold"),
            bg=COLOR_SURFACE_ELEVATED,
            fg=COLOR_TEXT_PRIMARY,
            padx=8,
            pady=3,
            bd=1,
            relief="solid",
            highlightbackground=COLOR_BORDER,
            highlightthickness=1,
        )
        self.count_badge.pack(side="right", pady=(2, 0))

        # Search Bar & Add Button Row
        toolbar = tk.Frame(main_area, bg=COLOR_BG)
        toolbar.pack(fill="x", pady=(0, 10))

        tk.Label(toolbar, text="Search:", font=(FONT_FAMILY, 9), bg=COLOR_BG, fg=COLOR_TEXT_MUTED).pack(side="left", padx=(0, 4))

        self.search_entry = ttk.Entry(toolbar)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.search_entry.bind("<KeyRelease>", lambda e: self.handle_search())

        clear_search_btn = ttk.Button(
            toolbar,
            text="Clear",
            command=self.clear_search,
        )
        clear_search_btn.pack(side="left", padx=(0, 8))

        self.btn_add = ttk.Button(
            toolbar,
            text="+ Add Credential",
            style="Primary.TButton",
            command=self.open_add_dialog,
        )
        self.btn_add.pack(side="right")

        # Treeview Credential Table Container
        tree_container = tk.Frame(
            main_area,
            bg=COLOR_SURFACE,
            bd=1,
            relief="solid",
            highlightbackground=COLOR_BORDER,
            highlightthickness=1,
        )
        tree_container.pack(fill="both", expand=True, pady=(0, 10))

        columns = ("site_name", "username_field", "updated_at")
        self.tree = ttk.Treeview(
            tree_container,
            columns=columns,
            show="headings",
            selectmode="browse",
        )

        self.tree.heading("site_name", text="Site / Application")
        self.tree.heading("username_field", text="Username / Identifier")
        self.tree.heading("updated_at", text="Last Updated")

        self.tree.column("site_name", width=220, anchor="w")
        self.tree.column("username_field", width=220, anchor="w")
        self.tree.column("updated_at", width=180, anchor="w")

        scrollbar = ttk.Scrollbar(
            tree_container,
            orient="vertical",
            command=self.tree.yview,
            style="Vertical.TScrollbar",
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Empty state overlay inside tree container
        self.empty_frame = tk.Frame(tree_container, bg=COLOR_SURFACE)
        tk.Label(
            self.empty_frame,
            text="No credentials yet",
            font=(FONT_FAMILY, 11, "bold"),
            bg=COLOR_SURFACE,
            fg=COLOR_TEXT_PRIMARY,
        ).pack(pady=(0, 3))
        tk.Label(
            self.empty_frame,
            text="Add your first credential to get started.",
            font=(FONT_FAMILY, 9),
            bg=COLOR_SURFACE,
            fg=COLOR_TEXT_SECONDARY,
        ).pack()

        self.tree.bind("<<TreeviewSelect>>", self.handle_row_select)

        # Action Buttons Toolbar
        actions_bar = tk.Frame(main_area, bg=COLOR_BG)
        actions_bar.pack(fill="x", pady=(0, 0))

        self.btn_show = ttk.Button(
            actions_bar,
            text="Show Password",
            command=self.handle_show_password,
        )
        self.btn_show.pack(side="left", padx=(0, 6))

        self.btn_copy = ttk.Button(
            actions_bar,
            text="Copy Password",
            command=self.handle_copy_password,
        )
        self.btn_copy.pack(side="left", padx=(0, 6))

        self.btn_edit = ttk.Button(
            actions_bar,
            text="Edit",
            command=self.open_edit_dialog,
        )
        self.btn_edit.pack(side="left", padx=(0, 6))

        self.btn_delete = ttk.Button(
            actions_bar,
            text="Delete",
            command=self.handle_delete_credential,
        )
        self.btn_delete.pack(side="left", padx=(0, 10))

        # Secondary backup / restore buttons in action bar
        self.btn_backup = ttk.Button(
            actions_bar,
            text="Backup",
            command=self.handle_backup,
        )
        self.btn_backup.pack(side="right", padx=(6, 0))

        self.btn_restore = ttk.Button(
            actions_bar,
            text="Restore",
            command=self.handle_restore,
        )
        self.btn_restore.pack(side="right")

        # Initial data load
        self.refresh_credential_list()

    def refresh_credential_list(self, entries=None):
        """
        Populates the credential table without decrypting passwords.
        """
        self.selected_entry_id = None
        self.update_action_button_states()

        for item in self.tree.get_children():
            self.tree.delete(item)

        if entries is None:
            entries = vault.get_credentials(self.current_user_id)

        for entry in entries:
            entry_id = entry["entry_id"]
            site_name = entry["site_name"]
            username_field = entry["username_field"]
            updated_at = entry["updated_at"]
            self.tree.insert(
                "",
                "end",
                iid=str(entry_id),
                values=(site_name, username_field, updated_at),
            )

        if hasattr(self, "empty_frame"):
            if len(self.tree.get_children()) == 0:
                self.empty_frame.place(relx=0.5, rely=0.5, anchor="center")
            else:
                self.empty_frame.place_forget()

        if hasattr(self, "count_badge"):
            count = len(self.tree.get_children())
            self.count_badge.config(text=f"{count} Saved")

    def handle_search(self):
        query = self.search_entry.get()
        entries = vault.search_credentials(self.current_user_id, query)
        self.refresh_credential_list(entries)

    def clear_search(self):
        self.search_entry.delete(0, tk.END)
        self.refresh_credential_list()

    def handle_row_select(self, event=None):
        selection = self.tree.selection()
        if selection:
            self.selected_entry_id = int(selection[0])
        else:
            self.selected_entry_id = None
        self.update_action_button_states()

    def update_action_button_states(self):
        has_selection = self.selected_entry_id is not None
        if hasattr(self, "btn_add"):
            self.btn_add.config(state="normal")
        if hasattr(self, "btn_edit"):
            self.btn_edit.config(state="normal" if has_selection else "disabled")
        if hasattr(self, "btn_delete"):
            self.btn_delete.config(state="normal" if has_selection else "disabled")
        if hasattr(self, "btn_show"):
            self.btn_show.config(state="normal" if has_selection else "disabled")
        if hasattr(self, "btn_copy"):
            self.btn_copy.config(state="normal" if has_selection else "disabled")
        if hasattr(self, "btn_backup"):
            self.btn_backup.config(state="normal")
        if hasattr(self, "btn_restore"):
            self.btn_restore.config(state="normal")

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
        dialog = tk.Toplevel(self.root)
        dialog.title("Onesium — Password Generator")
        dialog.resizable(False, False)
        dialog.configure(bg=COLOR_BG)
        dialog.transient(self.root)
        dialog.grab_set()
        center_window(dialog, 400, 320, self.root)

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

        close_btn = ttk.Button(btn_row, text="Close", command=dialog.destroy)
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

    def handle_auto_lock(self):
        """Locks the session upon inactivity timeout."""
        self.cancel_auto_lock_timer()

        if self.active_dialog and self.active_dialog.winfo_exists():
            self.active_dialog.destroy()
        self.active_dialog = None

        self.current_user_id = None
        self.current_encryption_key = None
        self.current_username = None
        self.selected_entry_id = None

        try:
            self.root.clipboard_clear()
        except Exception:
            pass

        self.show_login_screen(
            initial_message="Session locked due to inactivity. Please login again.",
            is_success=False,
        )

    # ----------------------------------------------------------------------
    # 11. Logout Handling
    # ----------------------------------------------------------------------
    def handle_logout(self):
        self.cancel_auto_lock_timer()

        # Close any active modal dialogs
        if self.active_dialog and self.active_dialog.winfo_exists():
            self.active_dialog.destroy()
        self.active_dialog = None

        # Clear in-memory session credentials & selection
        self.current_user_id = None
        self.current_encryption_key = None
        self.current_username = None
        self.selected_entry_id = None

        try:
            self.root.clipboard_clear()
        except Exception:
            pass

        self.show_login_screen(
            initial_message="You have been logged out.",
            is_success=True,
        )


def start_app(root=None):
    """Entry helper to launch GUI application."""
    if root is None:
        root = tk.Tk()
    app = PasswordManagerApp(root)
    return app
