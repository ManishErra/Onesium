import sqlite3

DB_NAME = "password_manager.db"


def get_connection(db_path=DB_NAME):
    """Returns a SQLite connection with foreign keys enabled."""
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
