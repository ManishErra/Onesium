# ONESIUM — Viva Preparation Guide

Quick-reference study notes aligned strictly with ONESIUM's actual codebase (`main.py`, `db.py`, `crypto_utils.py`, `auth.py`, `vault.py`, `password_utils.py`, `gui.py`).

---

## 1. Core Project Concepts

- **What is ONESIUM?** An offline, multi-user Windows desktop credential vault built in Python using CustomTkinter for UI, SQLite for local persistence, and `cryptography` (`PBKDF2HMAC` + `Fernet`) for key derivation and authenticated encryption.
- **Why offline?** Eliminates network attack surface, cloud account breaches, and third-party server trust; all data remains locally under `%LOCALAPPDATA%\ONESIUM\password_manager.db` on the user's machine.

---

## 2. Module-by-Module Explanation

| Module | Responsibility |
|---|---|
| `main.py` | Entry point: guards missing `None` stdout/stderr streams via `_NullStream` for PyInstaller `--windowed` builds, calls `db.prepare_database()` and `db.init_db()`, configures CustomTkinter dark mode and blue theme, creates `ctk.CTk()` root, instantiates `PasswordManagerApp(root)`, and runs `mainloop()`. |
| `db.py` | SQLite persistence and migration layer (`get_default_db_path`, `get_legacy_db_candidates`, `prepare_database`, `get_connection`, `init_db`, `create_user`, `get_user_by_username`, `add_entry`, `get_entries_for_user`, `update_entry`, `delete_entry`). Uses `%LOCALAPPDATA%\ONESIUM\password_manager.db`, enables foreign keys, and uses parameterized SQL. |
| `crypto_utils.py` | Cryptographic primitives: `generate_salt()`, `hash_password()`, `derive_key()`, `encrypt_password()`, `decrypt_password()`, `encrypt_data()`, `decrypt_data()`. |
| `auth.py` | User registration (`register_user`) and constant-time login verification + key derivation (`login_user`). |
| `vault.py` | Authenticated vault operations (`add_credential`, `get_credentials`, `get_credential_password`, `update_credential`, `delete_credential`, `search_credentials`, `backup_user_vault`, `restore_user_vault`). |
| `password_utils.py` | Cryptographically secure password generation (`generate_password` via `secrets`), deterministic strength scoring (`check_password_strength`), and `common_passwords.txt` check (`is_common_password` with `sys._MEIPASS` support). |
| `gui.py` | CustomTkinter presentation layer: login/registration screens, dashboard sidebar and credential cards, in-window details view, Add/Edit/Generator modals, 5-minute auto-lock, and 30-second SHA-256-checked clipboard clearing. |

---

## 3. Database Explanation (`db.py`)

Two normalized tables stored locally at `%LOCALAPPDATA%\ONESIUM\password_manager.db` (`db.get_default_db_path()`) with `PRAGMA foreign_keys = ON`:

1. **`users`**: `user_id` (PK), `username` (`UNIQUE NOT NULL`), `password_hash` (`TEXT NOT NULL` — stores the 32 derived bytes from `PBKDF2HMAC`), `salt` (`BLOB NOT NULL` — 16 random bytes), `created_at`.
2. **`vault_entries`**: `entry_id` (PK), `user_id` (FK -> `users.user_id ON DELETE CASCADE`), `site_name`, `username_field`, `encrypted_password` (`BLOB NOT NULL`), `notes`, `created_at`, `updated_at`.
   - Entries are retrieved sorted alphabetically (`ORDER BY site_name COLLATE NOCASE ASC`).
   - Every query uses parameterized `?` bindings to prevent SQL injection and scopes by `user_id` for strict multi-user isolation.

### Legacy Database Migration & Safety
- Prior builds used a relative path `password_manager.db`. Moving to `%LOCALAPPDATA%\ONESIUM\password_manager.db` prevents silent empty vaults when working directories change, avoids write failures under read-only install directories, and isolates SQLite files from cloud-synced project folders.
- On startup, `db.prepare_database()` safely copies any valid legacy `password_manager.db` into `%LOCALAPPDATA%\ONESIUM\password_manager.db` using SQLite's online `backup()` API via a verified staging file, without deleting or modifying the legacy file.
- If both an active AppData database and an un-migrated populated legacy database exist simultaneously, ONESIUM preserves both untouched without automatic overwriting.

---

## 4. PBKDF2 and Fernet (`crypto_utils.py`)

- **PBKDF2-HMAC-SHA256 (`PBKDF2HMAC`):**
  - Stretches the master password with a unique 16-byte random salt (`os.urandom(16)`) across **600,000 iterations** to produce a 32-byte output (`KEY_LENGTH = 32`).
  - High iteration count slows offline brute-force and dictionary attacks.
  - Unique random salt ensures identical master passwords for two users produce completely different hashes and keys, defeating rainbow tables.
