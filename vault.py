import base64
import json
from cryptography.fernet import InvalidToken
import crypto_utils
import db


def add_credential(user_id, key, site_name, username, password, notes="", db_path=db.DB_NAME):
    """
    Encrypts password and adds a new vault credential entry for the user.
    Returns the created entry_id.
    """
    if not isinstance(site_name, str) or not site_name.strip():
        raise ValueError("site_name must be a non-empty string")
    if not isinstance(username, str) or not username.strip():
        raise ValueError("username must be a non-empty string")
    if not isinstance(password, str) or not password:
        raise ValueError("password must be a non-empty string")

    encrypted_password = crypto_utils.encrypt_password(password, key)
    return db.add_entry(
        user_id=user_id,
        site_name=site_name.strip(),
        username_field=username.strip(),
        encrypted_password=encrypted_password,
        notes=notes or "",
        db_path=db_path,
    )


def get_credentials(user_id, db_path=db.DB_NAME):
    """
    Retrieves all vault entries for a user without decrypting passwords.
    Returns a list of sqlite3.Row objects.
    """
    return db.get_entries_for_user(user_id, db_path=db_path)


def get_credential_password(user_id, entry_id, key, db_path=db.DB_NAME):
    """
    Retrieves and decrypts exactly one credential password for the specified user.
    Returns plaintext string on success, or None if entry is not found/accessible.
    """
    entries = db.get_entries_for_user(user_id, db_path=db_path)
    target = None
    for entry in entries:
        if entry["entry_id"] == entry_id:
            target = entry
            break

    if target is None:
        return None

    try:
        return crypto_utils.decrypt_password(target["encrypted_password"], key)
    except InvalidToken:
        return None


def update_credential(user_id, entry_id, key, site_name, username, password, notes="", db_path=db.DB_NAME):
    """
    Encrypts updated password and updates an existing credential scoped to user_id.
    Returns True if update succeeded, False otherwise.
    """
    if not isinstance(site_name, str) or not site_name.strip():
        raise ValueError("site_name must be a non-empty string")
    if not isinstance(username, str) or not username.strip():
        raise ValueError("username must be a non-empty string")
    if not isinstance(password, str) or not password:
        raise ValueError("password must be a non-empty string")

    encrypted_password = crypto_utils.encrypt_password(password, key)
    return db.update_entry(
        entry_id=entry_id,
        user_id=user_id,
        site_name=site_name.strip(),
        username_field=username.strip(),
        encrypted_password=encrypted_password,
        notes=notes or "",
        db_path=db_path,
    )


def delete_credential(user_id, entry_id, db_path=db.DB_NAME):
    """
    Deletes a credential scoped strictly to user_id and entry_id.
    Returns True if deletion succeeded, False otherwise.
    """
    return db.delete_entry(entry_id=entry_id, user_id=user_id, db_path=db_path)


def search_credentials(user_id, query, db_path=db.DB_NAME):
    """
    Searches credentials for a user by site name or username without decrypting passwords.
    Case-insensitive search. Returns matching entries list.
    """
    entries = db.get_entries_for_user(user_id, db_path=db_path)
    if not query or not query.strip():
        return entries

    q = query.strip().lower()
    return [
        entry
        for entry in entries
        if q in entry["site_name"].lower() or q in entry["username_field"].lower()
    ]


def backup_user_vault(user_id, key, file_path, db_path=db.DB_NAME):
    """
    Exports a user's vault entries as an encrypted JSON backup file.
    Does not write plaintext passwords. Returns True on success.
    """
    entries = db.get_entries_for_user(user_id, db_path=db_path)
    backup_data = {
        "version": 1,
        "entries": [
            {
                "site_name": entry["site_name"],
                "username_field": entry["username_field"],
                "encrypted_password": base64.b64encode(entry["encrypted_password"]).decode("ascii"),
                "notes": entry["notes"] or "",
            }
            for entry in entries
        ],
    }

    raw_json_bytes = json.dumps(backup_data).encode("utf-8")
    encrypted_payload = crypto_utils.encrypt_data(raw_json_bytes, key)

    with open(file_path, "wb") as f:
        f.write(encrypted_payload)

    return True


def restore_user_vault(user_id, key, file_path, db_path=db.DB_NAME):
    """
    Restores vault entries from an encrypted backup file into the authenticated user_id.
    Validates structure before inserting. Returns True on success, False on failure.
    """
    try:
        with open(file_path, "rb") as f:
            encrypted_payload = f.read()

        raw_json_bytes = crypto_utils.decrypt_data(encrypted_payload, key)
        backup_data = json.loads(raw_json_bytes.decode("utf-8"))

        if not isinstance(backup_data, dict) or backup_data.get("version") != 1 or "entries" not in backup_data:
            return False
        if not isinstance(backup_data["entries"], list):
            return False

        validated_entries = []
        for item in backup_data["entries"]:
            if not isinstance(item, dict):
                return False
            site_name = item.get("site_name")
            username_field = item.get("username_field")
            enc_pwd_b64 = item.get("encrypted_password")
            notes = item.get("notes", "")

            if not isinstance(site_name, str) or not isinstance(username_field, str) or not isinstance(enc_pwd_b64, str):
                return False
            if not isinstance(notes, str):
                return False

            enc_pwd_bytes = base64.b64decode(enc_pwd_b64.encode("ascii"), validate=True)
            validated_entries.append((site_name, username_field, enc_pwd_bytes, notes))

        for site_name, username_field, enc_pwd_bytes, notes in validated_entries:
            db.add_entry(
                user_id=user_id,
                site_name=site_name,
                username_field=username_field,
                encrypted_password=enc_pwd_bytes,
                notes=notes,
                db_path=db_path,
            )

        return True
    except (InvalidToken, json.JSONDecodeError, UnicodeDecodeError, ValueError, OSError, TypeError):
        return False
