import json
import os
import sqlite3
import sys

APP_DATA_DIR_NAME = "ONESIUM"
DB_FILENAME = "password_manager.db"
_MIGRATION_STATE_FILENAME = ".migration_state.json"


def get_default_db_path():
    """Returns the persistent user-data database path (%LOCALAPPDATA%\\ONESIUM\\password_manager.db)."""
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        base_dir = os.path.join(local_app_data, APP_DATA_DIR_NAME)
    else:
        base_dir = os.path.join(os.path.expanduser("~"), "AppData", "Local", APP_DATA_DIR_NAME)
    return os.path.join(base_dir, DB_FILENAME)


DB_NAME = get_default_db_path()


def _ensure_parent_dir(db_path):
    """Creates parent directories for file-backed SQLite databases when needed."""
    if not db_path or db_path == ":memory:" or str(db_path).startswith("file:"):
        return
    parent = os.path.dirname(os.path.abspath(db_path))
    if parent:
        os.makedirs(parent, exist_ok=True)


def _is_valid_onesium_sqlite_db(db_path):
    """Returns True if db_path is a readable SQLite file containing the ONESIUM schema."""
    if not db_path or not os.path.isfile(db_path) or os.path.getsize(db_path) == 0:
        return False
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('users', 'vault_entries')"
        ).fetchall()
        return {r[0] for r in rows} == {"users", "vault_entries"}
    except sqlite3.Error:
        return False
    finally:
        if conn is not None:
            conn.close()


def _db_row_counts(db_path):
    """Returns (users_count, entries_count) for an existing ONESIUM SQLite database."""
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        users_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        entries_count = conn.execute("SELECT COUNT(*) FROM vault_entries").fetchone()[0]
        return int(users_count), int(entries_count)
    except sqlite3.Error:
        return 0, 0
    finally:
        if conn is not None:
            conn.close()


