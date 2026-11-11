# ONESIUM — The Credential Vault
## Final Academic Project Report

---

## 1. Project Introduction and Objectives

**ONESIUM — The Credential Vault** is an offline, multi-user Windows desktop password manager implemented in Python using CustomTkinter, SQLite 3, and the Python `cryptography` library. The application evolved across four structured milestones from a plain-Tkinter prototype into a dark-themed desktop application packaged as a standalone Windows executable (`dist\Onesium.exe`).

### Core Objectives
- **Confidentiality & Integrity at Rest:** Encrypt all stored account passwords using authenticated symmetric encryption (`Fernet`: AES-128-CBC with HMAC-SHA256 authentication) so SQLite files contain zero plaintext credentials.
- **Zero-Plaintext Master Authentication:** Never store or decrypt the user's master password; verify login via `PBKDF2HMAC` (SHA-256, 600,000 iterations, 16-byte per-user salt) and constant-time digest comparison (`secrets.compare_digest`).
- **Strict Multi-User Isolation:** Support independent user accounts on a single workstation with per-user cryptographic salts, derived session keys, and database queries strictly scoped by `user_id`.
- **Minimal Plaintext Exposure (Lazy Decryption):** Render the credential dashboard, search results, edit forms, and credential details views using unencrypted metadata only; decrypt a single password strictly upon explicit user **Reveal** or **Copy** interaction.
- **Reliable Local Persistence & Safe Migration:** Store the SQLite database in `%LOCALAPPDATA%\ONESIUM\password_manager.db` while safely copying pre-existing legacy databases without deleting, resetting, or overwriting existing vaults.
- **Modern Offline Desktop Experience:** Deliver a responsive dark-mode CustomTkinter UI with dedicated in-window credential details, compact row actions, password strength checks, and encrypted `.pmv` portability.

---

## 2. Problem Statement

Modern digital workflows require users to maintain dozens of distinct accounts, frequently resulting in weak passwords or password reuse across services. While commercial cloud password managers mitigate reuse, they introduce ongoing subscription dependencies, third-party cloud exposure, and network attack surfaces unsuitable for strictly offline environments.

Conversely, lightweight academic/local password tools often suffer from critical weaknesses:
1. Storing passwords or encryption keys unsafely, or decrypting an entire vault into memory upon login.
2. Persisting databases to relative working directories (`./password_manager.db`), causing broken vaults when launched from shortcuts, read-only installation folders (`Program Files`), or cloud-synced directories.
3. Displaying sensitive passwords inside standard OS popups (`messagebox`) or leaving copied secrets on the clipboard indefinitely.

ONESIUM addresses all three challenges cleanly through layered cryptographic design, memory-safe UI practices, persistent per-user AppData storage, and automated test verification.

---

## 3. Technologies and Libraries Used

| Layer | Technology / Library | Purpose in ONESIUM |
|---|---|---|
| **Programming Language** | Python 3.13 (`3.13.4`) | Core runtime across backend, GUI, packaging, and test automation |
| **Desktop GUI** | `customtkinter` (`6.0.0`), `tkinter` | Dark-theme widgets (`CTk`, `CTkFrame`, `CTkEntry`, `CTkButton`, `CTkSlider`, `CTkLabel`), native dialogs (`messagebox`, `filedialog`) |
| **Cryptography** | `cryptography` (`cryptography.fernet.Fernet`, `PBKDF2HMAC`), `hashlib`, `secrets` | Key derivation, AES-128-CBC + HMAC-SHA256 authenticated encryption, CSPRNG password generation, constant-time comparison, SHA-256 clipboard verification |
| **Database Engine** | SQLite 3 (`sqlite3` standard library) | Local relational storage (`password_manager.db`), parameterized SQL, `PRAGMA foreign_keys = ON`, SQLite online backup migration |
| **Packaging** | PyInstaller (`6.22.3`) | Standalone `--onefile --windowed` Windows executable (`dist\Onesium.exe`) bundling assets and libraries |
| **Testing & VCS** | `unittest`, Git | 53-test automated regression suite (`test_regression.py`) and milestone-branched release workflow |

---

## 4. System Architecture

