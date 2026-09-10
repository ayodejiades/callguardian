# Eval report — compliance engine

**Pass rate: 27/27 (100%)**

| id | kind | expected | got | result | note |
|---|---|---|---|---|---|
| p01_cleared | predial | CLEARED [] | CLEARED [] | PASS |  |
| p02_no_consent | predial | BLOCKED ['NO_CONSENT'] | BLOCKED ['NO_CONSENT'] | PASS |  |
| p03_suppressed_no_reconsent | predial | BLOCKED ['SUPPRESSED'] | BLOCKED ['SUPPRESSED'] | PASS |  |
| p04_suppressed_then_reconsented | predial | CLEARED [] | CLEARED [] | PASS |  |
| p05_consent_predates_suppression | predial | BLOCKED ['SUPPRESSED'] | BLOCKED ['SUPPRESSED'] | PASS | consent recorded before the suppression event does not excuse it — only a later re-consent does |
| p06_attempt_limit | predial | BLOCKED ['ATTEMPT_LIMIT_EXCEEDED'] | BLOCKED ['ATTEMPT_LIMIT_EXCEEDED'] | PASS |  |
| p07_before_window | predial | BLOCKED ['OUTSIDE_CALL_WINDOW'] | BLOCKED ['OUTSIDE_CALL_WINDOW'] | PASS | 12:00 UTC = 07:00 Chicago, before the 08:00 window start |
| p08_after_window | predial | BLOCKED ['OUTSIDE_CALL_WINDOW'] | BLOCKED ['OUTSIDE_CALL_WINDOW'] | PASS | 03:00 UTC = 22:00 Chicago, after the 21:00 window end |
| p09_window_start_boundary_inclusive | predial | CLEARED [] | CLEARED [] | PASS | 13:00 UTC = 08:00 Chicago exactly, the window start hour is inclusive |
| p10_window_end_boundary_exclusive | predial | BLOCKED ['OUTSIDE_CALL_WINDOW'] | BLOCKED ['OUTSIDE_CALL_WINDOW'] | PASS | 02:00 UTC = 21:00 Chicago exactly, the window end hour is exclusive |
| p11_appointment_reminder_no_consent_needed | predial | CLEARED [] | CLEARED [] | PASS |  |
| p12_healthcare_no_consent_needed | predial | CLEARED [] | CLEARED [] | PASS |  |
| p13_telemarketing_requires_consent | predial | BLOCKED ['NO_CONSENT'] | BLOCKED ['NO_CONSENT'] | PASS |  |
| p14_multiple_reasons_at_once | predial | BLOCKED ['NO_CONSENT', 'OUTSIDE_CALL_WINDOW'] | BLOCKED ['NO_CONSENT', 'OUTSIDE_CALL_WINDOW'] | PASS | both the window and consent checks fail independently; both reasons must be named, not just the first one found |
| p15_relocated_timezone_almost_always_blocked | predial | BLOCKED ['OUTSIDE_CALL_WINDOW'] | BLOCKED ['OUTSIDE_CALL_WINDOW'] | PASS | 15:00 UTC is 03:00 the next day in Auckland |
| t01_explicit_stop | transcript | True | True | PASS |  |
| t02_polite_variant | transcript | True | True | PASS |  |
| t03_ambiguous_call_back_later_is_not_opt_out | transcript | False | False | PASS | a reschedule request is not a revocation of consent and must not be treated as one |
| t04_ambiguous_not_interested_is_not_recognized | transcript | False | False | PASS | known gap: this reads like a soft opt-out to a human but matches none of our explicit phrases — see docs/FAILURE_CASE.md |
| t05_take_me_off_list | transcript | True | True | PASS |  |
| t06_short_ambiguous_not_matched | transcript | False | False | PASS | known gap: an obvious opt-out to a human listener, but 'stop calling' and 'don't call me' both require more words than this — see docs/FAILURE_CASE.md |
| t07_case_insensitive | transcript | True | True | PASS |  |
| t08_embedded_in_longer_transcript | transcript | True | True | PASS |  |
| t09_no_opt_out_language_at_all | transcript | False | False | PASS |  |
| s01_disclosure_present | script | CLEARED | CLEARED | PASS |  |
| s02_disclosure_missing | script | BLOCKED | BLOCKED | PASS |  |
| s03_no_disclosure_required | script | CLEARED | CLEARED | PASS |  |

## Known, honest limits (pass, but worth reading before you trust this in production)

- **p05_consent_predates_suppression**: consent recorded before the suppression event does not excuse it — only a later re-consent does
- **p07_before_window**: 12:00 UTC = 07:00 Chicago, before the 08:00 window start
- **p08_after_window**: 03:00 UTC = 22:00 Chicago, after the 21:00 window end
- **p09_window_start_boundary_inclusive**: 13:00 UTC = 08:00 Chicago exactly, the window start hour is inclusive
- **p10_window_end_boundary_exclusive**: 02:00 UTC = 21:00 Chicago exactly, the window end hour is exclusive
- **p14_multiple_reasons_at_once**: both the window and consent checks fail independently; both reasons must be named, not just the first one found
- **p15_relocated_timezone_almost_always_blocked**: 15:00 UTC is 03:00 the next day in Auckland
- **t03_ambiguous_call_back_later_is_not_opt_out**: a reschedule request is not a revocation of consent and must not be treated as one
- **t04_ambiguous_not_interested_is_not_recognized**: known gap: this reads like a soft opt-out to a human but matches none of our explicit phrases — see docs/FAILURE_CASE.md
- **t06_short_ambiguous_not_matched**: known gap: an obvious opt-out to a human listener, but 'stop calling' and 'don't call me' both require more words than this — see docs/FAILURE_CASE.md
