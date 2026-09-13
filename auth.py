import secrets
import crypto_utils
import db


def register_user(username, master_password, db_path=db.DB_NAME):
    """
    Registers a new user with a unique salt and PBKDF2 password hash.
    Returns the created user_id on success, or None if the username already exists.
    """
    if not isinstance(username, str) or not isinstance(master_password, str):
        raise TypeError("username and master_password must be strings")

    cleaned_username = username.strip()
    if not cleaned_username:
        raise ValueError("username cannot be empty or whitespace only")
    if not master_password:
        raise ValueError("master_password cannot be empty")

    salt = crypto_utils.generate_salt()
    password_hash = crypto_utils.hash_password(master_password, salt)

    user_id = db.create_user(cleaned_username, password_hash, salt, db_path=db_path)
    return user_id


def login_user(username, master_password, db_path=db.DB_NAME):
    """
    Authenticates a user against their stored PBKDF2 password hash.
    On successful authentication, derives and returns (user_id, encryption_key).
    Returns None if authentication fails.
    """
    if not isinstance(username, str) or not isinstance(master_password, str):
        raise TypeError("username and master_password must be strings")

    cleaned_username = username.strip()
    if not cleaned_username or not master_password:
        return None

    user = db.get_user_by_username(cleaned_username, db_path=db_path)
    if user is None:
        return None

    stored_salt = user["salt"]
    stored_hash = user["password_hash"]

    computed_hash = crypto_utils.hash_password(master_password, stored_salt)

    if not secrets.compare_digest(computed_hash, stored_hash):
        return None

    encryption_key = crypto_utils.derive_key(master_password, stored_salt)
    return user["user_id"], encryption_key
