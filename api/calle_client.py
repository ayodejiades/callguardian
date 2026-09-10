"""api/calle_client.py — the one module that actually talks to CALL-E at runtime.

Request/response shape confirmed 2026-09-10 against the real API with a live account and
one real call (`call_fXCiuIQ2q98YVvU7TPiKtQ`, to the reserved fictional number
+1-555-0101 — see AGENTS.md task CALLE-1). Findings that corrected the original,
PR-#419-inferred shape:

- There is no `to` field. The API extracts the E.164 destination from free text in
  `task` itself (or from a separate `recipients` list of objects — not used here, embedding
  in `task` is simpler and is what's implemented). Sending `to` gets a 422
  `extra_forbidden`.
- The created/polled object is a `call_task`, not a bare "call": top-level `id`, `status`
  (`queued` -> terminal `completed`/`failed`/...), `summary`, `task_completed`,
  `failure_code`/`failure_message`, and a `recipients[]` array whose entries carry their
  own `attempts[]`, each attempt holding `transcript_turns` (a list — empty when the call
  never connects, as in the verified test) and its own `summary`.
- A call that never connects (bad/reserved number, no answer) is `status: "failed"` with
  `failure_code: "call_failed"` at the top level and `"404"` on the specific attempt — this
  is what CallGuardian's own audit log now records for that case, not a crash.

Not yet verified: the exact shape of a `transcript_turns` entry from a call that actually
connects and talked to someone (the fictional test number cannot answer). `_extract_transcript`
below is written defensively for that reason — see docs/FAILURE_CASE.md.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass

from api.settings import settings

FIXTURE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fixtures", "calle")
TERMINAL_STATUSES = {"completed", "failed", "canceled", "cancelled"}


@dataclass
class CallOutcome:
    call_id: str
    status: str
    transcript: str
    summary: str
    source: str  # "live" | "demo_fixture" | "error_fallback"
    error: str | None = None

    def to_dict(self) -> dict:
        return {
            "callId": self.call_id, "status": self.status, "transcript": self.transcript,
            "summary": self.summary, "source": self.source, "error": self.error,
        }


def _idempotency_key(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:32]


def _load_fixture(name: str) -> dict:
    path = os.path.join(FIXTURE_DIR, f"{name}.json")
    if not os.path.isfile(path):
        path = os.path.join(FIXTURE_DIR, "default.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _extract_transcript(data: dict) -> str:
    """Flatten recipients[].attempts[].transcript_turns into one string. Turn shape from a
    connected, talking call is unverified (see module docstring) — handles both a plain
    string turn and a {speaker/role, text/content} dict defensively rather than crashing
    on whichever shape turns out to be real."""
    lines = []
    for recipient in data.get("recipients") or []:
        for attempt in recipient.get("attempts") or []:
            for turn in attempt.get("transcript_turns") or []:
                if isinstance(turn, str):
                    lines.append(turn)
                elif isinstance(turn, dict):
                    speaker = turn.get("speaker") or turn.get("role") or ""
                    text = turn.get("text") or turn.get("content") or ""
                    lines.append(f"{speaker}: {text}".strip(": "))
    return "\n".join(lines)


def place_call(account_id: str, phone: str, script_text: str, disposition_hint: str = "default") -> CallOutcome:
    """Place exactly one CALL-E call, gated by the caller (api/main.py never calls this
    without a CLEARED compliance.Decision first). In DEMO_MODE, or when no API key is
    configured, returns a deterministic fixture instead of touching the network.
    """
    idem_key = _idempotency_key(account_id, phone, script_text)

    if settings.demo_mode or not settings.calle_api_key:
        data = _load_fixture(disposition_hint)
        return CallOutcome(
            call_id=f"demo_{idem_key[:12]}", status=data.get("status", "completed"),
            transcript=data.get("transcript", ""), summary=data.get("summary", ""),
            source="demo_fixture",
        )

    import httpx

    try:
        task = f"Call {phone}. {script_text}"
        resp = httpx.post(
            f"{settings.calle_base_url}/v1/calls",
            headers={
                "Authorization": f"Bearer {settings.calle_api_key}",
                "Idempotency-Key": idem_key,
            },
            json={"task": task},
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        call_id = data.get("id", idem_key)

        for _ in range(30):
            if data.get("status") in TERMINAL_STATUSES:
                break
            time.sleep(2)
            poll = httpx.get(
                f"{settings.calle_base_url}/v1/calls/{call_id}",
                headers={"Authorization": f"Bearer {settings.calle_api_key}"}, timeout=30,
            )
            poll.raise_for_status()
            data = poll.json()

        return CallOutcome(
            call_id=call_id, status=data.get("status", "unknown"),
            transcript=_extract_transcript(data), summary=data.get("summary", ""),
            source="live",
        )
    except Exception as exc:  # noqa: BLE001 — the failure this module shows on camera:
        # a live CALL-E error never becomes a silent CLEARED/success, it becomes a visible
        # ERROR_FALLBACK outcome that the audit log records honestly (see docs/FAILURE_CASE.md).
        return CallOutcome(
            call_id=f"error_{idem_key[:12]}", status="error", transcript="", summary="",
            source="error_fallback", error=str(exc),
        )