ONESIUM enforces a strict separation between presentation (`main.py`, `gui.py`), application logic (`auth.py`, `vault.py`, `password_utils.py`), cryptographic primitives (`crypto_utils.py`), and database persistence (`db.py`):

```text
+-----------------------------------------------------------------------+
|                       Presentation Layer                              |
|  main.py (_NullStream guard, DB bootstrap, CTk theme init)            |
|  gui.py  (PasswordManagerApp: Login, Register, Dashboard, Details,    |
|           Add/Edit Modal, Generator Modal, Auto-Lock, ClipboardTimer) |
+-----------------------------------+-----------------------------------+
                                    | calls public API (in-RAM session key)
+-----------------------------------v-----------------------------------+
|                   Application & Utility Layer                         |
|  auth.py           (register_user, login_user)                        |
|  vault.py          (CRUD, search, single-entry decrypt, .pmv backup)  |
|  password_utils.py (secrets generator, strength meter, common list)   |
+-------------------+-------------------------------+-------------------+
                    |                               |
+-------------------v---------------+   +-----------v-------------------+
|      Cryptographic Layer          |   |      Persistence Layer        |
|  crypto_utils.py                  |   |  db.py                        |
|  - generate_salt (16B CSPRNG)     |   |  - %LOCALAPPDATA%\ONESIUM\    |
|  - hash_password (PBKDF2 600k)    |   |    password_manager.db        |
|  - derive_key (urlsafe b64 32B)   |   |  - prepare_database migration |
|  - Fernet (AES-128-CBC + HMAC)    |   |  - SQLite parameterized SQL   |
+-----------------------------------+   +-------------------------------+
```

### Module Responsibilities
- **`main.py`:** Installs `_NullStream` only when `sys.stdout` or `sys.stderr` is `None` (preventing crashes from CustomTkinter warnings under `--windowed` PyInstaller execution without hiding real exceptions), invokes `db.prepare_database()` and `db.init_db()`, configures dark/blue CustomTkinter defaults, passes optional startup adoption notices, and launches `PasswordManagerApp`.
- **`db.py`:** Resolves `%LOCALAPPDATA%\ONESIUM\password_manager.db`, executes non-destructive SQLite backup adoption when migrating legacy `password_manager.db` files, preserves conflicting pre-existing vaults, enforces `PRAGMA foreign_keys = ON`, and executes all SQL via parameterized `?` placeholders.
- **`crypto_utils.py`:** Implements PBKDF2-HMAC-SHA256 (`SALT_SIZE = 16`, `PBKDF2_ITERATIONS = 600_000`, `KEY_LENGTH = 32`) and Fernet encryption/decryption helpers (`encrypt_password`, `decrypt_password`, `encrypt_data`, `decrypt_data`).
- **`auth.py`:** Registers accounts (`register_user`) and authenticates logins (`login_user`), returning `(user_id, encryption_key)` solely upon constant-time verification success.
- **`vault.py`:** Manages user-scoped credentials (`add_credential`, `get_credentials`, `get_credential_password`, `update_credential`, `delete_credential`, `search_credentials`) and encrypted `.pmv` export/import (`backup_user_vault`, `restore_user_vault`).
- **`password_utils.py`:** Provides CSPRNG password generation (`generate_password`, 8–128 characters backend / 8–64 UI slider), rule-based scoring (`check_password_strength`), and `common_passwords.txt` verification (`is_common_password` with `sys._MEIPASS` support when frozen).
- **`gui.py`:** Implements the dark-theme desktop screens, interactive row cards, dedicated details page, shared Add/Edit modal, standalone Password Generator dialog, 5-minute (`300,000 ms`) inactivity auto-lock timer, and 30-second (`30,000 ms`) SHA-256-guarded clipboard auto-clear.

---

## 5. Application Workflow

1. **Startup & Safe Database Preparation (`main.py` → `db.py`):**
   - `db.prepare_database()` inspects `%LOCALAPPDATA%\ONESIUM\password_manager.db` and checks legacy locations (`cwd\password_manager.db`, executable/script directory).
   - If the AppData database is absent and a valid ONESIUM database exists in a legacy folder, SQLite's online `backup()` API copies it to a temporary staging file, verifies table schema and row counts, and moves it atomically into `%LOCALAPPDATA%\ONESIUM\password_manager.db` while leaving the source database intact.
   - If both databases already exist independently, neither file is overwritten and the application proceeds with the AppData vault alongside an informational login notice.
