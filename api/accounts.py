"""api/accounts.py — the account records the gate evaluates.

Backed by a JSON fixture so the dashboard opens on a populated, plausible workspace
instead of an empty form (see docs/demo-path.json). In a real deployment this would read
from whatever system of record holds consent — a CRM, a loan servicing platform, a
scheduling system — the gate does not care, it only needs these fields.
"""
from __future__ import annotations

import json
import os
import shutil
import threading
import time

_FIXTURES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fixtures")
DATA_PATH = os.path.join(_FIXTURES_DIR, "accounts.json")
SEED_PATH = os.path.join(_FIXTURES_DIR, "accounts.seed.json")

_lock = threading.Lock()


def reseed() -> None:
    """Copy the canonical, git-tracked seed dataset over the mutable runtime file. This is
    the only correct way to get back to a pristine demo state — resetting individual
    fields (like a naive "zero every call counter") silently destroys seed accounts that
    are deliberately non-zero, such as acc_attempt_limit."""
    shutil.copy2(SEED_PATH, DATA_PATH)


def _load() -> dict:
    if not os.path.isfile(DATA_PATH):
        reseed()
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


def _save(data: dict) -> None:
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)


def list_accounts() -> list[dict]:
    return list(_load().values())


def get_account(account_id: str) -> dict | None:
    return _load().get(account_id)


def mark_suppressed(account_id: str, reason: str) -> dict | None:
    with _lock:
        data = _load()
        account = data.get(account_id)
        if account is None:
            return None
        account["suppressed"] = True
        account["suppressedAt"] = time.time()
        account["suppressedReason"] = reason
        _save(data)
        return account


def record_call_attempt(account_id: str) -> dict | None:
    with _lock:
        data = _load()
        account = data.get(account_id)
        if account is None:
            return None
        today = time.strftime("%Y-%m-%d", time.gmtime())
        if account.get("callCountDate") != today:
            account["callCountDate"] = today
            account["callCountToday"] = 0
        account["callCountToday"] = account.get("callCountToday", 0) + 1
        account["lastCallAt"] = time.time()
        _save(data)
        return account


