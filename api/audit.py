"""api/audit.py — append-only, hash-chained audit log.

Every compliance decision and call outcome is written here. Each entry's hash covers its
own content plus the previous entry's hash, so editing or reordering any line breaks the
chain from that point forward — the same construction as a blockchain's block hashes,
applied to a JSONL file because a hackathon demo does not need a distributed ledger, it
needs a tamper-evidence property a judge can verify in fifteen seconds.

`verify()` is the whole point: it recomputes every hash and reports the first line where
the recomputed hash no longer matches the stored one.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass, field

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fixtures", "audit")
LOG_PATH = os.path.join(LOG_DIR, "log.jsonl")

GENESIS_HASH = "0" * 64


@dataclass
class AuditEntry:
    seq: int
    at: float
    type: str
    payload: dict
    prev_hash: str
    hash: str = ""


def _canonical(seq: int, at: float, type_: str, payload: dict, prev_hash: str) -> str:
    return json.dumps(
        {"seq": seq, "at": at, "type": type_, "payload": payload, "prevHash": prev_hash},
        sort_keys=True, separators=(",", ":"),
    )


def _compute_hash(seq: int, at: float, type_: str, payload: dict, prev_hash: str) -> str:
    return hashlib.sha256(_canonical(seq, at, type_, payload, prev_hash).encode("utf-8")).hexdigest()


def _read_all() -> list[dict]:
    if not os.path.isfile(LOG_PATH):
        return []
    entries = []
    with open(LOG_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def append(entry_type: str, payload: dict) -> AuditEntry:
    os.makedirs(LOG_DIR, exist_ok=True)
    entries = _read_all()
    seq = len(entries)
    prev_hash = entries[-1]["hash"] if entries else GENESIS_HASH
    at = time.time()
    h = _compute_hash(seq, at, entry_type, payload, prev_hash)
    entry = AuditEntry(seq=seq, at=at, type=entry_type, payload=payload, prev_hash=prev_hash, hash=h)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(_to_json(entry), sort_keys=True) + "\n")
    return entry


def _to_json(entry: AuditEntry) -> dict:
    return {"seq": entry.seq, "at": entry.at, "type": entry.type, "payload": entry.payload,
            "prevHash": entry.prev_hash, "hash": entry.hash}


def list_entries(limit: int = 200) -> list[dict]:
    return _read_all()[-limit:]


def verify() -> dict:
    """Recompute every hash from its content and check it against the stored chain.

    Returns {"ok": bool, "checked": int, "brokenAt": int | None, "reason": str | None}.
    """
    entries = _read_all()
    prev_hash = GENESIS_HASH
    for entry in entries:
        expected = _compute_hash(entry["seq"], entry["at"], entry["type"], entry["payload"], prev_hash)
        if entry["prevHash"] != prev_hash:
            return {"ok": False, "checked": entry["seq"], "brokenAt": entry["seq"],
                    "reason": f"entry {entry['seq']}: prevHash does not match the previous entry's hash"}
        if entry["hash"] != expected:
            return {"ok": False, "checked": entry["seq"], "brokenAt": entry["seq"],
                    "reason": f"entry {entry['seq']}: stored hash does not match its recomputed content hash"}
        prev_hash = entry["hash"]
    return {"ok": True, "checked": len(entries), "brokenAt": None, "reason": None}


def tamper(seq: int, mutate: dict) -> bool:
    """Demo-only: overwrite one entry's payload in place without recomputing its hash, so
    `verify()` catches it. Never reachable outside DEMO_MODE — see api/main.py."""
    entries = _read_all()
    if seq < 0 or seq >= len(entries):
        return False
    entries[seq]["payload"] = {**entries[seq]["payload"], **mutate}
    with open(LOG_PATH, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry, sort_keys=True) + "\n")
    return True


def reset() -> None:
    """Demo-only: wipe the log so a rehearsal starts clean."""
    if os.path.isfile(LOG_PATH):
        os.remove(LOG_PATH)
