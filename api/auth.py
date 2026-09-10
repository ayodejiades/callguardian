"""api/auth.py — the minimum real auth a hackathon demo needs: hashed passwords, a
signed session cookie, no third-party auth dependency. This is demo-appropriate, not
production-appropriate (no rate limiting, no password reset, no email verification) —
everything not on the demo path is deliberately left out, per AGENTS.md's working rules.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time

from api.settings import settings

USERS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fixtures", "users.json")
SESSION_COOKIE = "cg_session"
SESSION_TTL_SECONDS = 60 * 60 * 12


def _load_users() -> dict:
    if not os.path.isfile(USERS_PATH):
        return {}
    with open(USERS_PATH, encoding="utf-8") as f:
        return json.load(f)


def _save_users(users: dict) -> None:
    with open(USERS_PATH, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, sort_keys=True)


def _hash_password(password: str, salt: bytes) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000).hex()


def create_user(email: str, password: str, org: str) -> tuple[bool, str]:
    email = email.strip().lower()
    if not email or "@" not in email:
        return False, "enter a valid email address"
    if len(password) < 8:
        return False, "password must be at least 8 characters"
    users = _load_users()
    if email in users:
        return False, "an account with that email already exists"
    salt = os.urandom(16)
    users[email] = {
        "org": org, "salt": salt.hex(), "passwordHash": _hash_password(password, salt),
        "createdAt": time.time(),
    }
    _save_users(users)
    return True, ""


def verify_user(email: str, password: str) -> bool:
    users = _load_users()
    record = users.get(email.strip().lower())
    if record is None:
        return False
    salt = bytes.fromhex(record["salt"])
    return hmac.compare_digest(_hash_password(password, salt), record["passwordHash"])


def _sign(payload: str) -> str:
    return hmac.new(settings.session_secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()


def create_session_cookie(email: str) -> str:
    payload = json.dumps({"email": email, "exp": time.time() + SESSION_TTL_SECONDS})
    encoded = base64.urlsafe_b64encode(payload.encode("utf-8")).decode("ascii")
    return f"{encoded}.{_sign(encoded)}"


def read_session_cookie(cookie_value: str | None) -> str | None:
    if not cookie_value or "." not in cookie_value:
        return None
    encoded, _, signature = cookie_value.partition(".")
    if not hmac.compare_digest(_sign(encoded), signature):
        return None
    try:
        payload = json.loads(base64.urlsafe_b64decode(encoded.encode("ascii")))
    except Exception:  # noqa: BLE001 — any malformed cookie is just "not logged in"
        return None
    if payload.get("exp", 0) < time.time():
        return None
    return payload.get("email")
