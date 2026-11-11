# ONESIUM — The Credential Vault
### Academic Project Presentation Outline

---

## Slide 1: Title & Project Overview
- **Project Title:** ONESIUM — The Credential Vault
- **Category:** Offline Desktop Cybersecurity & Credential Management Application
- **Target Platform:** Microsoft Windows (Standalone Desktop Executable & Python Source)
- **Core Objective:** Provide an offline-first, zero-cloud, multi-user password manager that safeguards user credentials using authenticated symmetric encryption and high-work-factor key derivation behind a modern dark desktop interface.
- **Controlled Evolution:** Built upon a verified cryptographic backend (`db.py`, `auth.py`, `vault.py`, `crypto_utils.py`, `password_utils.py`) and migrated cleanly across four engineering milestones into a dark-themed CustomTkinter desktop application (`gui.py`).

---

## Slide 2: Problem Statement & Objectives
- **Problems Addressed:**
  - Password reuse and weak credentials across online and local accounts.
  - Privacy and breach exposure risks inherent in third-party cloud password synchronization.
  - Poor usability of legacy desktop interfaces (plain Tkinter, modal popups displaying plaintext passwords).
- **Key Objectives:**
  - Store all secrets encrypted at rest in local SQLite storage (`password_manager.db`) — zero plaintext storage.
  - Strictly isolate multiple local users via per-user salts, derived keys, and user-scoped queries.
  - Never decrypt vault passwords unnecessarily during dashboard rendering or details navigation.
  - Deliver a clean, responsive dark UI without altering the underlying cryptographic backend.

---

## Slide 3: System Architecture (Layered Design)
1. **Presentation Layer (`main.py`, `gui.py`):**
   - CustomTkinter dark-mode UI (`#0B0F17` canvas, `#121926` cards, `#3B82F6` blue accent).
   - Screens: Login, Create Account, Vault Dashboard, Dedicated Credential Details View, Add/Edit Modal, Password Generator Modal.
   - Manages volatile in-memory session state, 5-minute inactivity auto-lock, and 30-second SHA-256-guarded clipboard auto-clear.
2. **Application & Vault Logic (`auth.py`, `vault.py`, `password_utils.py`):**
   - User registration/authentication, user-scoped credential CRUD, case-insensitive search, `.pmv` encrypted backup/restore, `secrets`-based password generation, strength scoring, and common-password checks (`common_passwords.txt`).
3. **Cryptographic Engine (`crypto_utils.py`):**
   - PBKDF2-HMAC-SHA256 (`600,000` iterations, `16`-byte random salt, `32`-byte derived key).
   - Fernet authenticated encryption (**AES-128-CBC encryption with HMAC-SHA256 authentication**).
4. **Persistence Layer (`db.py`):**
   - SQLite database stored at `%LOCALAPPDATA%\ONESIUM\password_manager.db` with non-destructive legacy vault adoption (`prepare_database`), `PRAGMA foreign_keys = ON`, parameterized SQL queries, and normalized `users` and `vault_entries` tables.

---

## Slide 4: Core Features
- **Multi-User Vault Isolation:** Separate accounts on one device, each locked by its own master password, salt, and derived Fernet key.
- **Lazy-Decryption Vault Dashboard:** Displays site names, usernames, and real-time search (`Search by site or username...`) without decrypting stored passwords.
- **Dedicated Credential Details View:** Click any card to inspect Site, Username, Masked Password, Notes, Created/Updated timestamps, with explicit Reveal/Hide, Copy, Edit, and Delete controls and **Back to Vault** navigation.
- **Compact Card Action Icons:** Quick Edit and Delete icon controls with hover tooltips directly on credential rows.
- **Cryptographic Password Generator & Strength Auditor:** Configurable 8–64 character UI generator backed by Python's `secrets` module (8–128 in `password_utils.py`), real-time strength indicator (0–5 score), and warning against weak/common passwords (`common_passwords.txt`).
- **Encrypted Vault Portability:** Export and restore user-owned `.pmv` backup files encrypted with the user's derived Fernet key.

---

