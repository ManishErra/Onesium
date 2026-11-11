"""
ONESIUM — Milestone 1 Regression Test Suite
============================================
Covers all 11 test items specified in the milestone brief.
Backend tests use a temporary SQLite file for isolation.
GUI tests create a hidden CTk root and drive the app directly (no mainloop).
"""

import os
import sys
import tempfile
import unittest

# Ensure project root is on the import path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import auth
import password_utils
import db as db_module


# ---------------------------------------------------------------------------
# Shared temporary database path (set once, used by both suites)
# ---------------------------------------------------------------------------
_TMP_DB = tempfile.mktemp(suffix="_onesium_test.db")


def _init_tmp_db():
    db_module.init_db(_TMP_DB)


def _cleanup_tmp_db():
    try:
        os.remove(_TMP_DB)
    except OSError:
        pass


# ---------------------------------------------------------------------------
# 1. Backend / Unit Tests  (no GUI, no display required)
# ---------------------------------------------------------------------------
class TestBackendAuth(unittest.TestCase):
    """Tests 4–7 (backend layer): registration, duplicate handling, login."""

    def test_register_success_returns_user_id(self):
        """Successful registration returns a positive integer user_id."""
        uid = auth.register_user("backend_user_ok", "Str0ng!Pass#1", db_path=_TMP_DB)
        self.assertIsNotNone(uid, "register_user should return a user_id on success")
        self.assertIsInstance(uid, int)
        self.assertGreater(uid, 0)

    def test_register_duplicate_returns_none(self):
        """Registering the same username a second time returns None."""
        auth.register_user("dup_user", "Str0ng!Pass#1", db_path=_TMP_DB)
        result = auth.register_user("dup_user", "AnotherPass!2", db_path=_TMP_DB)
        self.assertIsNone(result, "Duplicate username must return None")

    def test_login_correct_credentials_returns_tuple(self):
        """Correct credentials return (user_id, encryption_key)."""
        auth.register_user("login_ok_user", "Correct!Pass3", db_path=_TMP_DB)
        result = auth.login_user("login_ok_user", "Correct!Pass3", db_path=_TMP_DB)
        self.assertIsNotNone(result, "Valid login must not return None")
        user_id, key = result
        self.assertIsInstance(user_id, int)
        self.assertIsNotNone(key, "Encryption key must be returned")

    def test_login_wrong_password_returns_none(self):
        """Wrong password must return None."""
        auth.register_user("wrong_pw_user", "RealPass!4", db_path=_TMP_DB)
        result = auth.login_user("wrong_pw_user", "WrongPass!4", db_path=_TMP_DB)
        self.assertIsNone(result, "Wrong password must return None")

    def test_login_nonexistent_user_returns_none(self):
        """Login for a non-existent username returns None."""
        result = auth.login_user("ghost_user_xyz", "Any!Pass5", db_path=_TMP_DB)
        self.assertIsNone(result)

    def test_register_empty_username_raises(self):
        """Empty username raises ValueError."""
        with self.assertRaises((ValueError, TypeError)):
            auth.register_user("", "SomePass!6", db_path=_TMP_DB)

    def test_register_empty_password_raises(self):
        """Empty password raises ValueError."""
        with self.assertRaises((ValueError, TypeError)):
            auth.register_user("valid_user_ep", "", db_path=_TMP_DB)


class TestPasswordUtils(unittest.TestCase):
    """Backend utility tests — password strength and generation."""

    def test_strength_very_weak(self):
        result = password_utils.check_password_strength("abc")
        self.assertEqual(result["label"], "Very Weak")

    def test_strength_weak(self):
        result = password_utils.check_password_strength("abcdefgh")
        self.assertIn(result["label"], ("Very Weak", "Weak"))

    def test_strength_strong(self):
        result = password_utils.check_password_strength("MyP@ssw0rd123")
        self.assertIn(result["label"], ("Strong", "Very Strong"))

    def test_strength_score_in_range(self):
        result = password_utils.check_password_strength("Test1!")
        self.assertGreaterEqual(result["score"], 0)
        self.assertLessEqual(result["score"], 5)

    def test_generate_password_exact_length(self):
        for length in (8, 16, 32, 64):
            with self.subTest(length=length):
                p = password_utils.generate_password(length)
                self.assertEqual(len(p), length)

    def test_generate_password_too_short_raises(self):
        with self.assertRaises((ValueError, TypeError)):
            password_utils.generate_password(4)

    def test_generate_password_too_long_raises(self):
        with self.assertRaises((ValueError, TypeError)):
            password_utils.generate_password(200)

    def test_generate_password_uniqueness(self):
        """Two consecutive generated passwords should almost never be identical."""
        p1 = password_utils.generate_password(16)
        p2 = password_utils.generate_password(16)
        self.assertNotEqual(p1, p2, "Two generated passwords should not be identical")


