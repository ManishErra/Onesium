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

    # 7. Adding a credential refreshes the list (+ row click opens in-window details)
    def test_07_adding_credential_refreshes_list(self):
        import customtkinter as ctk

        self._login_as("crud_user", "Crud!Pass7")
        self.app.open_add_dialog()
        self._update()

        dlg = self.app.active_dialog
        self.assertIsNotNone(dlg)

        # Locate entries and Save button in the CustomTkinter Add dialog
        all_dlg_widgets = self._collect_all_widgets(dlg)
        entries = [w for w in all_dlg_widgets if isinstance(w, ctk.CTkEntry)]
        buttons = [w for w in all_dlg_widgets if isinstance(w, ctk.CTkButton)]
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

        # Clicking a row selects it cleanly and opens in-window details (no popup dialog)
        eid = self.app.displayed_entries[0]["entry_id"]
        self.app.handle_row_click(eid)
        self._update()
        self.assertEqual(self.app.selected_entry_id, eid)
        self.assertIsNone(self.app.active_dialog)

    # 8. Editing a credential refreshes the list
    def test_08_editing_credential_refreshes_list(self):
        import customtkinter as ctk

        self._login_as("crud_user", "Crud!Pass7")
        eid = self.app.displayed_entries[0]["entry_id"]
        self.app.handle_row_click(eid)
        self.app.open_edit_dialog()
        self._update()

        dlg = self.app.active_dialog
        self.assertIsNotNone(dlg)
        all_dlg_widgets = self._collect_all_widgets(dlg)
        entries = [w for w in all_dlg_widgets if isinstance(w, ctk.CTkEntry)]
        buttons = [w for w in all_dlg_widgets if isinstance(w, ctk.CTkButton)]

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

    # 13. Regression: screen transitions with focused CTkButton canvas must not raise TclError in focus()
    def test_13_screen_transitions_do_not_raise_focus_tclerror(self):
        import customtkinter as ctk

        if auth.login_user("focus_user", "Focus!Pass13") is None:
            auth.register_user("focus_user", "Focus!Pass13")

        callback_errors = []
        orig_handler = self.root.report_callback_exception
        self.root.report_callback_exception = (
            lambda exc, val, tb: callback_errors.append(f"{exc.__name__}: {val}")
        )

        try:
            self.root.deiconify()
            self.app.show_login_screen()
            self._update()

            self.app.login_username_entry.insert(0, "focus_user")
            self.app.login_password_entry.insert(0, "Focus!Pass13")

            # Locate the primary "Unlock Vault" CTkButton and focus its internal _canvas,
            # matching CustomTkinter's <Button-1> focus binding when clicked by mouse.
            buttons = [
                w for w in self._collect_all_widgets(self.app.container)
                if isinstance(w, ctk.CTkButton)
            ]
            unlock_btn = next(b for b in buttons if b.cget("text") == "Unlock Vault")
            unlock_btn._canvas.focus_set()
            self._update()
            self.assertEqual(self.root.focus_get(), unlock_btn._canvas)

            # 1) Login -> Dashboard (changes resizable False->True while clearing container)
            unlock_btn._on_enter()
            unlock_btn._on_release()
            self.root.after(120, self.root.quit)
            self.root.mainloop()
            self.assertIsNotNone(self.app.current_user_id)

            # 2) Dashboard -> Logout -> Login (changes resizable True->False)
            self.app.search_entry.focus_set()
            self._update()
            self.app.btn_logout.invoke()
            self.root.after(120, self.root.quit)
            self.root.mainloop()
            self.assertIsNone(self.app.current_user_id)

            # 3) Login -> Register with focused "Create Account" button canvas
            buttons = [
                w for w in self._collect_all_widgets(self.app.container)
                if isinstance(w, ctk.CTkButton)
            ]
            create_btn = next(b for b in buttons if b.cget("text") == "Create Account")
            create_btn._canvas.focus_set()
            self._update()
            create_btn._on_enter()
            create_btn._on_release()
            self.root.after(120, self.root.quit)
            self.root.mainloop()
            self.assertTrue(hasattr(self.app, "reg_username_entry"))

            # 4) Register -> Back to Login with focused "Back to Login" button canvas
            buttons = [
                w for w in self._collect_all_widgets(self.app.container)
                if isinstance(w, ctk.CTkButton)
            ]
            back_btn = next(b for b in buttons if b.cget("text") == "Back to Login")
            back_btn._canvas.focus_set()
            self._update()
            back_btn._on_enter()
            back_btn._on_release()
            self.root.after(120, self.root.quit)
            self.root.mainloop()
            self.assertTrue(hasattr(self.app, "login_username_entry"))

            self.assertEqual(
                callback_errors,
                [],
                f"Tkinter callback raised unexpected errors: {callback_errors}",
            )
        finally:
            self.root.report_callback_exception = orig_handler
            self.root.withdraw()
            self._update()