2. **Account Registration & Authentication:**
   - Users register via **Create Account** with real-time strength feedback (`Very Weak` to `Very Strong`) and a warning banner when an input matches `common_passwords.txt`.
   - Login (**Unlock Vault**) recomputes the PBKDF2 verification hash against the stored per-user salt; on match, `derive_key()` places the Fernet session key in RAM only (`self.current_encryption_key`) and opens the Vault Dashboard.
3. **Vault Management & Lazy Details Inspection:**
   - The dashboard loads `vault.get_credentials()` metadata (site name, username, notes, timestamps) sorted alphabetically (`site_name COLLATE NOCASE ASC`) without calling `decrypt_password()`.
   - Clicking a credential card navigates in-window to **Credential Details**, displaying the password masked (`••••••••••••`) until the user explicitly toggles the reveal icon or copies it.
4. **Backup, Restore, Auto-Lock & Logout:**
   - **Backup Vault** exports encrypted ciphertext inside an outer Fernet-encrypted JSON v1 `.pmv` payload; **Restore Vault** rejects tampered files or backups encrypted by another user/key (`InvalidToken`).
   - Clicking **Lock & Logout** or remaining idle for 5 minutes runs `_clear_session_state()`, wiping the in-memory key, closing modals/details, clearing the clipboard, and returning to the Login view.

---

## 6. Features and Functionality

- **Authentication Views:** Dark-themed **Welcome back** login card and **Create Your Vault** registration card with per-field Show/Hide toggles, inline validation, password-field clearing on mismatch/duplicate error, and Enter-key submission.
- **Persistent Sidebar Dashboard:** Displays ONESIUM branding, offline status indicator (`Offline • Private • Local`), navigation items (**Your Vault**, **Password Generator**), vault tools (**Backup Vault**, **Restore Vault**), active local username, and **Lock & Logout**.
- **Search & Onboarding Empty States:** Real-time filtering (`Search by site or username...`) with clear (**✕**) button and `Esc` shortcut, plus distinct empty states for empty vaults versus zero search matches.
- **Credential Cards & Row Actions:** Clickable dark surface cards showing monogram badge, site name, username, last-updated date, compact icon-only **Edit** and **Delete** buttons with hover tooltips, and navigation chevron.
- **In-Window Credential Details View:** Displays website/application, username (with Copy icon), masked password (with Copy & Reveal/Hide icons), notes, Created date, Last Updated date, **Edit**, **Delete**, and **Back to Vault**.
- **Shared Add / Edit Modal:** Supports **Site / App**, **Username / Identifier**, **Password / New Password**, inline **Generate** button, real-time strength meter, common-password warning, and **Notes (Optional)**. Editing never decrypts or pre-fills the prior password.
- **Password Generator Tool:** Interactive length slider (`8–64`, default `16`) using `secrets`, guaranteed character-class diversity (uppercase, lowercase, digit, symbol from `!@#$%^&*()_+-=[]{}|;:,.<>?`), live strength readout, and auto-clearing clipboard copy.

---

## 7. Database Design

ONESIUM uses SQLite 3 (`%LOCALAPPDATA%\ONESIUM\password_manager.db`) with `PRAGMA foreign_keys = ON` enforced on every connection opened by `db.get_connection()`.

### Schema Definition