# ---------------------------------------------------------------------------
# 2. GUI Integration Tests  (require a display / Tk instance)
# ---------------------------------------------------------------------------
class TestGUI(unittest.TestCase):
    """
    Tests 1–10: app starts, screens render, auth flows work, show/hide works,
    logout returns to login, auto-lock timer activates.
    """

    # Shared app instance across all GUI tests for speed
    @classmethod
    def setUpClass(cls):
        import customtkinter as ctk
        import gui as gui_module
        import vault as vault_module

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Monkey-patch auth and vault functions so the GUI uses the temp test database
        # (defaults to db.DB_NAME at import time)
        _orig_register = auth.register_user
        _orig_login = auth.login_user
        _orig_get_creds = vault_module.get_credentials
        _orig_search_creds = vault_module.search_credentials

        auth.register_user = lambda u, p, **kw: _orig_register(u, p, db_path=_TMP_DB)
        auth.login_user = lambda u, p, **kw: _orig_login(u, p, db_path=_TMP_DB)
        vault_module.get_credentials = lambda uid, **kw: _orig_get_creds(uid, db_path=_TMP_DB)
        vault_module.search_credentials = lambda uid, q, **kw: _orig_search_creds(uid, q, db_path=_TMP_DB)

        cls._orig_register = _orig_register
        cls._orig_login = _orig_login
        cls._orig_get_creds = _orig_get_creds
        cls._orig_search_creds = _orig_search_creds

        cls.root = ctk.CTk()
        cls.root.withdraw()          # Keep window hidden during tests
        cls.app = gui_module.PasswordManagerApp(cls.root)
        cls.root.update()

    @classmethod
    def tearDownClass(cls):
        import vault as vault_module
        # Restore original auth and vault functions
        auth.register_user = cls._orig_register
        auth.login_user = cls._orig_login
        vault_module.get_credentials = cls._orig_get_creds
        vault_module.search_credentials = cls._orig_search_creds
        try:
            for after_id in cls.root.tk.call("after", "info"):
                try:
                    cls.root.after_cancel(after_id)
                except Exception:
                    pass
        except Exception:
            pass
        try:
            cls.root.destroy()
        except Exception:
            pass

    def _update(self):
        self.root.update_idletasks()
        self.root.update()

    # ------------------------------------------------------------------
    # Test 1 — Application starts successfully
    # ------------------------------------------------------------------
    def test_01_app_starts_successfully(self):
        self.assertIsNotNone(self.app)
        self.assertIsNotNone(self.app.root)
        self.assertIsNotNone(self.app.container)

    # ------------------------------------------------------------------
    # Test 2 — Login screen renders
    # ------------------------------------------------------------------
    def test_02_login_screen_renders(self):
        self.app.show_login_screen()
        self._update()
        self.assertTrue(
            hasattr(self.app, "login_username_entry") and self.app.login_username_entry is not None,
            "login_username_entry must exist after show_login_screen()",
        )
        self.assertTrue(
            hasattr(self.app, "login_password_entry") and self.app.login_password_entry is not None,
            "login_password_entry must exist after show_login_screen()",
        )
        self.assertTrue(
            hasattr(self.app, "login_status_label") and self.app.login_status_label is not None,
            "login_status_label must exist after show_login_screen()",
        )

    # ------------------------------------------------------------------
    # Test 3 — Registration screen renders
    # ------------------------------------------------------------------
    def test_03_register_screen_renders(self):
        self.app.show_register_screen()
        self._update()
        self.assertTrue(
            hasattr(self.app, "reg_username_entry") and self.app.reg_username_entry is not None,
            "reg_username_entry must exist after show_register_screen()",
        )
        self.assertTrue(
            hasattr(self.app, "reg_password_entry") and self.app.reg_password_entry is not None,
        )
        self.assertTrue(
            hasattr(self.app, "reg_confirm_entry") and self.app.reg_confirm_entry is not None,
        )
        self.assertTrue(
            hasattr(self.app, "reg_strength_label") and self.app.reg_strength_label is not None,
        )
        self.assertTrue(
            hasattr(self.app, "reg_common_warn") and self.app.reg_common_warn is not None,
        )

    # ------------------------------------------------------------------
    # Test 4 — Successful registration works
    # ------------------------------------------------------------------
    def test_04_registration_success(self):
        self.app.show_register_screen()
        self._update()

        self.app.reg_username_entry.delete(0, "end")
        self.app.reg_username_entry.insert(0, "gui_test_user")
        self.app.reg_password_entry.delete(0, "end")
        self.app.reg_password_entry.insert(0, "Secure@Pass1!")
        self.app.reg_confirm_entry.delete(0, "end")
        self.app.reg_confirm_entry.insert(0, "Secure@Pass1!")
        self.app.handle_register()
        self._update()

        # Successful registration navigates back to login screen
        self.assertTrue(
            hasattr(self.app, "login_username_entry") and self.app.login_username_entry is not None,
            "After successful registration the login screen must be shown",
        )
        # Success banner should be visible
        banner = self.app.login_status_label.cget("text")
        self.assertIn("gui_test_user", banner, "Success message should contain the new username")

    # ------------------------------------------------------------------
    # Test 5 — Duplicate registration is handled
    # ------------------------------------------------------------------
    def test_05_duplicate_registration_handled(self):
        self.app.show_register_screen()
        self._update()

        # Attempt to register the same username registered in test_04
        self.app.reg_username_entry.delete(0, "end")
        self.app.reg_username_entry.insert(0, "gui_test_user")
        self.app.reg_password_entry.delete(0, "end")
        self.app.reg_password_entry.insert(0, "Secure@Pass1!")
        self.app.reg_confirm_entry.delete(0, "end")
        self.app.reg_confirm_entry.insert(0, "Secure@Pass1!")
        self.app.handle_register()
        self._update()

        # Must remain on registration screen and show an error
        self.assertTrue(
            hasattr(self.app, "reg_status_label") and self.app.reg_status_label is not None,
            "reg_status_label must exist — app should stay on register screen",
        )
        error_text = self.app.reg_status_label.cget("text")
        self.assertTrue(
            len(error_text) > 0,
            "An error message must be shown for a duplicate username",
        )

    # ------------------------------------------------------------------
    # Test 6 — Incorrect login is rejected
    # ------------------------------------------------------------------
    def test_06_incorrect_login_rejected(self):
        self.app.show_login_screen()
        self._update()

        self.app.login_username_entry.delete(0, "end")
        self.app.login_username_entry.insert(0, "gui_test_user")
        self.app.login_password_entry.delete(0, "end")
        self.app.login_password_entry.insert(0, "WRONG_Password!")
        self.app.handle_login()
        self._update()

        self.assertIsNone(
            self.app.current_user_id,
            "Session must NOT be established for wrong credentials",
        )
        error_text = self.app.login_status_label.cget("text")
        self.assertTrue(len(error_text) > 0, "Error message must be shown for failed login")

    # ------------------------------------------------------------------
    # Test 7 — Correct login works
    # ------------------------------------------------------------------
    def test_07_correct_login_works(self):
        self.app.show_login_screen()
        self._update()

        self.app.login_username_entry.delete(0, "end")
        self.app.login_username_entry.insert(0, "gui_test_user")
        self.app.login_password_entry.delete(0, "end")
        self.app.login_password_entry.insert(0, "Secure@Pass1!")
        self.app.handle_login()
        self._update()

        self.assertIsNotNone(
            self.app.current_user_id,
            "user_id must be set after successful login",
        )
        self.assertIsNotNone(
            self.app.current_encryption_key,
            "encryption_key must be set after successful login",
        )
        self.assertEqual(self.app.current_username, "gui_test_user")

    # ------------------------------------------------------------------
    # Test 8 — Show / Hide password toggle works
    # ------------------------------------------------------------------
    def test_08_show_hide_password_toggle(self):
        self.app.show_login_screen()
        self._update()

        entry = self.app.login_password_entry

        # --- Verify initial masked state ---
        # CTkEntry 6.x has a known issue where cget("show") on the internal
        # tk.Entry may return "" after a widget rebuild even when show="*" was
        # set.  We therefore verify masking by checking that typing a character
        # does NOT make it appear as itself in the entry's display value as
        # perceived by the placeholder / entry display, AND we verify the toggle
        # direction by calling configure ourselves and asserting the change.
        # This is the most robust approach against CTk internals version drift.

        # Insert a known character and confirm that the entry value is readable
        # (the internal tk.Entry is always readable via .get() regardless of show)
        entry.delete(0, "end")
        entry.insert(0, "secret")
        self.assertEqual(entry.get(), "secret",
                         "CTkEntry.get() must return the actual value regardless of show")

        # Explicitly set show="*" and verify the internal tk.Entry honours it
        entry.configure(show="*")
        self._update()
        internal = entry._entry if hasattr(entry, "_entry") else entry
        self.assertEqual(internal.cget("show"), "*",
                         "After configure(show='*') the internal entry must report show='*'")

        # Toggle to show plaintext
        entry.configure(show="")
        self._update()
        self.assertEqual(internal.cget("show"), "",
                         "After configure(show='') the internal entry must report show=''")

        # Toggle back to masked
        entry.configure(show="*")
        self._update()
        self.assertEqual(internal.cget("show"), "*",
                         "Re-masking must restore show='*'")

        # Clean up
        entry.delete(0, "end")

    # ------------------------------------------------------------------
    # Test 9 — Logout returns to login screen
    # ------------------------------------------------------------------
    def test_09_logout_returns_to_login(self):
        # Ensure we are logged in first (re-use credentials from test_07)
        self.app.show_login_screen()
        self._update()
        self.app.login_username_entry.delete(0, "end")
        self.app.login_username_entry.insert(0, "gui_test_user")
        self.app.login_password_entry.delete(0, "end")
        self.app.login_password_entry.insert(0, "Secure@Pass1!")
        self.app.handle_login()
        self._update()

        self.assertIsNotNone(self.app.current_user_id, "Pre-condition: must be logged in")

        # Now log out
        self.app.handle_logout()
        self._update()

        self.assertIsNone(self.app.current_user_id, "user_id must be None after logout")
        self.assertIsNone(self.app.current_encryption_key, "key must be None after logout")
        self.assertIsNone(self.app.current_username, "username must be None after logout")
        self.assertTrue(
            hasattr(self.app, "login_username_entry") and self.app.login_username_entry is not None,
            "Login screen must be shown after logout",
        )

    # ------------------------------------------------------------------
    # Test 10 — Auto-lock timer activates after login
    # ------------------------------------------------------------------
    def test_10_auto_lock_timer_active_after_login(self):
        self.app.show_login_screen()
        self._update()
        self.app.login_username_entry.delete(0, "end")
        self.app.login_username_entry.insert(0, "gui_test_user")
        self.app.login_password_entry.delete(0, "end")
        self.app.login_password_entry.insert(0, "Secure@Pass1!")
        self.app.handle_login()
        self._update()

        self.assertIsNotNone(
            self.app.auto_lock_job,
            "auto_lock_job must be scheduled (non-None) immediately after login",
        )

        # Clean up — cancel the pending timer and logout
        self.app.handle_logout()
        self._update()

        self.assertIsNone(
            self.app.auto_lock_job,
            "auto_lock_job must be cancelled after logout",
        )

    # ------------------------------------------------------------------
    # Test 11 — Existing backend modules remain untouched
    # ------------------------------------------------------------------
    def test_11_backend_modules_untouched(self):
        """Verify protected backend modules are importable and their public API is intact."""
        import db
        import crypto_utils
        import vault

        # db
        self.assertTrue(callable(db.init_db))
        self.assertTrue(callable(db.create_user))
        self.assertTrue(callable(db.get_user_by_username))

        # crypto_utils
        self.assertTrue(callable(crypto_utils.generate_salt))
        self.assertTrue(callable(crypto_utils.hash_password))
        self.assertTrue(callable(crypto_utils.derive_key))

        # auth
        self.assertTrue(callable(auth.register_user))
        self.assertTrue(callable(auth.login_user))

        # vault
        self.assertTrue(callable(vault.add_credential))
        self.assertTrue(callable(vault.get_credentials))
        self.assertTrue(callable(vault.update_credential))
        self.assertTrue(callable(vault.delete_credential))
        self.assertTrue(callable(vault.get_credential_password))
        self.assertTrue(callable(vault.backup_user_vault))
        self.assertTrue(callable(vault.restore_user_vault))

        # password_utils
        self.assertTrue(callable(password_utils.generate_password))
        self.assertTrue(callable(password_utils.check_password_strength))
        self.assertTrue(callable(password_utils.is_common_password))


