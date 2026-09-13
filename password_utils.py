import os
import secrets
import string
import sys

SPECIAL_CHARACTERS = "!@#$%^&*()_+-=[]{}|;:,.<>?"
ALL_CHARACTERS = string.ascii_uppercase + string.ascii_lowercase + string.digits + SPECIAL_CHARACTERS


def generate_password(length=16):
    """
    Generates a cryptographically secure random password using secrets.
    Ensures at least one uppercase, lowercase, digit, and special character.
    Length must be an integer between 8 and 128.
    """
    if not isinstance(length, int) or isinstance(length, bool):
        raise TypeError("length must be an integer")
    if length < 8 or length > 128:
        raise ValueError("length must be between 8 and 128 characters")

    # Ensure representation from each character category
    password_chars = [
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.digits),
        secrets.choice(SPECIAL_CHARACTERS),
    ]

    # Fill the remaining length from the full character pool
    password_chars += [secrets.choice(ALL_CHARACTERS) for _ in range(length - 4)]

    # Shuffle using SystemRandom to preserve cryptographically secure randomness
    secrets.SystemRandom().shuffle(password_chars)

    return "".join(password_chars)


def check_password_strength(password):
    """
    Evaluates password strength using deterministic rule-based criteria.
    Returns a dictionary with score (0-5) and label.
    """
    if not isinstance(password, str) or not password:
        return {"score": 0, "label": "Very Weak"}

    points = 0
    if len(password) >= 8:
        points += 1
    if len(password) >= 12:
        points += 1
    if any(c.islower() for c in password):
        points += 1
    if any(c.isupper() for c in password):
        points += 1
    if any(c.isdigit() for c in password):
        points += 1
    if any(c in SPECIAL_CHARACTERS for c in password):
        points += 1

    score = min(points, 5)

    labels = {
        0: "Very Weak",
        1: "Very Weak",
        2: "Weak",
        3: "Moderate",
        4: "Strong",
        5: "Very Strong",
    }

    return {"score": score, "label": labels[score]}


def is_common_password(password, file_path="common_passwords.txt"):
    """
    Checks if a password exists in the local common_passwords.txt list.
    Case-sensitive exact match. Returns False if file is missing or on error.
    """
    if not isinstance(password, str) or not password:
        return False

    if file_path == "common_passwords.txt" and hasattr(sys, "_MEIPASS"):
        meipass_path = os.path.join(sys._MEIPASS, "common_passwords.txt")
        if os.path.exists(meipass_path):
            file_path = meipass_path

    if not os.path.exists(file_path):
        return False

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                cleaned = line.strip()
                if cleaned and cleaned == password:
                    return True
        return False
    except OSError:
        return False
