# Demo path

1. **Sign in to CallGuardian** — go to `/signin`
2. **Open the accounts dashboard — eight seeded accounts across four rule packs** — (narration only)
3. **Tick 'simulate a US business afternoon' so the recording is correct regardless of what time it's actually filmed** — click `#demo-clock`
4. **Check a consented, in-window account — CLEARED** — click `[data-demo='check-acc_cleared']`, wait for `[data-demo='status-acc_cleared'] [data-demo='result']`
5. **Check an account with no consent on file — BLOCKED: NO_CONSENT** — click `[data-demo='check-acc_no_consent']`, wait for `[data-demo='status-acc_no_consent'] [data-demo='result']`
6. **Place the cleared call through CALL-E and see the outcome land in the row** — click `[data-demo='call-acc_cleared']`, wait for `[data-demo='status-acc_cleared']`
7. **Verify the audit chain — every decision and call outcome, hash-chained** — click `[data-demo='verify-btn']`, wait for `#verify-result`
8. **Tamper one entry and verify again — the chain visibly breaks at the exact entry** — click `[data-demo='tamper-btn']`, wait for `#verify-result`

Everything not listed above is stubbed, hardcoded, or deleted. That is the correct prioritisation under a deadline, not technical debt.

## Fallback
If the live deploy is unreachable, `docs/fallback.mp4` is a recording of the exact path above, captured in `DEMO_MODE`.