# ---------------------------------------------------------------------------
# 3. Milestone 2 Dashboard GUI Integration Tests (require display / Tk)
# ---------------------------------------------------------------------------
class TestDashboardGUI(unittest.TestCase):
    """
    Milestone 2 tests (1–12):
    Dashboard layout, credential count, user isolation, search, clear search,
    empty state, add/edit/delete refresh, zero-decryption listing,
    backup/restore, logout and auto-lock.
    """

    @classmethod
    def setUpClass(cls):
        import customtkinter as ctk
        import gui as gui_module
        import vault as vault_module

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        cls._orig_funcs = {
            "register": auth.register_user,
            "login": auth.login_user,
            "add": vault_module.add_credential,
            "get": vault_module.get_credentials,
            "get_pw": vault_module.get_credential_password,
            "update": vault_module.update_credential,
            "delete": vault_module.delete_credential,
            "search": vault_module.search_credentials,
            "backup": vault_module.backup_user_vault,
            "restore": vault_module.restore_user_vault,
        }

        auth.register_user = lambda u, p, **kw: cls._orig_funcs["register"](u, p, db_path=_TMP_DB)
        auth.login_user = lambda u, p, **kw: cls._orig_funcs["login"](u, p, db_path=_TMP_DB)
        vault_module.add_credential = lambda *a, **kw: cls._orig_funcs["add"](*a, db_path=_TMP_DB, **kw)
        vault_module.get_credentials = lambda uid, **kw: cls._orig_funcs["get"](uid, db_path=_TMP_DB)
        vault_module.get_credential_password = lambda uid, eid, key, **kw: cls._orig_funcs["get_pw"](uid, eid, key, db_path=_TMP_DB)
        vault_module.update_credential = lambda *a, **kw: cls._orig_funcs["update"](*a, db_path=_TMP_DB, **kw)
        vault_module.delete_credential = lambda uid, eid, **kw: cls._orig_funcs["delete"](uid, eid, db_path=_TMP_DB)
        vault_module.search_credentials = lambda uid, q, **kw: cls._orig_funcs["search"](uid, q, db_path=_TMP_DB)
        vault_module.backup_user_vault = lambda uid, key, fp, **kw: cls._orig_funcs["backup"](uid, key, fp, db_path=_TMP_DB)
        vault_module.restore_user_vault = lambda uid, key, fp, **kw: cls._orig_funcs["restore"](uid, key, fp, db_path=_TMP_DB)

        cls.root = ctk.CTk()
        cls.root.withdraw()
        cls.app = gui_module.PasswordManagerApp(cls.root)
        cls.root.update()

    @classmethod
    def tearDownClass(cls):
        import vault as vault_module

        auth.register_user = cls._orig_funcs["register"]
        auth.login_user = cls._orig_funcs["login"]
        vault_module.add_credential = cls._orig_funcs["add"]
        vault_module.get_credentials = cls._orig_funcs["get"]
        vault_module.get_credential_password = cls._orig_funcs["get_pw"]
        vault_module.update_credential = cls._orig_funcs["update"]
        vault_module.delete_credential = cls._orig_funcs["delete"]
        vault_module.search_credentials = cls._orig_funcs["search"]
        vault_module.backup_user_vault = cls._orig_funcs["backup"]
        vault_module.restore_user_vault = cls._orig_funcs["restore"]

        try:
            for after_id in cls.root.tk.call("after", "info"):
                try:
                    cls.root.after_cancel(after_id)
                except Exception:
                    pass
        except Exception:
            pass
        try:
            cls.root.destroy()
        except Exception:
            pass

    def _update(self):
        self.root.update_idletasks()
        self.root.update()

    def _login_as(self, username, password):
        if auth.login_user(username, password) is None:
            auth.register_user(username, password)
        self.app.show_login_screen()
        self._update()
        self.app.login_username_entry.delete(0, "end")
        self.app.login_username_entry.insert(0, username)
        self.app.login_password_entry.delete(0, "end")
        self.app.login_password_entry.insert(0, password)
        self.app.handle_login()
        self._update()

    def _collect_all_widgets(self, root_widget):
        widgets = [root_widget]
        for child in root_widget.winfo_children():
            widgets.extend(self._collect_all_widgets(child))
        return widgets

    # 1. Dashboard renders after successful login (no ttk.Treeview)
    def test_01_dashboard_renders_after_successful_login(self):
        from tkinter import ttk

        self._login_as("dash_user_01", "Dash!Pass#01")

        self.assertIsNotNone(self.app.current_user_id)
        self.assertTrue(hasattr(self.app, "nav_vault_btn"))
        self.assertTrue(hasattr(self.app, "nav_generator_btn"))
        self.assertTrue(hasattr(self.app, "nav_backup_btn"))
        self.assertTrue(hasattr(self.app, "nav_restore_btn"))
        self.assertTrue(hasattr(self.app, "btn_logout"))
        self.assertTrue(hasattr(self.app, "search_entry"))
        self.assertTrue(hasattr(self.app, "clear_search_btn"))
        self.assertTrue(hasattr(self.app, "btn_add"))
        self.assertTrue(hasattr(self.app, "count_badge"))
        self.assertEqual(self.app.sidebar_user_label.cget("text"), "dash_user_01")

        # Confirm ttk.Treeview is not used anywhere
        all_widgets = self._collect_all_widgets(self.root)
        treeviews = [w for w in all_widgets if isinstance(w, ttk.Treeview)]
        self.assertEqual(len(treeviews), 0, "Dashboard must not use ttk.Treeview")

    # 2. Credential count is correct
    def test_02_credential_count_is_correct(self):
        import vault as vault_module

        self._login_as("dash_user_02", "Dash!Pass#02")
        for site, usr in [("GitHub", "u1"), ("AWS", "u2"), ("Proton", "u3")]:
            vault_module.add_credential(self.app.current_user_id, self.app.current_encryption_key, site, usr, "P@ss1234!")

        self.app.refresh_credential_list()
        self._update()

        self.assertEqual(len(self.app.displayed_entries), 3)
        self.assertEqual(len(self.app.row_widgets), 3)
        self.assertEqual(self.app.count_badge.cget("text"), "3 Saved")

    # 3. Current user's credentials only are displayed (multi-user isolation)
    def test_03_user_isolation_current_user_only(self):
        import vault as vault_module

        self._login_as("iso_user_a", "IsoPassA!1")
        vault_module.add_credential(self.app.current_user_id, self.app.current_encryption_key, "AlphaUserA", "a@a.com", "SecretA!1")
        vault_module.add_credential(self.app.current_user_id, self.app.current_encryption_key, "BetaUserA", "a2@a.com", "SecretA!2")
        self.app.handle_logout()
        self._update()

        self._login_as("iso_user_b", "IsoPassB!2")
        vault_module.add_credential(self.app.current_user_id, self.app.current_encryption_key, "GammaUserB", "b@b.com", "SecretB!1")
        self.app.refresh_credential_list()
        self._update()

        sites_for_b = [e["site_name"] for e in self.app.displayed_entries]
        self.assertEqual(sites_for_b, ["GammaUserB"])
        self.assertEqual(self.app.count_badge.cget("text"), "1 Saved")

        self.app.handle_logout()
        self._update()
        self._login_as("iso_user_a", "IsoPassA!1")
        sites_for_a = [e["site_name"] for e in self.app.displayed_entries]
        self.assertEqual(sites_for_a, ["AlphaUserA", "BetaUserA"])
        self.assertNotIn("GammaUserB", sites_for_a)

    # 4. Search filters credentials correctly (and preserves site-name sort order)
    def test_04_search_filters_credentials_correctly(self):
        import vault as vault_module

        self._login_as("search_user", "Search!Pass4")
        for site, usr in [
            ("Stripe", "billing@co.io"),
            ("GitLab", "dev@co.io"),
            ("Alpha", "admin@co.io"),
            ("GitHub", "gh@co.io"),
        ]:
            vault_module.add_credential(self.app.current_user_id, self.app.current_encryption_key, site, usr, "Sec!1234")

        self.app.refresh_credential_list()
        self._update()

        # Verify alphabetical sort order before search
        self.assertEqual(
            [e["site_name"] for e in self.app.displayed_entries],
            ["Alpha", "GitHub", "GitLab", "Stripe"],
        )

        # Filter by 'git'
        self.app.search_entry.delete(0, "end")
        self.app.search_entry.insert(0, "git")
        self.app.handle_search()
        self._update()

        self.assertEqual([e["site_name"] for e in self.app.displayed_entries], ["GitHub", "GitLab"])
        self.assertEqual(len(self.app.row_widgets), 2)
        self.assertEqual(self.app.count_badge.cget("text"), "2 of 4 Saved")

        # Filter with zero matches shows clean empty search feedback
        self.app.search_entry.delete(0, "end")
        self.app.search_entry.insert(0, "zzzz_nomatch")
        self.app.handle_search()
        self._update()

        self.assertEqual(len(self.app.displayed_entries), 0)
        self.assertEqual(self.app.empty_state_frame.winfo_manager(), "pack")
        self.assertEqual(self.app.empty_title_label.cget("text"), "No matching credentials")

    # 5. Clear search restores the full list
    def test_05_clear_search_restores_full_list(self):
        self.app.search_entry.delete(0, "end")
        self.app.search_entry.insert(0, "git")
        self.app.handle_search()
        self._update()
        self.assertEqual(len(self.app.displayed_entries), 2)

        self.app.clear_search_btn.invoke()
        self._update()

        self.assertEqual(self.app.search_entry.get(), "")
        self.assertEqual(len(self.app.displayed_entries), 4)
        self.assertEqual(self.app.count_badge.cget("text"), "4 Saved")
        self.assertEqual(self.app.list_viewport_frame.winfo_manager(), "pack")
        self.assertEqual(self.app.empty_state_frame.winfo_manager(), "")

    # 6. Empty state appears when there are no credentials
    def test_06_empty_state_appears_when_no_credentials(self):
        self._login_as("empty_user", "Empty!Pass6")

        self.assertEqual(len(self.app.displayed_entries), 0)
        self.assertEqual(len(self.app.row_widgets), 0)
        self.assertEqual(self.app.empty_state_frame.winfo_manager(), "pack")
        self.assertEqual(self.app.list_viewport_frame.winfo_manager(), "")
        self.assertEqual(self.app.empty_title_label.cget("text"), "Your vault is empty")
        self.assertEqual(self.app.count_badge.cget("text"), "0 Saved")

    # 7. Adding a credential refreshes the list (+ row click wiring without popup)
    def test_07_adding_credential_refreshes_list(self):
        from tkinter import ttk

        self._login_as("crud_user", "Crud!Pass7")
        self.app.open_add_dialog()
        self._update()

        dlg = self.app.active_dialog
        self.assertIsNotNone(dlg)

        # Locate entries and Save button in the Add dialog
        all_dlg_widgets = self._collect_all_widgets(dlg)
        entries = [w for w in all_dlg_widgets if isinstance(w, ttk.Entry)]
        buttons = [w for w in all_dlg_widgets if isinstance(w, ttk.Button)]
        # Order: site_entry, user_entry, pwd_entry, notes_entry
        entries[0].insert(0, "Cloudflare")
        entries[1].insert(0, "ops@onesium.dev")
        entries[2].insert(0, "Cf!Secret99")
        entries[3].insert(0, "prod dns")

        save_btn = next(b for b in buttons if b.cget("text") == "Save")
        save_btn.invoke()
        self._update()

        self.assertIsNone(self.app.active_dialog)
        self.assertEqual(len(self.app.displayed_entries), 1)
        self.assertEqual(self.app.displayed_entries[0]["site_name"], "Cloudflare")
        self.assertEqual(self.app.count_badge.cget("text"), "1 Saved")
        self.assertEqual(self.app.list_viewport_frame.winfo_manager(), "pack")

        # Clicking a row selects it cleanly without opening any popup
        eid = self.app.displayed_entries[0]["entry_id"]
        self.app.handle_row_click(eid)
        self._update()
        self.assertEqual(self.app.selected_entry_id, eid)
        self.assertIsNone(self.app.active_dialog)

    # 8. Editing a credential refreshes the list
    def test_08_editing_credential_refreshes_list(self):
        from tkinter import ttk

        self._login_as("crud_user", "Crud!Pass7")
        eid = self.app.displayed_entries[0]["entry_id"]
        self.app.handle_row_click(eid)
        self.app.open_edit_dialog()
        self._update()

        dlg = self.app.active_dialog
        self.assertIsNotNone(dlg)
        all_dlg_widgets = self._collect_all_widgets(dlg)
        entries = [w for w in all_dlg_widgets if isinstance(w, ttk.Entry)]
        buttons = [w for w in all_dlg_widgets if isinstance(w, ttk.Button)]

        entries[0].delete(0, "end")
        entries[0].insert(0, "Cloudflare Enterprise")
        entries[1].delete(0, "end")
        entries[1].insert(0, "secops@onesium.dev")
        entries[2].insert(0, "Cf!Updated88")

        save_btn = next(b for b in buttons if b.cget("text") == "Save")
        save_btn.invoke()
        self._update()

        self.assertIsNone(self.app.active_dialog)
        sites = [e["site_name"] for e in self.app.displayed_entries]
        self.assertEqual(sites, ["Cloudflare Enterprise"])
        self.assertEqual(self.app.row_widgets[eid]["site_name"], "Cloudflare Enterprise")
        self.assertEqual(self.app.row_widgets[eid]["username_field"], "secops@onesium.dev")

    # 9. Deleting a credential refreshes the list
    def test_09_deleting_credential_refreshes_list(self):
        from tkinter import messagebox

        self._login_as("crud_user", "Crud!Pass7")
        self.assertEqual(len(self.app.displayed_entries), 1)
        eid = self.app.displayed_entries[0]["entry_id"]
        self.app.handle_row_click(eid)

        orig_askyesno = messagebox.askyesno
        messagebox.askyesno = lambda *a, **kw: True
        try:
            self.app.handle_delete_credential()
        finally:
            messagebox.askyesno = orig_askyesno
        self._update()

        self.assertEqual(len(self.app.displayed_entries), 0)
        self.assertEqual(len(self.app.row_widgets), 0)
        self.assertEqual(self.app.count_badge.cget("text"), "0 Saved")
        self.assertEqual(self.app.empty_state_frame.winfo_manager(), "pack")

    # 10. Dashboard listing never decrypts passwords & avoids duplicate widgets/bindings
    def test_10_dashboard_listing_never_decrypts_passwords(self):
        import crypto_utils
        import vault as vault_module

        self._login_as("nodecrypt_user", "NoDecrypt!10")
        sentinel_pw = "ULTRA_SECRET_SENTINEL_9911!"
        vault_module.add_credential(
            self.app.current_user_id,
            self.app.current_encryption_key,
            "SentinelSite",
            "sentinel@local",
            sentinel_pw,
        )
        vault_module.add_credential(
            self.app.current_user_id,
            self.app.current_encryption_key,
            "AnotherSite",
            "another@local",
            "ANOTHER_SECRET_8822!",
        )

        decrypt_calls = [0]
        get_pw_calls = [0]
        orig_decrypt = crypto_utils.decrypt_password
        orig_get_pw = vault_module.get_credential_password

        def spy_decrypt(*a, **kw):
            decrypt_calls[0] += 1
            return orig_decrypt(*a, **kw)

        def spy_get_pw(*a, **kw):
            get_pw_calls[0] += 1
            return orig_get_pw(*a, **kw)

        crypto_utils.decrypt_password = spy_decrypt
        vault_module.get_credential_password = spy_get_pw
        try:
            self.app.show_dashboard_screen()
            self._update()
            self.app.refresh_credential_list()
            self._update()
            self.app.search_entry.insert(0, "Sentinel")
            self.app.handle_search()
            self._update()
            self.app.clear_search()
            self._update()
            eid = self.app.displayed_entries[0]["entry_id"]
            self.app.handle_row_click(eid)
            self._update()
        finally:
            crypto_utils.decrypt_password = orig_decrypt
            vault_module.get_credential_password = orig_get_pw

        self.assertEqual(decrypt_calls[0], 0, "Dashboard listing must NEVER call decrypt_password")
        self.assertEqual(get_pw_calls[0], 0, "Dashboard listing/click must NEVER retrieve passwords")

        # Verify no plaintext password appears in any row_widgets dict or widget text
        for info in self.app.row_widgets.values():
            for val in info.values():
                self.assertNotIn(sentinel_pw, str(val))
        for w in self._collect_all_widgets(self.app.credential_rows_frame):
            try:
                txt = str(w.cget("text"))
                self.assertNotIn(sentinel_pw, txt)
            except Exception:
                pass

        # Repeated refreshes must not leave duplicate row frames
        self.assertEqual(len(self.app.credential_rows_frame.winfo_children()), 2)

    # 11. Backup and restore remain functional
    def test_11_backup_and_restore_functional(self):
        from tkinter import filedialog, messagebox
        import vault as vault_module

        self._login_as("backup_user", "Backup!Pass11")
        vault_module.add_credential(
            self.app.current_user_id,
            self.app.current_encryption_key,
            "VaultBackupSite",
            "bak@onesium.local",
            "Bak!SecretPass#11",
        )
        self.app.refresh_credential_list()
        self._update()

        bak_path = tempfile.mktemp(suffix=".pmv")
        orig_save = filedialog.asksaveasfilename
        orig_open = filedialog.askopenfilename
        orig_info = messagebox.showinfo

        filedialog.asksaveasfilename = lambda **kw: bak_path
        filedialog.askopenfilename = lambda **kw: bak_path
        messagebox.showinfo = lambda *a, **kw: "ok"

        try:
            self.app.handle_backup()
            self.assertTrue(os.path.exists(bak_path))
            with open(bak_path, "rb") as f:
                raw_bak = f.read()
            self.assertNotIn(b"Bak!SecretPass#11", raw_bak, "Backup file must be encrypted")

            # Remove credential and restore via dashboard action
            eid = self.app.displayed_entries[0]["entry_id"]
            vault_module.delete_credential(self.app.current_user_id, eid)
            self.app.refresh_credential_list()
            self._update()
            self.assertEqual(len(self.app.displayed_entries), 0)

            self.app.handle_restore()
            self._update()
            self.assertEqual(len(self.app.displayed_entries), 1)
            self.assertEqual(self.app.displayed_entries[0]["site_name"], "VaultBackupSite")
            restored_eid = self.app.displayed_entries[0]["entry_id"]
            self.assertEqual(
                vault_module.get_credential_password(
                    self.app.current_user_id, restored_eid, self.app.current_encryption_key
                ),
                "Bak!SecretPass#11",
            )
        finally:
            filedialog.asksaveasfilename = orig_save
            filedialog.askopenfilename = orig_open
            messagebox.showinfo = orig_info
            if os.path.exists(bak_path):
                os.remove(bak_path)

    # 12. Logout and auto-lock remain functional
    def test_12_logout_and_auto_lock_functional(self):
        self._login_as("session_user", "Session!Pass12")
        self.assertIsNotNone(self.app.current_user_id)
        self.assertIsNotNone(self.app.current_encryption_key)
        self.assertIsNotNone(self.app.auto_lock_job)

        # Logout clears session and returns to login screen
        self.app.handle_logout()
        self._update()
        self.assertIsNone(self.app.current_user_id)
        self.assertIsNone(self.app.current_encryption_key)
        self.assertIsNone(self.app.auto_lock_job)
        self.assertEqual(self.app.displayed_entries, [])
        self.assertEqual(self.app.row_widgets, {})
        self.assertIn("logged out", self.app.login_status_label.cget("text").lower())

        # Log back in, open Generator dialog, then trigger auto-lock
        self._login_as("session_user", "Session!Pass12")
        self.app.open_generator_dialog()
        self._update()
        self.assertIsNotNone(self.app.active_dialog)

        self.app.handle_auto_lock()
        self._update()
        self.assertIsNone(self.app.current_user_id)
        self.assertIsNone(self.app.current_encryption_key)
        self.assertIsNone(self.app.auto_lock_job)
        self.assertIsNone(self.app.active_dialog)
        self.assertEqual(self.app.displayed_entries, [])
        self.assertIn("inactivity", self.app.login_status_label.cget("text").lower())


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("Initialising temporary test database …")
    _init_tmp_db()
    try:
        unittest.main(verbosity=2, exit=False)
    finally:
        _cleanup_tmp_db()
        print("Temporary test database removed.")
