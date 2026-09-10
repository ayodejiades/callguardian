"""tests/conftest.py — tests exercise the same on-disk fixtures the live demo seeds from
(fixtures/accounts.json, fixtures/users.json, fixtures/audit/log.jsonl). Snapshot and
restore them around the whole test session so running the suite repeatedly never
accumulates call counts, signups, or audit entries into the checked-in fixture files.
"""
from __future__ import annotations

import os
import shutil

import pytest

os.environ.setdefault("DEMO_MODE", "1")

from api import accounts as accounts_mod  # noqa: E402
from api import audit as audit_mod  # noqa: E402
from api import auth as auth_mod  # noqa: E402

_PATHS = [accounts_mod.DATA_PATH, auth_mod.USERS_PATH, audit_mod.LOG_PATH]


@pytest.fixture(autouse=True, scope="session")
def _restore_fixtures_after_suite():
    backups = {}
    for path in _PATHS:
        if os.path.isfile(path):
            backups[path] = path + ".bak_test"
            shutil.copy2(path, backups[path])
    yield
    for path, backup in backups.items():
        shutil.move(backup, path)
    if os.path.isfile(auth_mod.USERS_PATH) and auth_mod.USERS_PATH not in backups:
        os.remove(auth_mod.USERS_PATH)
    if os.path.isfile(audit_mod.LOG_PATH) and audit_mod.LOG_PATH not in backups:
        os.remove(audit_mod.LOG_PATH)
