# ONESIUM — The Credential Vault

ONESIUM is a strictly offline, multi-user Windows desktop password manager built with Python, CustomTkinter, SQLite, and `cryptography`. Every user vault is isolated locally on disk with PBKDF2-HMAC-SHA256 key derivation and Fernet authenticated encryption.

---

## Features

- **Local Multi-User Accounts:** Create independent user vaults on the same device with unique per-user salts and SQLite user isolation.
- **Zero-Plaintext Storage:** Master passwords are never stored; only a PBKDF2-HMAC-SHA256 derived verification hash and random 16-byte salt are saved. Vault passwords are stored as Fernet ciphertext.
- **Modern Dark-Theme Desktop UI:** CustomTkinter dark-mode interface featuring redesigned login/registration flows, sidebar navigation, search, designed empty states, and custom credential cards.
- **Credential Details View & Quick Row Actions:**
  - Click any credential card to inspect website/application name, username, masked password, notes, created timestamp, and last-updated timestamp inside the main window.
  - Passwords remain masked by default (`••••••••••••`) and are decrypted only upon explicit **Show** or **Copy** interaction.
  - Compact icon-only **Edit** and **Delete** buttons on each card (with confirmation before deletion).
- **Cryptographic Password Generator & Strength Meter:** Uses Python's `secrets` module (`generate_password`) with live strength scoring (`Very Weak` to `Very Strong`) and local `common_passwords.txt` checking.
- **Encrypted Backup & Restore (`.pmv`):** Export and restore a user's encrypted vault entries wrapped in a Fernet-encrypted JSON payload.
- **Automatic Security Controls:**
  - **5-minute inactivity auto-lock:** Clears session encryption keys, closes active dialogs/details, clears the clipboard, and returns to the login screen.
  - **30-second clipboard auto-clear:** Clears copied passwords after 30 seconds only if the clipboard still matches the SHA-256 digest of the copied secret (preserving clipboard content replaced by another app).

---

## Technologies Used

| Component | Technology |
|---|---|
| Language | Python 3.13 |
| Desktop UI | CustomTkinter 6.0.0 (`tkinter` / `Segoe Fluent Icons`) |
| Cryptography | `cryptography` 50.0.1 (`PBKDF2HMAC`, `Fernet`) |
| Local Database | SQLite 3 (`sqlite3` standard library) |
| Packaging | PyInstaller 6.22.3 (`Onesium.exe`) |
| Testing | `unittest` standard library |

---

## Installation (From Source)

1. **Clone the repository:**
   ```powershell
   git clone https://github.com/ManishErra/Onesium.git
   cd Onesium
   ```

2. **Install runtime dependencies:**
   ```powershell
   python -m pip install -r requirements.txt
   ```
   `requirements.txt` includes:
   - `cryptography`
   - `customtkinter`

---

## Running from Source

Launch the application from the project root:

```powershell
python main.py
```

*(If multiple Python installations exist on Windows, use the interpreter where dependencies are installed, e.g. `C:\Users\Manish\AppData\Local\Programs\Python\Python313\python.exe main.py`.)*

To run the automated regression test suite:

```powershell
python test_regression.py
```

---

## Using the Application

1. **Create Account / Login:** Click **Create Account** to register a local username and strong master password, then sign in with **Unlock Vault**.
2. **Add Credentials:** Click **+  Add Credential**, enter the site, username, password (or click **Generate**), and optional notes, then click **Save**.
3. **Search:** Type in the **Search by site or username...** field to filter entries in real time; click the clear (**✕**) button (or press `Esc`) to clear search.
4. **View, Reveal, & Copy:** Click any credential card to open its **Credential Details** view. Click the reveal icon to toggle password visibility, or the copy icon to copy the username or password to the clipboard (passwords auto-clear after 30 seconds).
5. **Edit & Delete:** Use the Edit/Delete icon buttons on any card (or **Edit** / **Delete** inside the details view). Editing updates metadata and sets a replacement password without decrypting the previous password.
6. **Password Generator:** Open **Password Generator** from the sidebar to generate 8–64 character random passwords (backend `password_utils.generate_password()` supports 8–128 characters).
7. **Backup & Restore:** Use **Backup Vault** and **Restore Vault** in the sidebar to export or import encrypted `.pmv` files (restore only succeeds with the matching user account/master key).
8. **Lock & Logout:** Click **Lock & Logout** in the sidebar at any time to wipe the session key and lock the vault.

---

## Security Design

- **Key Derivation & Password Verification (`crypto_utils.py` / `auth.py`):**
  - Random 16-byte salt per user (`os.urandom(16)`).
  - `PBKDF2HMAC` with `SHA-256`, `600,000` iterations, 32-byte derived output.
  - Constant-time password hash verification via `secrets.compare_digest()`.
- **Vault Encryption (`crypto_utils.py` / `vault.py`):**
  - Session encryption key derived in memory at login and passed to `cryptography.fernet.Fernet`.
  - Fernet uses **AES-128-CBC encryption with PKCS7 padding and HMAC-SHA256 authentication**.
  - Dashboard listing and details navigation never decrypt passwords; decryption occurs only for the single requested entry on explicit **Show** or **Copy**.
- **Persistent Database Location & Safe Migration (`db.py` / `main.py`):**
  - Default vault path resolves to `%LOCALAPPDATA%\ONESIUM\password_manager.db` via `db.get_default_db_path()`, keeping vault data independent of shortcut working directories, read-only install paths, or cloud-synced project folders.
  - At startup, `db.prepare_database()` checks for existing legacy `password_manager.db` files in the current working or application directory and safely copies an eligible legacy vault using SQLite's online backup API without deleting or altering the original file.
  - If both an active AppData database and an un-migrated populated legacy database already exist, neither file is automatically overwritten.
- **Database Safety (`db.py`):**
  - `PRAGMA foreign_keys = ON` enforced on every connection.
  - Parameterized SQL queries throughout (`?` placeholders).
  - Strict `user_id` scoping on read, update, and delete operations.

---

## Known Limitations

- **Offline / Single-Device Only:** No cloud synchronization or multi-device vault sharing.
- **Windows AppData Vault Location:** The primary database is stored locally per Windows user at `%LOCALAPPDATA%\ONESIUM\password_manager.db`. If a separate pre-existing legacy database sits in an older folder alongside an existing AppData database, ONESIUM preserves both untouched without automatic merging.
- **No Master Password Recovery:** Because the master password and derived encryption key are never stored, forgetting the master password makes encrypted entries unrecoverable.
- **Backup Key Binding:** `.pmv` backup files are encrypted with the active user's Fernet key and can only be restored by an account with the same master password and salt (same user/credentials).
- **Local Common-Password List:** `common_passwords.txt` provides a lightweight local dictionary (49 common entries) rather than a full breach database.
- **Windows Native Dialogs:** Delete confirmations (`messagebox`) and backup/restore file pickers (`filedialog`) use native OS dialogs.
- **Local SQLite Key Verification/Vault Coupling:** Both login verification hash and vault key derivation derive from `PBKDF2HMAC(master_password, salt)` using the same parameters (no separate key-wrapping layer, so master-password change is not implemented).