| Table | Column | Constraints & Type | Purpose |
|---|---|---|---|
| `users` | `user_id` | `INTEGER PRIMARY KEY AUTOINCREMENT` | Unique internal user identifier |
| `users` | `username` | `TEXT UNIQUE NOT NULL` | Unique stripped login name |
| `users` | `password_hash` | `TEXT NOT NULL` | Stores 32-byte PBKDF2-HMAC-SHA256 verification digest |
| `users` | `salt` | `BLOB NOT NULL` | 16-byte per-user CSPRNG salt |
| `users` | `created_at` | `TIMESTAMP DEFAULT CURRENT_TIMESTAMP` | Account creation timestamp |
| `vault_entries` | `entry_id` | `INTEGER PRIMARY KEY AUTOINCREMENT` | Unique credential row ID |
| `vault_entries` | `user_id` | `INTEGER NOT NULL`, `FK -> users(user_id) ON DELETE CASCADE` | Owner user scope & cascade cleanup |
| `vault_entries` | `site_name` | `TEXT NOT NULL` | Website or application label |
| `vault_entries` | `username_field` | `TEXT NOT NULL` | Login identifier / email |
| `vault_entries` | `encrypted_password` | `BLOB NOT NULL` | Fernet ciphertext token (`gAAAA...`) |
| `vault_entries` | `notes` | `TEXT` | Optional user notes |
| `vault_entries` | `created_at` | `TIMESTAMP DEFAULT CURRENT_TIMESTAMP` | Creation timestamp |
| `vault_entries` | `updated_at` | `TIMESTAMP DEFAULT CURRENT_TIMESTAMP` | Updated automatically on entry edits |

### Persistence Location & Migration Safety (`db.py`)
- Moving from relative `password_manager.db` to `%LOCALAPPDATA%\ONESIUM\password_manager.db` avoids shortcut CWD mismatches, `Program Files` read-only permissions errors, and OneDrive sync locks.
- Migration history is tracked locally in `%LOCALAPPDATA%\ONESIUM\.migration_state.json`. Once a legacy file is safely copied via `_copy_sqlite_db_safely()`, original legacy files remain untouched and later startups open the AppData vault cleanly without overwriting either file.

---

## 8. Encryption and Security Implementation

1. **Key Derivation (`crypto_utils.py`):**
   - Master passwords generate a unique 16-byte salt via `os.urandom(16)`.
   - `PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=600_000)` produces both verification bytes and the URL-safe base64-encoded 32-byte `Fernet` key.
   - Login verification uses `secrets.compare_digest(computed_hash, stored_hash)` to prevent timing side-channels.
2. **Authenticated Vault & Backup Encryption (`crypto_utils.py` / `vault.py`):**
   - Vault credentials and `.pmv` export files use `cryptography.fernet.Fernet`, which provides **AES-128-CBC encryption with PKCS7 padding and HMAC-SHA256 authentication**.
   - Any bit modification in ciphertext or decryption attempt with a different user's derived key raises `InvalidToken`.
3. **Volatile Session & Clipboard Controls (`gui.py`):**
   - `current_user_id` and `current_encryption_key` exist exclusively in memory on `PasswordManagerApp`.
   - Inactivity (`AUTO_LOCK_MS = 300_000`) resets on `<Key>` and `<Button>` events; expiry clears session keys, closes active dialogs, wipes details state, clears clipboard, and restores the login screen.
   - Copying a secret stores **only its SHA-256 digest** (`self._clipboard_expected_digest`) and schedules `_auto_clear_clipboard` at `30,000 ms` (`CLIPBOARD_CLEAR_MS`), comparing hashes with `secrets.compare_digest` so text copied later from another application is preserved.
4. **Weak-Password Awareness (`password_utils.py`):**
   - Local dictionary lookup against `common_passwords.txt` (`49` common passwords, resolved via `sys._MEIPASS` in frozen builds).

---

## 9. UI Design and Visual Verification

ONESIUM applies a consistent dark palette defined in `gui.py`:
- **Canvas Background:** `#0B0F17` (`COLOR_BG`)
- **Cards & Sidebar Surface:** `#121926` (`COLOR_SURFACE`), **Elevated:** `#192333`, **Inputs:** `#0F1724`, **Borders:** `#273449`
- **Primary Blue Accent:** `#3B82F6` (hover `#2563EB`), **Semantic Accents:** Success `#10B981`, Warning `#F59E0B`, Danger `#EF4444`
- **Typography & Icons:** `Segoe UI` hierarchy, `Consolas` monospace for passwords, and Windows vector glyphs (`Segoe Fluent Icons` / `Segoe MDL2 Assets` with Unicode fallback).