## Slide 5: Technology Stack
- **Language:** Python 3.13
- **GUI Framework:** CustomTkinter (`customtkinter`) — dark theme with blue accent
- **Cryptography:** `cryptography` (`cryptography.fernet.Fernet`), Python `hashlib` (PBKDF2-HMAC-SHA256, SHA-256), `secrets` (CSPRNG & constant-time comparison)
- **Database:** SQLite 3 (Python standard library `sqlite3`)
- **Packaging:** PyInstaller (standalone windowed Windows binary `dist\Onesium.exe` bundling `common_passwords.txt` and CustomTkinter assets)
- **Testing & Version Control:** Python `unittest` regression suite (`test_regression.py`), Git milestone workflow (`main` + four milestone branches)

---

## Slide 6: Security Mechanisms
- **Master Password Protection:** Never stored in plaintext; hashed with PBKDF2-HMAC-SHA256 (`600,000` iterations, per-user 16-byte CSPRNG salt via `os.urandom(16)`), verified with `secrets.compare_digest`.
- **Authenticated Encryption:** Vault secrets and `.pmv` backups use Fernet (**AES-128-CBC encryption with HMAC-SHA256 authentication**), blocking silent tampering and cross-user backup restoration.
- **Minimal Plaintext Exposure:** Dashboard listing queries omit decryption (`get_credentials`); `get_credential_password` runs only on explicit Reveal or Copy; no plaintext secrets printed, logged, or stored in card data structures.
- **Session & Endpoint Hygiene:** Session encryption key cleared immediately on logout or 5-minute (`300,000 ms`) inactivity auto-lock; copied secrets trigger a 30-second (`30,000 ms`) timer that hashes the copied value with SHA-256 in memory and clears the Windows clipboard only if the digest matches.

---

## Slide 7: Live Demonstration Flow
1. Launch `Onesium.exe` -> Register a new account (**Create Account**) demonstrating weak/common password warning on `password` and strong password check.
2. Sign in (**Unlock Vault**) -> Observe empty vault onboarding state (`Your vault is empty`) -> Add two credentials using the Password Generator (**Generate**).
3. Filter credentials dynamically via the top search bar (**Search by site or username...**).
4. Click a credential card -> Inspect Details View (password masked by default) -> Toggle Reveal/Hide icon, copy password, and edit notes.
5. Export encrypted `.pmv` backup (**Backup Vault**) -> Delete an entry -> Restore from `.pmv` backup (**Restore Vault**) -> Confirm recovery.
6. Demonstrate **Lock & Logout** / 5-minute Auto-Lock and multi-user isolation (a second user cannot view or restore User A's entries/backups).

---

## Slide 8: Testing Results & Release Engineering
- **Automated Regression Suite (`test_regression.py`):** 53 unit, GUI, database-migration, integration, and security audit tests covering:
  - Auth & PBKDF2 isolation (`TestBackendAuth`)
  - Generator & strength validation (`TestPasswordUtils`)
  - Login, Registration & Session Lifecycle (`TestGUI`)
  - Dashboard, Search, CRUD, Backup/Restore (`TestDashboardGUI`)
  - Details View, Lazy Decryption & Safe Clipboard Auto-Clear (`TestCredentialDetailsAndActionsGUI`)
  - End-to-End Cryptographic & Cross-User Security (`TestSecurityAudit`)
  - Persistent `%LOCALAPPDATA%\ONESIUM` Location & Safe Legacy Migration (`TestDatabaseLocationAndSafety`)
- **Milestone Progression:** Delivered sequentially across `milestone1-ctk-auth-ui` -> `milestone2-modern-dashboard` -> `milestone3-credential-details` -> `milestone4-final-release`, then cleanly merged into `main`.
- **Deployment Ready:** Packaged as standalone Windows GUI executable `dist\Onesium.exe` with zero external setup required for end users.

---

## Slide 9: Limitations & Conclusion
- **Current Scope & Limitations:**
  - Single-device offline vault stored per Windows user at `%LOCALAPPDATA%\ONESIUM\password_manager.db` (no automatic cloud sync or automatic merging if separate old/new DBs both exist).
  - Password verification and key derivation share the same master password without a secondary TOTP/hardware factor or master-password rotation wizard.
  - SQLite metadata (`site_name`, `username_field`, `notes`, timestamps) remains searchable/unencrypted at rest while `encrypted_password` and `.pmv` payloads are Fernet-encrypted.
- **Conclusion:**
  - ONESIUM successfully integrates defense-in-depth local cryptography (`PBKDF2-HMAC-SHA256` + `Fernet`) with an intuitive dark desktop interface, passing full functional, UI, and security regression testing as a release-ready standalone Windows application.