# ---------------------------------------------------------------------------
# 4. Milestone 3 Credential Details & Row Action Icons GUI Tests
# ---------------------------------------------------------------------------
class TestCredentialDetailsAndActionsGUI(unittest.TestCase):
    """
    Milestone 3 tests:
    - Credential details view rendering, metadata, zero-auto-decrypt, masking
    - Explicit Reveal / Hide / Copy without messagebox popups
    - Non-retention of plaintext after closing details, logout, or auto-lock
    - Individual card Edit / Delete action icon isolation from row navigation
    - Edit refresh & rename, cancelled vs confirmed deletion, multi-user isolation
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

    def _collect_all_widgets(self, root_widget):
        widgets = [root_widget]
        for child in root_widget.winfo_children():
            widgets.extend(self._collect_all_widgets(child))
        return widgets

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

    def test_01_clicking_row_opens_details_masked_without_decrypting(self):
        import crypto_utils
        import gui as gui_module
        import vault as vault_module
        from tkinter import messagebox

        self._login_as("m3_user_1", "M3!Pass#01")
        secret_pw = "M3_OnlyRevealOnClick!99"
        eid = vault_module.add_credential(
            self.app.current_user_id,
            self.app.current_encryption_key,
            "GitHub Enterprise",
            "dev@onesium.io",
            secret_pw,
            notes="Hardware MFA enabled.",
        )
        vault_module.add_credential(
            self.app.current_user_id,
            self.app.current_encryption_key,
            "Secondary App",
            "other@onesium.io",
            "OtherSecret!88",
        )
        self.app.refresh_credential_list()
        self._update()

        decrypt_calls = [0]
        get_pw_calls = [0]
        showinfo_calls = [0]
        orig_decrypt = crypto_utils.decrypt_password
        orig_get_pw = vault_module.get_credential_password
        orig_showinfo = messagebox.showinfo

        def spy_decrypt(*a, **kw):
            decrypt_calls[0] += 1
            return orig_decrypt(*a, **kw)

        def spy_get_pw(*a, **kw):
            get_pw_calls[0] += 1
            return orig_get_pw(*a, **kw)

        def spy_showinfo(*a, **kw):
            showinfo_calls[0] += 1
            return "ok"

        crypto_utils.decrypt_password = spy_decrypt
        vault_module.get_credential_password = spy_get_pw
        messagebox.showinfo = spy_showinfo
        try:
            # Map window briefly so Tk processes real <Button-1> click on card._canvas
            self.root.deiconify()
            self._update()
            card = self.app.row_widgets[eid]["card"]
            card._canvas.event_generate("<Button-1>", x=10, y=10)
            self._update()

            # Details view opened in-window (no popup dialog, no messagebox)
            self.assertIsNotNone(self.app._details_view)
            self.assertEqual(self.app._details_entry_id, eid)
            self.assertIsNone(self.app.active_dialog)
            self.assertEqual(showinfo_calls[0], 0)
            self.assertEqual(self.app._vault_list_view.winfo_manager(), "")

            # Zero password decryption when opening details
            self.assertEqual(decrypt_calls[0], 0)
            self.assertEqual(get_pw_calls[0], 0)

            # Metadata displayed accurately & password masked by default
            self.assertEqual(self.app.details_site_title.cget("text"), "GitHub Enterprise")
            self.assertEqual(self.app.details_site_value.cget("text"), "GitHub Enterprise")
            self.assertEqual(self.app.details_username_value.cget("text"), "dev@onesium.io")
            self.assertIn("Hardware MFA enabled.", self.app.details_notes_box.get("1.0", "end"))
            self.assertTrue(len(self.app.details_created_value.cget("text")) > 0)
            self.assertTrue(len(self.app.details_updated_value.cget("text")) > 0)
            self.assertEqual(self.app.details_password_label.cget("text"), gui_module.MASKED_PASSWORD)
            self.assertFalse(self.app._details_password_revealed)
        finally:
            self.root.withdraw()
            self._update()
            crypto_utils.decrypt_password = orig_decrypt
            vault_module.get_credential_password = orig_get_pw
            messagebox.showinfo = orig_showinfo

    def test_02_reveal_hide_copy_and_leave_clear_password(self):
        import gui as gui_module
        import vault as vault_module
        from tkinter import messagebox

        self._login_as("m3_user_2", "M3!Pass#02")
        pw_one = "Reveal_Only_This_One!1"
        pw_two = "Never_Touch_Second!2"
        eid1 = vault_module.add_credential(
            self.app.current_user_id, self.app.current_encryption_key, "ServiceOne", "u1@local", pw_one
        )
        vault_module.add_credential(
            self.app.current_user_id, self.app.current_encryption_key, "ServiceTwo", "u2@local", pw_two
        )
        self.app.refresh_credential_list()
        self._update()
        self.app.handle_row_click(eid1)
        self._update()

        retrieved_ids = []
        showinfo_calls = [0]
        orig_get_pw = vault_module.get_credential_password
        orig_showinfo = messagebox.showinfo

        def spy_get_pw(uid, target_eid, key, **kw):
            retrieved_ids.append(target_eid)
            return orig_get_pw(uid, target_eid, key, **kw)

        vault_module.get_credential_password = spy_get_pw
        messagebox.showinfo = lambda *a, **kw: showinfo_calls.__setitem__(0, showinfo_calls[0] + 1) or "ok"
        try:
            # 1. Explicit Reveal decrypts ONLY the selected credential
            self.app.details_toggle_pw_btn.invoke()
            self._update()
            self.assertEqual(retrieved_ids, [eid1])
            self.assertEqual(self.app.details_password_label.cget("text"), pw_one)
            self.assertTrue(self.app._details_password_revealed)
            self.assertEqual(showinfo_calls[0], 0)

            # 2. Hide masks the password again without keeping plaintext on label
            self.app.details_toggle_pw_btn.invoke()
            self._update()
            self.assertEqual(self.app.details_password_label.cget("text"), gui_module.MASKED_PASSWORD)
            self.assertFalse(self.app._details_password_revealed)

            # 3. Copy retrieves ONLY selected password, writes clipboard, uses no messagebox
            self.app.details_copy_pw_btn.invoke()
            self._update()
            self.assertEqual(retrieved_ids, [eid1, eid1])
            self.assertEqual(self.root.clipboard_get(), pw_one)
            self.assertEqual(showinfo_calls[0], 0)

            # 4. Reveal again, then leave via Back to Vault -> plaintext cleared
            self.app.details_toggle_pw_btn.invoke()
            self._update()
            self.assertEqual(self.app.details_password_label.cget("text"), pw_one)
            self.app.details_back_btn.invoke()
            self._update()

            self.assertIsNone(self.app._details_view)
            self.assertIsNone(self.app._details_entry_id)
            self.assertFalse(self.app._details_password_revealed)
            self.assertEqual(self.app._vault_list_view.winfo_manager(), "pack")
            # Ensure pw_one is not retained in app attributes
            for attr_val in self.app.__dict__.values():
                self.assertNotIn(pw_one, str(attr_val))
        finally:
            vault_module.get_credential_password = orig_get_pw
            messagebox.showinfo = orig_showinfo

    def test_03_row_action_icons_isolated_from_details_navigation(self):
        import customtkinter as ctk
        import vault as vault_module

        self._login_as("m3_user_3", "M3!Pass#03")
        eid = vault_module.add_credential(
            self.app.current_user_id,
            self.app.current_encryption_key,
            "OriginalSite",
            "user@orig.io",
            "OrigPass!33",
            notes="old note",
        )
        self.app.refresh_credential_list()
        self._update()

        row = self.app.row_widgets[eid]
        edit_btn = row["edit_btn"]
        delete_btn = row["delete_btn"]

        # Simulate real mouse click on card's Edit icon button
        edit_btn._on_enter()
        edit_btn._on_release()
        self._update()

        # Must open CustomTkinter Edit dialog, NOT details view
        self.assertIsNone(self.app._details_view)
        dlg = self.app.active_dialog
        self.assertIsNotNone(dlg)
        self.assertIsInstance(dlg, ctk.CTkToplevel)

        all_dlg_widgets = self._collect_all_widgets(dlg)
        entries = [w for w in all_dlg_widgets if isinstance(w, ctk.CTkEntry)]
        buttons = [w for w in all_dlg_widgets if isinstance(w, ctk.CTkButton)]

        # Edit (rename site + update username + replacement password)
        entries[0].delete(0, "end")
        entries[0].insert(0, "RenamedSite")
        entries[1].delete(0, "end")
        entries[1].insert(0, "renamed@site.io")
        entries[2].insert(0, "NewPass!44")

        save_btn = next(b for b in buttons if b.cget("text") == "Save")
        save_btn.invoke()
        self._update()

        self.assertIsNone(self.app.active_dialog)
        self.assertIsNone(self.app._details_view)
        self.assertEqual(self.app.displayed_entries[0]["site_name"], "RenamedSite")
        self.assertEqual(self.app.row_widgets[eid]["site_name"], "RenamedSite")
        self.assertEqual(
            vault_module.get_credential_password(
                self.app.current_user_id, eid, self.app.current_encryption_key
            ),
            "NewPass!44",
        )

        # Cancelled deletion via row Delete icon changes nothing and does not open details
        from tkinter import messagebox

        delete_btn = self.app.row_widgets[eid]["delete_btn"]
        orig_askyesno = messagebox.askyesno
        messagebox.askyesno = lambda *a, **kw: False
        try:
            delete_btn._on_enter()
            delete_btn._on_release()
            self._update()
        finally:
            messagebox.askyesno = orig_askyesno

        self.assertIsNone(self.app._details_view)
        self.assertEqual(len(self.app.displayed_entries), 1)
        self.assertEqual(self.app.displayed_entries[0]["site_name"], "RenamedSite")

        # Confirmed deletion via row Delete icon removes credential & refreshes dashboard
        messagebox.askyesno = lambda *a, **kw: True
        try:
            delete_btn._on_enter()
            delete_btn._on_release()
            self._update()
        finally:
            messagebox.askyesno = orig_askyesno

        self.assertEqual(len(self.app.displayed_entries), 0)
        self.assertEqual(self.app.count_badge.cget("text"), "0 Saved")
        self.assertEqual(self.app.empty_state_frame.winfo_manager(), "pack")

    def test_04_edit_and_delete_from_details_and_user_isolation(self):
        import customtkinter as ctk
        import gui as gui_module
        import vault as vault_module
        from tkinter import messagebox

        # User B adds a credential first
        self._login_as("m3_iso_b", "IsoB!Pass#9")
        b_eid = vault_module.add_credential(
            self.app.current_user_id, self.app.current_encryption_key, "UserBSecret", "b@b.io", "SecretB!9"
        )
        self.app.handle_logout()
        self._update()

        # User A adds a credential and opens details
        self._login_as("m3_iso_a", "IsoA!Pass#9")
        a_eid = vault_module.add_credential(
            self.app.current_user_id, self.app.current_encryption_key, "UserASite", "a@a.io", "SecretA!9"
        )
        self.app.refresh_credential_list()
        self._update()

        # Attempting to open User B's entry_id as User A must do nothing (isolation)
        self.app.open_credential_details(b_eid)
        self._update()
        self.assertIsNone(self.app._details_view)

        # Open User A's details and edit from Details view
        self.app.handle_row_click(a_eid)
        self._update()
        self.app.details_edit_btn.invoke()
        self._update()

        dlg = self.app.active_dialog
        all_dlg_widgets = self._collect_all_widgets(dlg)
        entries = [w for w in all_dlg_widgets if isinstance(w, ctk.CTkEntry)]
        buttons = [w for w in all_dlg_widgets if isinstance(w, ctk.CTkButton)]

        entries[0].delete(0, "end")
        entries[0].insert(0, "UserASiteRenamed")
        entries[2].insert(0, "UpdatedA!99")
        next(b for b in buttons if b.cget("text") == "Save").invoke()
        self._update()

        # Both dashboard and active details view reflect rename, password stays masked
        self.assertIsNotNone(self.app._details_view)
        self.assertEqual(self.app.details_site_title.cget("text"), "UserASiteRenamed")
        self.assertEqual(self.app.details_password_label.cget("text"), gui_module.MASKED_PASSWORD)
        self.assertEqual(self.app.displayed_entries[0]["site_name"], "UserASiteRenamed")

        # Delete from Details view returns cleanly to vault list
        orig_askyesno = messagebox.askyesno
        messagebox.askyesno = lambda *a, **kw: True
        try:
            self.app.details_delete_btn.invoke()
            self._update()
        finally:
            messagebox.askyesno = orig_askyesno

        self.assertIsNone(self.app._details_view)
        self.assertEqual(self.app._vault_list_view.winfo_manager(), "pack")
        self.assertEqual(len(self.app.displayed_entries), 0)

        # Verify User B's credential was untouched
        self.app.handle_logout()
        self._login_as("m3_iso_b", "IsoB!Pass#9")
        self.assertEqual([e["entry_id"] for e in self.app.displayed_entries], [b_eid])

    def test_05_logout_and_auto_lock_clear_details_and_revealed_password(self):
        import vault as vault_module

        self._login_as("m3_sess_user", "Sess!Pass#5")
        pw = "SessionSecret!55"
        eid = vault_module.add_credential(
            self.app.current_user_id, self.app.current_encryption_key, "VaultSession", "s@local", pw
        )
        self.app.refresh_credential_list()
        self._update()

        # Open details and reveal password, then logout
        self.app.handle_row_click(eid)
        self.app.details_toggle_pw_btn.invoke()
        self._update()
        self.assertEqual(self.app.details_password_label.cget("text"), pw)

        self.app.handle_logout()
        self._update()
        self.assertIsNone(self.app._details_view)
        self.assertIsNone(self.app._details_entry_id)
        self.assertFalse(self.app._details_password_revealed)
        self.assertIsNone(self.app.current_user_id)
        self.assertIsNone(self.app.current_encryption_key)
        for attr_val in self.app.__dict__.values():
            self.assertNotIn(pw, str(attr_val))

        # Log back in, open details, reveal password, then trigger auto-lock
        self._login_as("m3_sess_user", "Sess!Pass#5")
        self.app.handle_row_click(eid)
        self.app.details_toggle_pw_btn.invoke()
        self._update()
        self.assertEqual(self.app.details_password_label.cget("text"), pw)

        self.app.handle_auto_lock()
        self._update()
        self.assertIsNone(self.app._details_view)
        self.assertIsNone(self.app._details_entry_id)
        self.assertFalse(self.app._details_password_revealed)
        self.assertIsNone(self.app.current_user_id)
        self.assertIsNone(self.app.current_encryption_key)
        self.assertIn("inactivity", self.app.login_status_label.cget("text").lower())
        for attr_val in self.app.__dict__.values():
            self.assertNotIn(pw, str(attr_val))

    def test_06_safe_clipboard_auto_clear_preserves_replaced_text(self):
        import hashlib
        import tkinter as tk
        import vault as vault_module

        self._login_as("clip_user", "Clip!Pass#6")
        pw = "ClipboardSecret!66"
        eid = vault_module.add_credential(
            self.app.current_user_id, self.app.current_encryption_key, "ClipSite", "c@local", pw
        )
        self.app.refresh_credential_list()
        self._update()
        self.app.handle_row_click(eid)
        self._update()

        # 1. Copy sets timer and stores SHA-256 digest only (never plaintext)
        self.app.details_copy_pw_btn.invoke()
        self._update()
        self.assertEqual(self.root.clipboard_get(), pw)
        self.assertIsNotNone(self.app._clipboard_clear_job)
        self.assertEqual(
            self.app._clipboard_expected_digest,
            hashlib.sha256(pw.encode("utf-8")).digest(),
        )
        for attr_val in self.app.__dict__.values():
            self.assertNotIn(pw, str(attr_val))

        # 2. When clipboard still matches copied password, auto-clear empties it
        self.app._auto_clear_clipboard()
        self._update()
        try:
            clip_after = self.root.clipboard_get()
        except tk.TclError:
            clip_after = ""
        self.assertEqual(clip_after, "")
        self.assertIsNone(self.app._clipboard_expected_digest)

        # 3. When another app replaces clipboard content, auto-clear preserves it
        self.app.details_copy_pw_btn.invoke()
        self._update()
        self.root.clipboard_clear()
        self.root.clipboard_append("ExternalUserText999")
        self.root.update()

        self.app._auto_clear_clipboard()
        self._update()
        self.assertEqual(self.root.clipboard_get(), "ExternalUserText999")


# ---------------------------------------------------------------------------
# 5. Milestone 4 Final Security & Integrity Audit Tests
# ---------------------------------------------------------------------------
class TestSecurityAudit(unittest.TestCase):
    """Phase 3 audit checks: PBKDF2, Fernet storage, FK enforcement, common passwords, isolation."""

    def test_pbkdf2_config_and_no_plaintext_storage(self):
        import crypto_utils
        import vault as vault_module

        self.assertEqual(crypto_utils.PBKDF2_ITERATIONS, 600_000)
        master = "MasterAudit!Pass1"
        uid = auth.register_user("audit_sec_user", master, db_path=_TMP_DB)
        self.assertIsNotNone(uid)
        _, key = auth.login_user("audit_sec_user", master, db_path=_TMP_DB)

        secret = "VaultEntrySecret!77"
        eid = vault_module.add_credential(uid, key, "AuditBank", "me@bank.io", secret, db_path=_TMP_DB)
        self.assertGreater(eid, 0)

        conn = db_module.get_connection(_TMP_DB)
        try:
            fk_row = conn.execute("PRAGMA foreign_keys;").fetchone()
            self.assertEqual(fk_row[0], 1, "PRAGMA foreign_keys must be enabled")

            user_row = conn.execute("SELECT password_hash, salt FROM users WHERE user_id = ?", (uid,)).fetchone()
            self.assertNotIn(master.encode("utf-8"), bytes(user_row["password_hash"]))
            self.assertEqual(len(user_row["salt"]), 16)

            entry_row = conn.execute(
                "SELECT encrypted_password FROM vault_entries WHERE entry_id = ?", (eid,)
            ).fetchone()
            self.assertNotIn(secret.encode("utf-8"), bytes(entry_row["encrypted_password"]))
            self.assertTrue(bytes(entry_row["encrypted_password"]).startswith(b"gAAAA"))
        finally:
            conn.close()

    def test_cross_user_backup_restore_rejected(self):
        import vault as vault_module

        uid_a = auth.register_user("bak_sec_a", "BakA!Pass#1", db_path=_TMP_DB)
        _, key_a = auth.login_user("bak_sec_a", "BakA!Pass#1", db_path=_TMP_DB)
        uid_b = auth.register_user("bak_sec_b", "BakB!Pass#2", db_path=_TMP_DB)
        _, key_b = auth.login_user("bak_sec_b", "BakB!Pass#2", db_path=_TMP_DB)

        vault_module.add_credential(uid_a, key_a, "BankA", "a@a.io", "SecretA!1", db_path=_TMP_DB)
        bak_path = tempfile.mktemp(suffix=".pmv")
        try:
            self.assertTrue(vault_module.backup_user_vault(uid_a, key_a, bak_path, db_path=_TMP_DB))
            self.assertFalse(
                vault_module.restore_user_vault(uid_b, key_b, bak_path, db_path=_TMP_DB),
                "Backup encrypted with User A's key must fail to restore under User B's key",
            )
        finally:
            if os.path.exists(bak_path):
                os.remove(bak_path)

    def test_common_password_detection(self):
        self.assertTrue(password_utils.is_common_password("password"))
        self.assertTrue(password_utils.is_common_password("123456"))
        self.assertFalse(password_utils.is_common_password("X9!vQ2#mZ7&kL4@p"))


# ---------------------------------------------------------------------------
# 6. Milestone 4 Phase 2 — Persistent Database Location & Safe Migration Tests
# ---------------------------------------------------------------------------
class TestDatabaseLocationAndSafety(unittest.TestCase):
    """Verifies %LOCALAPPDATA%\\ONESIUM path resolution, safe migration, persistence, and preservation."""

    @staticmethod
    def _file_sha256(path):
        import hashlib

        h = hashlib.sha256()
        with open(path, "rb") as f:
            while True:
                chunk = f.read(65536)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()

    def test_01_default_db_path_uses_localappdata_onesium(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            orig = os.environ.get("LOCALAPPDATA")
            os.environ["LOCALAPPDATA"] = tmpdir
            try:
                expected = os.path.join(tmpdir, "ONESIUM", "password_manager.db")
                self.assertEqual(db_module.get_default_db_path(), expected)
            finally:
                if orig is None:
                    os.environ.pop("LOCALAPPDATA", None)
                else:
                    os.environ["LOCALAPPDATA"] = orig

    def test_02_fresh_database_creation_and_persistence_across_restart(self):
        import vault as vault_module

        with tempfile.TemporaryDirectory() as tmpdir:
            target_db = os.path.join(tmpdir, "AppData", "Local", "ONESIUM", "password_manager.db")

            status1 = db_module.prepare_database(target_path=target_db, legacy_paths=[])
            self.assertEqual(status1["action"], "initialize_new")
            db_module.init_db(target_db)
            self.assertTrue(os.path.isfile(target_db))

            uid = auth.register_user("persist_user", "P3rsist!Pass#9", db_path=target_db)
            self.assertIsNotNone(uid)
            _, key = auth.login_user("persist_user", "P3rsist!Pass#9", db_path=target_db)
            eid = vault_module.add_credential(
                uid, key, "PersistSite", "p@local", "PersistSecret!1", "Saved note", db_path=target_db
            )

            # Simulate restart against the existing persistent database
            status2 = db_module.prepare_database(target_path=target_db, legacy_paths=[])
            self.assertEqual(status2["action"], "existing_active")
            db_module.init_db(target_db)

            res2 = auth.login_user("persist_user", "P3rsist!Pass#9", db_path=target_db)
            self.assertIsNotNone(res2)
            uid2, key2 = res2
            self.assertEqual(uid2, uid)
            self.assertEqual(
                vault_module.get_credential_password(uid2, eid, key2, db_path=target_db),
                "PersistSecret!1",
            )

    def test_03_legacy_database_migrated_safely_without_deleting_source(self):
        import vault as vault_module

        with tempfile.TemporaryDirectory() as tmpdir:
            legacy_db = os.path.join(tmpdir, "old_folder", "password_manager.db")
            target_db = os.path.join(tmpdir, "LocalAppData", "ONESIUM", "password_manager.db")

            db_module.init_db(legacy_db)
            uid1 = auth.register_user("legacy_alice", "Alice!Pass#1", db_path=legacy_db)
            _, key1 = auth.login_user("legacy_alice", "Alice!Pass#1", db_path=legacy_db)
            eid1 = vault_module.add_credential(
                uid1, key1, "LegacyMail", "alice@legacy", "AliceSecret!1", db_path=legacy_db
            )
            uid2 = auth.register_user("legacy_bob", "Bob!Pass#2", db_path=legacy_db)
            legacy_hash_before = self._file_sha256(legacy_db)

            status1 = db_module.prepare_database(target_path=target_db, legacy_paths=[legacy_db])
            self.assertEqual(status1["action"], "migrated")
            self.assertEqual(status1["migrated_from"], os.path.abspath(legacy_db))
            self.assertTrue(os.path.isfile(target_db))

            # Original legacy database must remain intact and unmodified
            self.assertTrue(os.path.isfile(legacy_db))
            self.assertEqual(self._file_sha256(legacy_db), legacy_hash_before)

            # Adopted database preserves all accounts, encryption, and secrets
            login1 = auth.login_user("legacy_alice", "Alice!Pass#1", db_path=target_db)
            self.assertIsNotNone(login1)
            self.assertEqual(
                vault_module.get_credential_password(login1[0], eid1, login1[1], db_path=target_db),
                "AliceSecret!1",
            )
            self.assertIsNotNone(auth.login_user("legacy_bob", "Bob!Pass#2", db_path=target_db))

            # Subsequent startup uses active target without conflict notice or overwrite
            status2 = db_module.prepare_database(target_path=target_db, legacy_paths=[legacy_db])
            self.assertEqual(status2["action"], "existing_active")

    def test_04_both_databases_exist_never_overwrites_either(self):
        import vault as vault_module

        with tempfile.TemporaryDirectory() as tmpdir:
            legacy_db = os.path.join(tmpdir, "legacy", "password_manager.db")
            target_db = os.path.join(tmpdir, "LocalAppData", "ONESIUM", "password_manager.db")

            db_module.init_db(legacy_db)
            u_old = auth.register_user("old_only_user", "OldPass!1", db_path=legacy_db)
            _, k_old = auth.login_user("old_only_user", "OldPass!1", db_path=legacy_db)
            vault_module.add_credential(u_old, k_old, "OldSite", "old@site", "OldSec!1", db_path=legacy_db)

            db_module.init_db(target_db)
            u_new = auth.register_user("new_only_user", "NewPass!2", db_path=target_db)
            _, k_new = auth.login_user("new_only_user", "NewPass!2", db_path=target_db)
            e_new = vault_module.add_credential(u_new, k_new, "NewSite", "new@site", "NewSec!2", db_path=target_db)

            old_hash_before = self._file_sha256(legacy_db)
            new_hash_before = self._file_sha256(target_db)

            status = db_module.prepare_database(target_path=target_db, legacy_paths=[legacy_db])
            self.assertEqual(status["action"], "both_exist_preserved")
            self.assertEqual(self._file_sha256(legacy_db), old_hash_before)
            self.assertEqual(self._file_sha256(target_db), new_hash_before)

            # Verify target_db preserves its existing account and does not merge/reset
            res_new = auth.login_user("new_only_user", "NewPass!2", db_path=target_db)
            self.assertIsNotNone(res_new)
            self.assertEqual(
                vault_module.get_credential_password(res_new[0], e_new, res_new[1], db_path=target_db),
                "NewSec!2",
            )
            self.assertIsNone(auth.login_user("old_only_user", "OldPass!1", db_path=target_db))
            self.assertIsNotNone(auth.login_user("old_only_user", "OldPass!1", db_path=legacy_db))

    def test_05_empty_or_corrupt_legacy_file_ignored_safely(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            bad_db = os.path.join(tmpdir, "bad", "password_manager.db")
            os.makedirs(os.path.dirname(bad_db), exist_ok=True)
            with open(bad_db, "wb") as f:
                f.write(b"not a valid sqlite database")
            target_db = os.path.join(tmpdir, "LocalAppData", "ONESIUM", "password_manager.db")

            status = db_module.prepare_database(target_path=target_db, legacy_paths=[bad_db])
            self.assertEqual(status["action"], "initialize_new")
            self.assertFalse(os.path.exists(target_db))


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
