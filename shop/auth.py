"""Demo-only authentication. Do not use real credentials here."""

_USERS = {"alice@example.com": "demo-password"}


def authenticate(email, password):
    """Return True if the credentials match a known demo user."""
    return _USERS.get(email) == password
