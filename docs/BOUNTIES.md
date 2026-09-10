# Prize targeting — CALL-E: Your Code Is Calling

This event has no per-sponsor bounty tracks — one hackathon, four prize categories, judged
on the same four criteria (Real World Impact, Quality of the Idea, Technical
Implementation, Product Experience & Demo). This file maps CallGuardian to each category
in the judges' own language, done before more feature code, per this kit's rule 1.

## Chosen categories (in order of fit)
1. **Most Innovative Use Case** — primary target.
2. **Most Practical Use Case** — secondary target; same build, same submission.
3. **Most Valuable Feedback** — filed separately via CALL-E's own Feedback Survey, not
   this submission. Near-zero marginal effort, five $200 prizes, do it regardless.

## The one build that satisfies all of them
Architecture sentence: a compliance/consent gate sits in front of every CALL-E call —
pre-dial (consent, call-window, suppression, attempt-cap), pre-script (required
disclosure), and in-call (live opt-out detection) — with every decision written to a
tamper-evident, hash-chained audit log, delivered two ways from the same engine: a
dashboard (sign up, see accounts, check/call/verify) and a Google Sheets Apps Script
plugin (the actual community contribution — a PR to `CALLE-AI/awesome-phone-call-agents`
under `plugins/`).

## Criterion-by-criterion mapping

**Real World Impact.** TCPA/FDCPA/Reg F violations carry $500–1,500 in statutory damages
*per call* in the US. A company that wants to point CALL-E at outbound collections,
telemarketing, or healthcare outreach cannot ship without exactly this gate — it is not a
nice-to-have layered on a demo, it is the difference between "workable" and "a real legal
liability," and it is worth building further after the hackathon ends because that
liability does not go away.

**Quality of the Idea.** Every other CALL-E submission we found builds *the calling
agent*. None gate CALL-E behind a real, jurisdiction-pluggable compliance engine that
also ships as a spreadsheet-native community plugin — see `docs/COMPETITIVE_NOTES.md` for
the specific prior art checked before committing to this shape. The rule-pack design
(`api/rules.py`) means a fifth vertical is a new dataclass instance, not new engine code —
that is the "well-scoped and reusable by the community" bar, not just a claim.

**Technical Implementation.** `api/calle_client.py` calls CALL-E's real `/v1/calls`
endpoint at runtime (confirmed base URL and idempotency pattern from a live, tested
integration — see that file's docstring), not a mock standing in for one. The hash-chain
in `api/audit.py` and the rule engine in `api/compliance.py` are exercised by 14 API tests
and a 27-case eval harness with a published pass rate (`evals/REPORT.md`) — not asserted,
shown.

**Product Experience & Demo.** The dashboard makes an abstract compliance decision
visible and inspectable in real time (CLEARED/BLOCKED with named reasons, a live call
outcome, a chain that visibly breaks under tampering) rather than reading as a rules
engine's changelog. The Sheets plugin makes the same engine usable by someone who has
never seen the dashboard.