- **Fernet (`cryptography.fernet.Fernet`):**
  - Symmetric authenticated encryption using **AES-128-CBC with PKCS7 padding and HMAC-SHA256 authentication**.
  - Key is URL-safe base64-encoded 32 bytes (16-byte HMAC-SHA256 signing key + 16-byte AES-128 encryption key).
  - Provides **confidentiality** (AES-128-CBC) and **integrity/authenticity** (HMAC-SHA256 + timestamp). If ciphertext is tampered with or decrypted with the wrong key, `InvalidToken` is raised.

---

## 5. Password Encryption vs. Hashing

- **Master Password (Verification):** Derived via one-way `PBKDF2HMAC` (`hash_password`) and compared in constant time via `secrets.compare_digest()`. Never decrypted because login only needs verification.
- **Stored Vault Passwords:** Must be retrievable in plaintext when needed, so they are encrypted with `Fernet` using the user's in-memory session key and decrypted only on explicit reveal or copy.

---

## 6. Session Management & Auto-Lock

- On login, `auth.login_user()` returns `(user_id, encryption_key)` which are stored **only in RAM** on `PasswordManagerApp` (`self.current_user_id`, `self.current_encryption_key`). Nothing is written to disk.
- **Auto-Lock (`AUTO_LOCK_MS = 5 * 60 * 1000`):** Every `<Key>` and `<Button>` event resets the `root.after()` countdown. After 5 minutes of inactivity, `handle_auto_lock()` runs `_clear_session_state()`, wiping the encryption key, closing active dialogs and details view, clearing the clipboard, and returning to the login screen.
- **Clipboard Auto-Clear (`CLIPBOARD_CLEAR_MS = 30 * 1000`):** Stores only a SHA-256 digest of the copied secret (`self._clipboard_expected_digest`)—never the plaintext password—and clears the clipboard after 30 seconds only if its current contents still match that digest.

---

## 7. Backup and Restore (`vault.py`)

- **Backup (`backup_user_vault`):** Reads the user's entries from SQLite, base64-encodes each entry's already-encrypted `encrypted_password` token into JSON (`{"version": 1, "entries": [...]}`), encrypts the JSON payload again with `crypto_utils.encrypt_data(raw_json_bytes, key)`, and writes a `.pmv` file. Plaintext passwords are never written to backup files.
- **Restore (`restore_user_vault`):** Reads `.pmv`, decrypts with the user's session key (`InvalidToken` caught if wrong key or tampered file), validates schema (`version == 1`, `entries` list, required string fields, valid base64), and inserts entries into `vault_entries` scoped to the authenticated `user_id`.

---

## 8. Likely Viva Questions & Answers

1. **Q: Why can't you encrypt passwords with AES-ECB or SHA-256 alone?**
   - *A:* SHA-256 is a one-way hash—you could not recover saved site passwords. Plain AES-ECB leaks patterns and lacks integrity verification. Fernet combines AES-128-CBC (fresh random IV per token) with HMAC-SHA256 authentication.
2. **Q: Why use 600,000 PBKDF2 iterations?**
   - *A:* Matches current OWASP guidance for PBKDF2-HMAC-SHA256 to raise offline cracking cost while keeping interactive login fast.
3. **Q: Where is the encryption key stored while running, and what happens on logout?**
   - *A:* Strictly in RAM (`self.current_encryption_key`). Logout and 5-minute auto-lock reset it to `None`, wipe active views/dialogs, clear the clipboard, and return to Login.
4. **Q: Why don't dashboard cards decrypt passwords when loading?**
   - *A:* Minimizes memory exposure of plaintext secrets and improves performance; `vault.get_credentials()` and `open_credential_details()` read metadata only, and `vault.get_credential_password()` runs only when the user clicks Reveal or Copy.
5. **Q: How does ONESIUM prevent SQL injection and cross-user access?**
   - *A:* All SQLite statements in `db.py` use `?` parameterized placeholders, `PRAGMA foreign_keys = ON` is enabled on every connection, and every read/update/delete query filters strictly by `user_id`.
6. **Q: Why does editing a credential require entering a replacement password instead of pre-filling the old one?**
   - *A:* Opening the Edit dialog never decrypts the existing password, reducing shoulder-surfing and unnecessary plaintext exposure in form widgets.
7. **Q: How does clipboard auto-clear avoid erasing unrelated text copied by the user?**
   - *A:* On copy, ONESIUM stores a one-way SHA-256 digest of the copied password. When the 30-second timer fires, it hashes the current clipboard text and clears the clipboard only if `secrets.compare_digest` confirms it still holds the copied secret.
8. **Q: How does `common_passwords.txt` work inside the packaged `Onesium.exe`?**
   - *A:* `password_utils.is_common_password()` checks `sys._MEIPASS` when frozen so it locates the bundled `common_passwords.txt` unpacked by PyInstaller.
9. **Q: Why does ONESIUM store the database in `%LOCALAPPDATA%\ONESIUM` instead of a relative path?**
   - *A:* Relative paths depend on shortcut working directories, fail inside read-only installation folders, and risk OneDrive sync locks. Using `%LOCALAPPDATA%\ONESIUM\password_manager.db` with non-destructive SQLite backup migration keeps existing user vaults safe across launches.
