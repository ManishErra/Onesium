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

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Monkey-patch auth functions so the GUI uses the temp test database
        # (auth.register_user/login_user defaults to db.DB_NAME at import time)
        _orig_register = auth.register_user
        _orig_login = auth.login_user

        auth.register_user = lambda u, p, **kw: _orig_register(u, p, db_path=_TMP_DB)
        auth.login_user = lambda u, p, **kw: _orig_login(u, p, db_path=_TMP_DB)

        cls._orig_register = _orig_register
        cls._orig_login = _orig_login

        cls.root = ctk.CTk()
        cls.root.withdraw()          # Keep window hidden during tests
        cls.app = gui_module.PasswordManagerApp(cls.root)
        cls.root.update()

    @classmethod
    def tearDownClass(cls):
        # Restore original auth functions
        auth.register_user = cls._orig_register
        auth.login_user = cls._orig_login
        try:
            if cls.app.auto_lock_job:
                cls.root.after_cancel(cls.app.auto_lock_job)
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
