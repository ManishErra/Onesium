# ONESIUM

ONESIUM is an offline Windows desktop credential vault built with Python, CustomTkinter, SQLite, and the `cryptography` package. It supports separate local accounts, encrypted credential storage, password generation, and encrypted vault backups.

> **Project status:** Academic project. It has not undergone an independent security audit. Do not rely on it as the sole storage for production or high-value credentials.

## Features

- Per-user vaults stored locally in the Windows `%LOCALAPPDATA%\ONESIUM` directory.
- Master-password based key derivation and Fernet encryption for saved credentials.
- Search, add, edit, delete, reveal, and copy credential entries.
- Secure password generation and common-password checks.
- Encrypted `.pmv` backup and restore.
- Automatic inactivity lock and timed clipboard clearing.

## Requirements

- Windows
- Python 3.10 or newer
- Dependencies from `requirements.txt`

## Install and run

```powershell
git clone https://github.com/ManishErra/Onesium.git
cd Onesium
python -m pip install -r requirements.txt
python main.py
```

The application creates its database in `%LOCALAPPDATA%\ONESIUM\password_manager.db`. Keep encrypted backups in a safe location. Losing the master password makes the vault unrecoverable.

## Tests

Run the regression suite from the repository root:

```powershell
python test_regression.py
```

## Project layout

| Path | Purpose |
| --- | --- |
| `main.py`, `gui.py` | Application entry point and desktop interface |
| `auth.py`, `vault.py` | Account and credential operations |
| `crypto_utils.py`, `password_utils.py` | Encryption, key derivation, password generation, and strength checks |
| `db.py` | SQLite storage and database setup |
| `common_passwords.txt` | Password denylist used by the strength checks |
| `test_regression.py` | Regression tests |
| `docs/` | Development and security notes, project report, presentation, and viva guide |

## Documentation

- [Development guide](docs/DEVELOPMENT.md)
- [Security notes](docs/SECURITY.md)
- [Project report](docs/PROJECT_REPORT.md)
- [Presentation outline](docs/PRESENTATION.md)
- [Viva preparation guide](docs/VIVA_PREPARATION.md)

## License

No license is currently provided. All rights are reserved unless the repository owner adds a license.