def _load_migration_state(state_path):
    """Loads previously recorded legacy migration metadata if present."""
    if not os.path.isfile(state_path):
        return {"migrated_sources": []}
    try:
        with open(state_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and isinstance(data.get("migrated_sources"), list):
            return data
    except (OSError, ValueError, TypeError):
        pass
    return {"migrated_sources": []}


def _save_migration_state(state_path, recorded_sources):
    """Persists normalized legacy source paths that have already been copied."""
    try:
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump({"migrated_sources": sorted(set(recorded_sources))}, f, indent=2)
    except OSError:
        pass


def get_legacy_db_candidates(target_path=None):
    """
    Returns unique existing legacy database paths from the working directory
    and executable/script directory, excluding target_path.
    """
    target_norm = os.path.normcase(os.path.abspath(target_path or DB_NAME))
    candidates = []
    seen = {target_norm}

    raw_locations = [os.path.abspath(DB_FILENAME)]
    if getattr(sys, "frozen", False):
        app_dir = os.path.dirname(os.path.abspath(sys.executable))
    else:
        app_dir = os.path.dirname(os.path.abspath(__file__))
    raw_locations.append(os.path.join(app_dir, DB_FILENAME))

    for path in raw_locations:
        abs_path = os.path.abspath(path)
        norm = os.path.normcase(abs_path)
        if norm in seen:
            continue
        seen.add(norm)
        if os.path.isfile(abs_path):
            candidates.append(abs_path)
    return candidates


def _copy_sqlite_db_safely(src_path, dst_path):
    """
    Safely copies src_path to dst_path using SQLite's backup API via a staging file.
    Never overwrites dst_path if it already exists and never deletes src_path.
    """
    if os.path.exists(dst_path):
        raise FileExistsError(f"Refusing to overwrite existing database at {dst_path}")

    _ensure_parent_dir(dst_path)
    stage_path = f"{dst_path}.migrating.{os.getpid()}"
    if os.path.exists(stage_path):
        os.remove(stage_path)

    src_conn = None
    stage_conn = None
    try:
        src_conn = sqlite3.connect(src_path)
        stage_conn = sqlite3.connect(stage_path)
        src_conn.backup(stage_conn)
    finally:
        if stage_conn is not None:
            stage_conn.close()
        if src_conn is not None:
            src_conn.close()

    if not _is_valid_onesium_sqlite_db(stage_path) or _db_row_counts(stage_path) != _db_row_counts(src_path):
        try:
            os.remove(stage_path)
        except OSError:
            pass
        raise RuntimeError(f"Migrated database verification failed for {src_path}")

    if os.path.exists(dst_path):
        try:
            os.remove(stage_path)
        except OSError:
            pass
        raise FileExistsError(f"Refusing to overwrite existing database at {dst_path}")

    os.rename(stage_path, dst_path)


def prepare_database(target_path=None, legacy_paths=None):
    """
    Prepares the persistent database path without overwriting, deleting, or resetting
    any existing database. Safely copies an existing legacy database when target_path
    does not yet exist; if both target_path and a legacy database exist, preserves both.
    """
    target = os.path.abspath(target_path or DB_NAME)
    _ensure_parent_dir(target)
    state_path = os.path.join(os.path.dirname(target), _MIGRATION_STATE_FILENAME)

    if legacy_paths is None:
        raw_candidates = get_legacy_db_candidates(target)
    else:
        target_norm = os.path.normcase(target)
        raw_candidates = []
        seen = {target_norm}
        for p in legacy_paths:
            abs_p = os.path.abspath(p)
            norm = os.path.normcase(abs_p)
            if norm not in seen and os.path.isfile(abs_p):
                seen.add(norm)
                raw_candidates.append(abs_p)

    valid_candidates = [p for p in raw_candidates if _is_valid_onesium_sqlite_db(p)]
    state = _load_migration_state(state_path)
    recorded_sources = {os.path.normcase(os.path.abspath(p)) for p in state.get("migrated_sources", [])}

    if not os.path.exists(target):
        if not valid_candidates:
            return {
                "active_db": target,
                "action": "initialize_new",
                "migrated_from": None,
                "legacy_dbs": [],
                "conflict_dbs": [],
            }

        # Prefer a populated vault over an empty schema when multiple legacy DBs exist
        chosen = max(valid_candidates, key=lambda p: sum(_db_row_counts(p)))
        _copy_sqlite_db_safely(chosen, target)
        recorded_sources.add(os.path.normcase(chosen))
        _save_migration_state(state_path, recorded_sources)
        remaining = [p for p in valid_candidates if os.path.normcase(p) != os.path.normcase(chosen)]
        return {
            "active_db": target,
            "action": "migrated",
            "migrated_from": chosen,
            "legacy_dbs": remaining,
            "conflict_dbs": [p for p in remaining if sum(_db_row_counts(p)) > 0],
        }

    # Target DB already exists: never overwrite either target or any legacy file
    unrecorded_conflicts = [
        p
        for p in valid_candidates
        if os.path.normcase(p) not in recorded_sources and sum(_db_row_counts(p)) > 0
    ]
    action = "both_exist_preserved" if unrecorded_conflicts else "existing_active"
    return {
        "active_db": target,
        "action": action,
        "migrated_from": None,
        "legacy_dbs": valid_candidates,
        "conflict_dbs": unrecorded_conflicts,
    }


def get_connection(db_path=DB_NAME):
    """Returns a SQLite connection with foreign keys enabled."""
    _ensure_parent_dir(db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path=DB_NAME):
    """Initializes the database schema if tables do not already exist."""
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt BLOB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS vault_entries (
                    entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    site_name TEXT NOT NULL,
                    username_field TEXT NOT NULL,
                    encrypted_password BLOB NOT NULL,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
                """
            )
    finally:
        conn.close()


def create_user(username, password_hash, salt, db_path=DB_NAME):
    """
    Creates a new user record.
    Returns the new user_id on success, or None if the username already exists.
    """
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (username, password_hash, salt)
                VALUES (?, ?, ?)
                """,
                (username, password_hash, salt),
            )
            return cursor.lastrowid
    except sqlite3.IntegrityError as e:
        if "UNIQUE" in str(e) and "username" in str(e):
            return None
        raise
    finally:
        conn.close()


def get_user_by_username(username, db_path=DB_NAME):
    """
    Retrieves a user by username.
    Returns sqlite3.Row object or None if not found.
    """
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT user_id, username, password_hash, salt, created_at
            FROM users
            WHERE username = ?
            """,
            (username,),
        )
        return cursor.fetchone()
    finally:
        conn.close()


def add_entry(user_id, site_name, username_field, encrypted_password, notes="", db_path=DB_NAME):
    """
    Adds a new vault entry for a user.
    Returns the created entry_id.
    """
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO vault_entries (user_id, site_name, username_field, encrypted_password, notes)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, site_name, username_field, encrypted_password, notes),
            )
            return cursor.lastrowid
    finally:
        conn.close()


def get_entries_for_user(user_id, db_path=DB_NAME):
    """
    Retrieves all vault entries for a given user.
    Returns a list of sqlite3.Row objects containing encrypted password data.
    """
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT entry_id, user_id, site_name, username_field, encrypted_password, notes, created_at, updated_at
            FROM vault_entries
            WHERE user_id = ?
            ORDER BY site_name COLLATE NOCASE ASC
            """,
            (user_id,),
        )
        return cursor.fetchall()
    finally:
        conn.close()


def update_entry(entry_id, user_id, site_name, username_field, encrypted_password, notes="", db_path=DB_NAME):
    """
    Updates an existing vault entry scoped strictly to entry_id AND user_id.
    Returns True if an entry was updated, False otherwise.
    """
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE vault_entries
                SET site_name = ?,
                    username_field = ?,
                    encrypted_password = ?,
                    notes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE entry_id = ? AND user_id = ?
                """,
                (site_name, username_field, encrypted_password, notes, entry_id, user_id),
            )
            return cursor.rowcount > 0
    finally:
        conn.close()


def delete_entry(entry_id, user_id, db_path=DB_NAME):
    """
    Deletes a vault entry scoped strictly to entry_id AND user_id.
    Returns True if an entry was deleted, False otherwise.
    """
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                DELETE FROM vault_entries
                WHERE entry_id = ? AND user_id = ?
                """,
                (entry_id, user_id),
            )
            return cursor.rowcount > 0
    finally:
        conn.close()
