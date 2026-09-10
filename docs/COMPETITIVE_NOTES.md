# Competitive landscape — checked before committing to this shape

`CALLE-AI/awesome-phone-call-agents` is the actual submission target and, as of
2026-09-10, already holds ~137 merged skills/apps plus 100+ open PRs going back to
2026-08-08 — this is not a fresh 4-day field. Two rounds of idea validation happened
before writing CallGuardian's current code; recorded here so nobody re-discovers the same
dead ends.

## Round 1 — "a consent/compliance gate for CALL-E" (rejected as the *whole* product)

Already done, multiple times, more maturely than a solo 4-day build can match from
scratch:

- `apps/python/consent-gate` — pre-flight + redacted audit ledger, dry-run by default,
  published demo video.
- `apps/python/consent-envelope` — two-sided pre/post gate, SHA-256 transcript
  fingerprinting, official `calle-ai` SDK wired.
- `apps/python/reality-resolver` — generic decision engine with a full multi-jurisdiction
  compliance module (`compliance/jurisdictions/us_federal.py`, `us_oregon.py`,
  `eu_common.py`, `fr.py`) sourced from an actual legal research report.
- `apps/python/kept` — collections-specific payment-promise ledger.
- Open PRs #141 (`fintech-collections-callback`), #385 (`ledger-collections-call`), #258
  (`CallGuard AI` — name collision, unrelated scam-call product), #248 (`AgentCover
  CallGate`) — the collections/consent-gate genre is one of the single most repeated
  shapes in the whole repo.

**Decision:** don't compete head-on as a bare gate. Keep the gate as a component (it's
genuinely well-built — rules.py/compliance.py/audit.py), stop pitching it as the entire
submission.

## Round 2 — "a Slack Workflow Builder step for CALL-E" (rejected on feasibility + still crowded)

- Open PR #419 (`feat(slack): add confirmed CALL-E bridge`, 2026-09-09) already ships a
  Slack **slash-command** bridge (`/calle-call`) to CALL-E's real `/v1/calls` endpoint —
  confirmed the base URL (`https://api.heycall-e.com`) and the idempotency-key pattern
  used in `api/calle_client.py`.
- A true Workflow Builder *step* (drag-and-drop, not a slash command) requires Slack's
  "custom functions" — classic "Steps from Apps" was killed 2026-09-26 [sic, per Slack's
  own docs]. Of the two implementations: Deno/TypeScript is the only one that can be
  distributed to other workspaces; Bolt-Python custom functions are beta and **cannot be
  distributed outside your own org**, which directly undercuts "reusable by the
  community." Also `apps/typescript/phone-approval-gate` and `apps/typescript/callaction`
  and `apps/typescript/linecanary` already ship real GitHub Actions for phone-approval and
  monitoring use cases — that adjacent lane is claimed too.

**Decision:** new toolchain (Deno) for a still-partially-claimed lane, on a hard deadline,
was the wrong trade. Rejected in favor of Round 3.

## Round 3 — Google Sheets Apps Script plugin (current direction)

Checked and clear as of 2026-09-10: no `apps script`, `google sheet`, or `zendesk` hits
anywhere in the repo tree or README except the unrelated `google-form-callback` skill
(agent-driven off Form responses, not a Sheets-native menu plugin). Chosen specifically
because it needed no new signup, no card, no geo-restriction, and reuses the Round-1 gate
engine outright — see `plugins/google-sheets-callguardian/`.

**If you are a smaller model resuming this project:** re-run the checks above
(`gh pr list --repo CALLE-AI/awesome-phone-call-agents --state open`, and search the
merged tree) before adding a new "unique" angle — this list goes stale fast at the rate
this repo receives submissions (multiple per day).
