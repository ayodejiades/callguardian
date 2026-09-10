# Handoff prompt — build the CallGuardian demo video

Copy everything below into a new session with a cheaper model.

---

Build the ~3-minute submission demo video for a project called CallGuardian, using the
`demo-video` kit already installed on this machine (CLIs `demo-new`, `demo-build`,
`demo-record` are on PATH; skill source at `/Users/mac/hackops/skills/demo-video/`).

## Project context

CallGuardian is a compliance gate CALL-E (a phone-calling AI agent platform) calls have to
pass first: pre-dial consent / call-window / do-not-call / attempt-cap checks, a required-
disclosure check, live in-call opt-out detection, and a tamper-evident hash-chained audit
log. It ships two ways from one engine: a dashboard, and a Google Sheets Apps Script
plugin. Built for the "CALL-E: Your Code Is Calling" hackathon.

- Project directory: `/Users/mac/Documents/calling/callguardian`
- Live deploy: https://callguardian-tkhj.onrender.com (runs `DEMO_MODE=1` — safe, no real
  calls, no CALL-E account needed to record against)
- GitHub: https://github.com/ayodejiades/callguardian
- Submission PR: https://github.com/CALLE-AI/awesome-phone-call-agents/pull/437
- Demo path spec (already written, do not redesign it): `docs/DEMO_PATH.md` and
  `docs/demo-path.json`
- Real, verified numbers to use on screen/in narration — do not invent different ones:
  14/14 API tests passing, 27/27 compliance eval cases passing, 4 rule packs (US
  collections/TCPA, US telemarketing/DNC, appointment reminders, healthcare outreach).

## Steps

1. `cd /Users/mac/Documents/calling/callguardian`
2. Record the real screen capture against the demo path:
   `demo-record . --base-url https://callguardian-tkhj.onrender.com`
   (or `--demo-mode` against a local `make dev` instance if the live URL is unreachable).
   Before recording, sign in on the dashboard and tick "simulate a US business afternoon"
   — the demo path assumes this so the clock doesn't accidentally block every account.
3. Scaffold the video project, linked to this one:
   `demo-new callguardian-demo ~/Hackathons --from-project /Users/mac/Documents/calling/callguardian`
4. Write the narration script for each beat (see "Narration content" below), then render:
   `demo-build ~/Hackathons/callguardian-demo`
5. Confirm `out/` contains the final mp4 (and a cover image / captions per the kit's
   normal output) before handing it back.

## Narration content — use these facts, in this order, one beat per demo-path step

1. **Sign in.** One line: this is CallGuardian, a compliance gate CALL-E calls have to
   pass first.
2. **Dashboard.** Eight seeded accounts, four rule packs: US collections, US
   telemarketing, appointment reminders, healthcare outreach.
3. **Check a cleared account (Jordan Blake).** Consent on file, inside the call window —
   cleared.
4. **Check a blocked account (Priya Nair).** No consent on file — blocked, and the reason
   is named, not a bare failure.
5. **Place the call on the cleared account.** Only cleared accounts get dialed. The
   outcome and a real audit hash land back in the row.
6. **Verify the audit log.** Every decision is written to a hash-chained log. Verify
   recomputes the whole thing — chain's intact.
7. **Tamper one entry, verify again.** Edit one line after the fact, verify again — it
   names the exact entry where the chain breaks, not just "something's wrong."
8. **Close.** One line mentioning the Google Sheets plugin exists too (same engine, same
   audit log, delivered where outreach teams already keep their lists), and that this is
   PR #437 against CALLE-AI/awesome-phone-call-agents.

Keep total narration under 3 minutes. Prefer showing the thing over describing it — most
beats need one short sentence, not a paragraph.

## Writing rules — strip every one of these before finalizing the script

The script must read like an engineer explaining their own project, not like AI-generated
marketing copy. Before rendering, check every line against this list and rewrite anything
that matches:

- **No em dashes as a crutch.** Use a period or a comma. (One or two em dashes in the
  whole script is fine if a sentence genuinely needs it — not as the default connector.)
- **No throat-clearing openers.** Cut "In today's fast-paced world," "Let's dive in,"
  "Imagine a world where," "Now, let's talk about." Start with the fact.
- **No "it's not just X, it's Y" construction.** Anywhere.
- **No hype adjectives.** Cut "powerful," "seamless," "robust," "cutting-edge,"
  "game-changing," "revolutionary," "effortless," "unlock," "harness," "leverage,"
  "elevate." Say what it actually does instead.
- **No rule-of-three lists for their own sake.** Only list three things if there are
  genuinely three things, not because triads sound rhythmic.
- **No empty transitions.** Cut "Now, let's take a look at," "Moving on to," "As you can
  see." Just cut to the next beat.
- **No hedging.** Cut "might," "could potentially," "in some ways." State it or cut it.
  This product either blocks the call or it doesn't — say which.
- **No exclamation points.** The subject matter (compliance, audit logs) doesn't call for
  enthusiasm punctuation.
- **No "In conclusion" / summary restatement at the end.** End on the last concrete beat
  (the PR number), not a recap of what was just shown.
- **Vary sentence length and structure.** If three sentences in a row start with the same
  word or follow the same subject-verb-object rhythm, rewrite one of them.
- **Every claim must be a fact from this document, not an invented one.** If you don't
  have the real number or real behavior, cut the sentence rather than guess or round up.

## Done when

- `out/` has a rendered mp4 under ~3 minutes.
- Every number spoken in the video matches this document exactly (14/14, 27/27, 4 rule
  packs, PR #437).
- No sentence in the script trips any rule in "Writing rules" above.