### Verified Rendered Screens (Captured Live via Win32 `PrintWindow`)
- **Packaged Executable Login & Migration Banner (`m4_exe_migrated.png`):** Verified `Onesium.exe` rendering dark card styling, `Offline • Private • Local` pill badge, masked password input, primary `Unlock Vault` CTA, and green startup status (`Existing vault safely adopted into Local AppData storage.`).
- **Vault Dashboard (`m3_dashboard_icons.png`):** Verified 2-column layout with persistent left sidebar (`Your Vault`, `Password Generator`, `Backup Vault`, `Restore Vault`, session user badge, `Lock & Logout`), real-time search bar, `+ Add Credential` button, `4 Saved` badge, and rounded credential cards with compact **Edit** / **Delete** action icons.
- **Credential Details View (`m3_details_masked.png`):** Verified in-window view showing **Back to Vault**, **Edit**, **Delete**, `Stored locally • Fernet encrypted` status, Username copy control, masked Password (`••••••••••••`) with Copy & Reveal icons, Notes block, and Created / Last Updated timestamps.
- **Password Generator Modal (`m3_dialog_generator.png`):** Verified monospace password preview, interactive length slider (`Length: 16`), strength readout (`Strength: Very Strong`), **Regenerate**, **Copy to Clipboard**, and **Close**.

---

## 10. Testing Methodology and Results

Testing combines automated backend unit tests, live CustomTkinter GUI integration tests, cryptographic security audits, and isolated packaged-binary execution tests.

### Automated Regression Suite (`test_regression.py`)

Executed via `C:\Users\Manish\AppData\Local\Programs\Python\Python313\python.exe test_regression.py` against an isolated temporary SQLite database and temporary `TemporaryDirectory` migration sandboxes:

| Test Suite | Tests | Verified Coverage | Result |
|---|---:|---|---|
| `TestBackendAuth` | 7 | Registration, duplicate rejection, empty input validation, login key tuple, wrong password/ghost user rejection | 7/7 Passed |
| `TestPasswordUtils` | 8 | Strength scoring (`Very Weak`–`Strong`), generated exact lengths (`8, 16, 32, 64`), bounds errors (`4`, `200`), randomness | 8/8 Passed |
| `TestGUI` | 11 | Startup, Login/Register UI rendering, duplicate/wrong auth handling, Show/Hide toggle, logout, auto-lock timer, backend API intact | 11/11 Passed |
| `TestDashboardGUI` | 13 | Dashboard render, entry counts, multi-user isolation, search/clear, empty states, Add/Edit/Delete refresh, **zero-decryption listing check**, `.pmv` backup/restore, auto-lock, focus safety | 13/13 Passed |
| `TestCredentialDetailsAndActionsGUI` | 6 | Details masked without decryption, Reveal/Hide/Copy/navigate clear, row icons isolated from card navigation, Edit/Delete isolation, logout/auto-lock cleanup, **30s SHA-256 clipboard clear preserves external clipboard** | 6/6 Passed |
| `TestSecurityAudit` | 3 | `PBKDF2_ITERATIONS == 600_000`, `PRAGMA foreign_keys == 1`, no plaintext secrets in SQLite (`gAAAA...` Fernet token), cross-user `.pmv` restore rejection, `common_passwords.txt` lookup | 3/3 Passed |
| `TestDatabaseLocationAndSafety` | 5 | `%LOCALAPPDATA%\ONESIUM` default path, cold DB creation & persistence across restart, non-destructive legacy DB adoption preserving SHA-256 hash of source, dual-existing DB non-overwrite protection, corrupt/0-byte file rejection | 5/5 Passed |
| **Total Automated Suite** | **53** | **Full End-to-End Coverage** | **53/53 Passed (0 Failed, 0 Skipped)** |

---

## 11. PyInstaller Packaging Process

The standalone Windows desktop binary was built cleanly with PyInstaller 6.22.3:

```powershell
C:\Users\Manish\AppData\Local\Programs\Python\Python313\python.exe -m PyInstaller `
  --clean --noconfirm --onefile --windowed --name Onesium `
  --workpath "C:\Users\Manish\.gemini\antigravity\brain\7fe7f813-7a0e-4b74-8bc1-1c5ec5bac847\scratch\pyi_build" `
  --distpath dist `
  --add-data "common_passwords.txt;." `
  --collect-data customtkinter `
  main.py
```

