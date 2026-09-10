# The failure case this project shows on camera

Per the AI/ML playbook: showing what happens when something breaks is more credible than
a curated happy path. Three real, current limits — not hidden, not yet fixed.

## 1. A live CALL-E error never becomes a silent success

`api/calle_client.py:place_call` wraps the real network call in a broad except: any
failure (timeout, 5xx, an unexpected response shape) returns a `CallOutcome` with
`status="error"` and `source="error_fallback"`, and that outcome — including the error
string — is written to the audit log exactly like a real outcome would be. It never falls
back to pretending the call succeeded. Demo this by pointing `CALLE_BASE_URL` at a
nonexistent host with `DEMO_MODE=0` and a fake key, then placing a call.

## 2. The opt-out matcher is substring-based, not a language model

`api/rules.py`'s `opt_out_phrases` are matched as lowercase substrings against the
transcript (`api/compliance.evaluate_transcript`). This is honest and inspectable, but it
has real, known gaps — see the eval report's "Known, honest limits" section
(`evals/REPORT.md`, cases `t04` and `t06`):

- **"I'm not really interested in discussing this right now"** reads as a soft opt-out to
  a human, and is not detected — it matches none of the explicit phrases.
- **"No, don't. Stop."** is an obvious opt-out to a human listener but is too short to
  match `"stop calling"` or `"don't call me"` verbatim.

The honest fix is a small classifier (or the LLM already inside CALL-E's own pipeline)
judging opt-out intent semantically, not just string containment. Out of scope for this
build; named here rather than discovered by a judge.

## 3. CALL-E's request/response schema — confirmed for the "never connected" path only

`api/calle_client.py`'s request/response handling was corrected on 2026-09-10 against two
real calls to the reserved fictional number `+1-555-0101` (see `AGENTS.md`, task
`CALLE-1`, now resolved). Confirmed for real: the request is `{"task": "Call <phone>. ..."}`
with no separate `to` field; the response is a `call_task` object; a call that never
connects returns `status: "failed"`, an empty `transcript_turns`, and a real `summary`.

**Still an honest gap:** no real, reachable phone has been called, so the shape of a
`transcript_turns` entry from an actual conversation is unverified —
`_extract_transcript` handles both a plain-string turn and a `{speaker/role, text/content}`
dict, but that is an informed guess, not a confirmed fact. If this matters before judging,
place one real call to a number that can actually answer (with that person's consent) and
check the parsed transcript against what CALL-E actually sent.
