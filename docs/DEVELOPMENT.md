# Development

## Set up

Use Python 3.10 or newer on Windows. From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Run the desktop app with `python main.py`.

## Regression suite

```powershell
python test_regression.py
```

The suite uses Python's standard `unittest` framework. Tests may use temporary SQLite databases; do not point tests at a personal vault.

## Data and generated files

Runtime data is stored under `%LOCALAPPDATA%\ONESIUM`. Never commit database files, encrypted backup exports, build output, or local environment files. The repository's `.gitignore` excludes common runtime and build artifacts.

## Change guidelines

Keep credentials encrypted at rest, avoid logging secrets, preserve per-user scoping for database operations, and update documentation when user-facing behavior or setup steps change.
