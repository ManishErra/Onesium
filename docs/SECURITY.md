# Security notes

ONESIUM handles sensitive data, but this academic project has not received an independent security review. Use it for evaluation and learning; do not treat it as a professionally audited password manager.

## Current design

- The application is designed to keep its SQLite database on the local Windows account.
- Master passwords are not stored directly. A salted PBKDF2-derived value is used for verification and key derivation.
- Credential values and exported backups are encrypted with Fernet.
- The project includes inactivity locking and clipboard clearing controls.

These design notes describe intended behavior, not a guarantee that the complete application is free of vulnerabilities. Local malware, compromised user accounts, backups, clipboard access, and memory inspection remain relevant risks.

## Reporting a vulnerability

Please do not open a public issue containing exploit details or real credentials. Use GitHub's private vulnerability reporting for this repository when available, or contact the repository maintainer privately. Include affected versions, impact, and reproducible steps without sharing personal data.
