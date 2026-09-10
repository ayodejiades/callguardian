"""api/rules.py — jurisdiction/vertical rule packs for the compliance gate.

The gate (api/compliance.py) is generic; everything specific to a regulation or a vertical
lives here as data, not code, so adding a new use case (a new pack) never touches the
engine. This is the thing that differentiates CallGuardian from a single-vertical gate:
one engine, many packs.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RulePack:
    id: str
    label: str
    statute: str
    call_window_start_hour: int  # local to the account's timezone
    call_window_end_hour: int
    requires_consent: bool
    requires_disclosure: bool
    disclosure_text: str
    opt_out_phrases: tuple[str, ...]
    reconsent_cooldown_days: int
    max_attempts_per_day: int


# Opt-out phrasing is intentionally broad — a compliance gate that only catches the exact
# words "stop calling" misses the cases that actually create liability. These are matched
# as substrings against a lowercased transcript in api/compliance.evaluate_transcript.
_COMMON_OPT_OUT = (
    "stop calling",
    "do not call me",
    "don't call me",
    "take me off your list",
    "take me off the list",
    "remove my number",
    "stop contacting me",
    "never call me again",
    "please don't call again",
    "revoke consent",
    "withdraw consent",
    "i want to opt out",
    "opt me out",
)

PACKS: dict[str, RulePack] = {
    "us-tcpa-collections": RulePack(
        id="us-tcpa-collections",
        label="US collections (TCPA / FDCPA / Reg F)",
        statute="47 U.S.C. §227 (TCPA); 15 U.S.C. §1692c (FDCPA); 12 CFR Part 1006 (Reg F)",
        call_window_start_hour=8,
        call_window_end_hour=21,
        requires_consent=True,
        requires_disclosure=True,
        disclosure_text="This is an attempt to collect a debt. Any information obtained will be used for that purpose.",
        opt_out_phrases=_COMMON_OPT_OUT,
        reconsent_cooldown_days=30,
        max_attempts_per_day=1,
    ),
    "us-telemarketing-dnc": RulePack(
        id="us-telemarketing-dnc",
        label="US telemarketing (TCPA / National DNC)",
        statute="47 U.S.C. §227 (TCPA); 16 CFR Part 310 (TSR / National DNC)",
        call_window_start_hour=8,
        call_window_end_hour=21,
        requires_consent=True,
        requires_disclosure=True,
        disclosure_text="This call is a sales call from {org}. You may ask to be placed on our do-not-call list at any time.",
        opt_out_phrases=_COMMON_OPT_OUT,
        reconsent_cooldown_days=365,
        max_attempts_per_day=3,
    ),
    "appointment-reminder": RulePack(
        id="appointment-reminder",
        label="Appointment / service reminders",
        statute="TCPA established-business-relationship exemption (informational, non-marketing)",
        call_window_start_hour=8,
        call_window_end_hour=20,
        requires_consent=False,
        requires_disclosure=False,
        disclosure_text="",
        opt_out_phrases=_COMMON_OPT_OUT,
        reconsent_cooldown_days=0,
        max_attempts_per_day=3,
    ),
    "healthcare-outreach": RulePack(
        id="healthcare-outreach",
        label="Healthcare outreach (TCPA healthcare exemption + HIPAA minimum-necessary)",
        statute="47 CFR §64.1200(a)(3)(v) (healthcare exemption); 45 CFR §164.502(b) (HIPAA minimum necessary)",
        call_window_start_hour=8,
        call_window_end_hour=20,
        requires_consent=False,
        requires_disclosure=True,
        disclosure_text="This call may include information about your treatment, payment, or health care operations.",
        opt_out_phrases=_COMMON_OPT_OUT,
        reconsent_cooldown_days=0,
        max_attempts_per_day=2,
    ),
}


def get_pack(pack_id: str) -> RulePack:
    try:
        return PACKS[pack_id]
    except KeyError as exc:
        raise ValueError(f"unknown rule pack: {pack_id!r} — options: {sorted(PACKS)}") from exc