### Packaging Verification Summary
- **Output Artifact:** `dist\Onesium.exe` (`16,509,778` bytes, `--onefile`, `--windowed` / `console=False`).
- **Bundle Audit (`CArchiveReader`):** Confirmed `1,021` archive entries, including `common_passwords.txt` (`True`), `10` `customtkinter` theme/font/icon assets, and zero user databases or backups (`no user DB/backup bundled: True`).
- **Windowed Stream Compatibility Fix (`main.py`):** Initial windowed testing revealed that when CustomTkinter's font loader logs a fallback warning to `sys.stderr` (`CustomTkinter_shapes_font.otf` check), PyInstaller `--windowed` leaves `sys.stdout`/`sys.stderr` as `None`, causing `'NoneType' object has no attribute 'write'`. Adding `_NullStream` strictly when standard streams are `None` resolved the crash while keeping unhandled exception propagation intact.
- **Isolated Executable Verification:** Launched `dist\Onesium.exe` copied outside the repository in two isolated scratch environments (`LOCALAPPDATA` pointed to temp directories): verified cold database initialization at `<LOCALAPPDATA>\ONESIUM\password_manager.db`, verified legacy `password_manager.db` adoption preserving the source SHA-256 hash and allowing authenticated `vault.get_credential_password()` retrieval against the migrated DB, verified clean `WM_CLOSE` exit code `0`, and verified the repository's existing `password_manager.db` remained untouched (`hash` & `mtime` identical).

---

## 12. Installation and Execution Instructions

### Option A — Standalone Windows Executable (End Users)
1. Locate or distribute `dist\Onesium.exe`.
2. Double-click `Onesium.exe`. No Python installation or external dependencies are required.
3. User vault data is automatically initialized (or safely adopted from an existing local `password_manager.db`) inside `%LOCALAPPDATA%\ONESIUM\password_manager.db`.

### Option B — Running from Python Source
1. Clone the repository and enter the project folder:
   ```powershell
   git clone https://github.com/ManishErra/Onesium.git
   cd Onesium
   ```
2. Install runtime dependencies:
   ```powershell
   python -m pip install -r requirements.txt
   ```
3. Launch ONESIUM or run the full regression suite:
   ```powershell
   python main.py
   python test_regression.py
   ```

---

## 13. Known Limitations and Future Improvements

### Known Limitations
1. **Single-Device Offline Design:** No cloud synchronization or multi-device conflict resolution; vault portability relies on manual `.pmv` backup/restore.
2. **Irrecoverable Master Passwords & Shared Derivation:** Forgetting a master password renders stored entries permanently inaccessible. Because login verification and vault key derivation derive from the same `PBKDF2HMAC` secret, master-password rotation/re-encryption is not currently implemented.
3. **Searchable Metadata Unencrypted at Rest:** While passwords and `.pmv` backup contents are encrypted with Fernet, SQLite columns `site_name`, `username_field`, `notes`, and timestamps remain unencrypted to support instant local sorting and substring search.
4. **Dual-Existing Legacy/AppData Vaults:** When distinct populated `password_manager.db` files already exist independently in both a legacy directory and `%LOCALAPPDATA%\ONESIUM`, ONESIUM preserves both untouched rather than attempting an automatic merge.
5. **Non-Interactive Automation Scope for Frozen EXE:** In automated background verification runs without an active interactive Windows pointer/foreground desktop (`SetCursorPos` unavailable), live packaged-binary click-through from Login to Dashboard was covered via `test_regression.py`'s in-process CustomTkinter UI suite alongside isolated `Onesium.exe` startup, migration, and window-render checks.

### Future Improvements
1. **Master Password Rotation:** Add an in-vault key-wrapping header (random DEK wrapped by master-derived KEK) enabling master password changes without re-encrypting every row individually, plus optional merge tooling when both legacy and AppData vaults exist.
2. **Custom Application Icon & Metadata Masking:** Embed a dedicated `.ico` icon inside `Onesium.spec` and optionally encrypt `notes` fields under Fernet.
3. **Optional Hardware / TOTP Second Factor & CSV Import:** Support encrypted JSON/CSV import wizards from external managers while maintaining strict offline isolation.
