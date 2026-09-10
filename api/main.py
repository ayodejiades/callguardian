"""api/main.py — FastAPI app. Landing/auth/dashboard pages plus the gate + audit API the
dashboard and the Google Sheets Apps Script plugin both call. /health, /api/accounts,
/api/gate/check, /api/gate/place-call, /api/audit, /api/audit/verify, /api/audit/tamper.
"""
from __future__ import annotations

import os

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from api import accounts as accounts_mod
from api import audit as audit_mod
from api import auth
from api import calle_client
from api import compliance
from api import rules
from api.settings import settings

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app = FastAPI(title="CallGuardian")
templates = Jinja2Templates(directory=os.path.join(ROOT, "templates"))

_ILLUSTRATIONS_DIR = os.path.join(ROOT, "public", "illustrations")
if os.path.isdir(_ILLUSTRATIONS_DIR):
    app.mount("/illustrations", StaticFiles(directory=_ILLUSTRATIONS_DIR), name="illustrations")


def _current_user(request: Request) -> str | None:
    return auth.read_session_cookie(request.cookies.get(auth.SESSION_COOKIE))


@app.get("/health")
@app.get("/api/health")
async def health():
    return {"ok": True, "sha": "dev", "demoMode": settings.demo_mode}


# --- pages -------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    return templates.TemplateResponse(request, "landing.html", {})


@app.get("/signup", response_class=HTMLResponse)
async def signup_form(request: Request):
    return templates.TemplateResponse(request, "signup.html", {})


@app.post("/signup")
async def signup_submit(request: Request, org: str = Form(...), email: str = Form(...), password: str = Form(...)):
    ok, error = auth.create_user(email, password, org)
    if not ok:
        return templates.TemplateResponse(
            request, "signup.html", {"error": error, "org": org, "email": email}, status_code=400,
        )
    resp = RedirectResponse(url="/dashboard", status_code=303)
    resp.set_cookie(auth.SESSION_COOKIE, auth.create_session_cookie(email.strip().lower()),
                     httponly=True, samesite="lax", max_age=auth.SESSION_TTL_SECONDS)
    return resp


@app.get("/signin", response_class=HTMLResponse)
async def signin_form(request: Request):
    return templates.TemplateResponse(request, "signin.html", {})


@app.post("/signin")
async def signin_submit(request: Request, email: str = Form(...), password: str = Form(...)):
    if not auth.verify_user(email, password):
        return templates.TemplateResponse(
            request, "signin.html", {"error": "wrong email or password", "email": email}, status_code=401,
        )
    resp = RedirectResponse(url="/dashboard", status_code=303)
    resp.set_cookie(auth.SESSION_COOKIE, auth.create_session_cookie(email.strip().lower()),
                     httponly=True, samesite="lax", max_age=auth.SESSION_TTL_SECONDS)
    return resp


@app.get("/signout")
async def signout():
    resp = RedirectResponse(url="/", status_code=303)
    resp.delete_cookie(auth.SESSION_COOKIE)
    return resp


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    email = _current_user(request)
    if not email:
        return RedirectResponse(url="/signin", status_code=303)
    return templates.TemplateResponse(request, "dashboard.html", {"email": email})


# --- gate + audit API, called by the dashboard above and by the Apps Script plugin ---

class AccountIdBody(BaseModel):
    accountId: str
    # Only honored when DEMO_MODE=1 (tests and rehearsals need a fixed clock; a live
    # deployment must never let a caller dictate "now" — that would let a client talk its
    # way around the call-window check).
    now: str | None = None


def _resolve_now(now: str | None):
    if now and settings.demo_mode:
        from datetime import datetime
        return datetime.fromisoformat(now.replace("Z", "+00:00"))
    return None


@app.get("/api/accounts")
async def list_accounts():
    return accounts_mod.list_accounts()


@app.post("/api/gate/check")
async def gate_check(body: AccountIdBody):
    account = accounts_mod.get_account(body.accountId)
    if account is None:
        raise HTTPException(404, f"unknown account: {body.accountId}")
    decision = compliance.evaluate_predial(account, now=_resolve_now(body.now))
    audit_mod.append("predial_check", decision.to_dict())
    return decision.to_dict()


@app.post("/api/gate/place-call")
async def gate_place_call(body: AccountIdBody):
    account = accounts_mod.get_account(body.accountId)
    if account is None:
        raise HTTPException(404, f"unknown account: {body.accountId}")

    # Never trust a status the caller claims to have seen earlier — re-check now, at the
    # moment of dialing, which is the only check that matters.
    decision = compliance.evaluate_predial(account, now=_resolve_now(body.now))
    if decision.status != compliance.CLEARED:
        audit_mod.append("call_blocked", decision.to_dict())
        raise HTTPException(409, detail=decision.to_dict())

    pack = rules.get_pack(account["rulePack"])
    script_text = pack.disclosure_text.format(org=account.get("org", "the organization")) if pack.disclosure_text else (
        "Hello, this is an automated call. " + str(account.get("notes", "")))
    script_decision = compliance.evaluate_script(pack.id, script_text)
    if script_decision.status != compliance.CLEARED:
        audit_mod.append("call_blocked", script_decision.to_dict())
        raise HTTPException(409, detail=script_decision.to_dict())

    disposition_hint = "opt_out" if account["id"] == "acc_suppressed" else "default"
    outcome = calle_client.place_call(account["id"], account["phone"], script_text, disposition_hint)
    accounts_mod.record_call_attempt(account["id"])

    opt_out = compliance.evaluate_transcript(pack.id, outcome.transcript)
    if opt_out.detected:
        accounts_mod.mark_suppressed(account["id"], "opt_out_detected")

    entry = audit_mod.append("call_outcome", {
        **outcome.to_dict(), "accountId": account["id"], "optOutDetected": opt_out.detected,
        "matchedPhrase": opt_out.matched_phrase,
    })
    return {**outcome.to_dict(), "optOutDetected": opt_out.detected, "auditHash": entry.hash}


class ConsentBody(BaseModel):
    given: bool = False
    givenAt: str | None = None
    method: str | None = None


class ExternalAccountBody(BaseModel):
    """One row from an external source of record — today, the Google Sheets plugin.
    Unlike AccountIdBody, this carries the account's fields inline instead of looking them
    up in our own fixtures/accounts.json: the spreadsheet itself is the system of record
    for this path, and CallGuardian is purely the gate + the shared audit ledger. Every
    decision here lands in the same hash-chained log as dashboard-originated ones, tagged
    with its source."""

    externalId: str
    org: str = ""
    phone: str
    timezone: str
    rulePack: str
    consent: ConsentBody = ConsentBody()
    suppressed: bool = False
    suppressedAt: str | None = None
    suppressedReason: str | None = None
    callCountToday: int = 0
    notes: str = ""
    now: str | None = None

    def to_account_dict(self) -> dict:
        return {
            "id": self.externalId, "org": self.org, "phone": self.phone, "timezone": self.timezone,
            "rulePack": self.rulePack, "consent": self.consent.model_dump(), "suppressed": self.suppressed,
            "suppressedAt": self.suppressedAt, "suppressedReason": self.suppressedReason,
            "callCountToday": self.callCountToday, "notes": self.notes,
        }


@app.post("/api/gate/check-external")
async def gate_check_external(body: ExternalAccountBody):
    account = body.to_account_dict()
    decision = compliance.evaluate_predial(account, now=_resolve_now(body.now))
    audit_mod.append("predial_check", {**decision.to_dict(), "source": "google_sheets"})
    return decision.to_dict()


@app.post("/api/gate/place-call-external")
async def gate_place_call_external(body: ExternalAccountBody):
    account = body.to_account_dict()
    decision = compliance.evaluate_predial(account, now=_resolve_now(body.now))
    if decision.status != compliance.CLEARED:
        audit_mod.append("call_blocked", {**decision.to_dict(), "source": "google_sheets"})
        raise HTTPException(409, detail=decision.to_dict())

    pack = rules.get_pack(account["rulePack"])
    script_text = pack.disclosure_text.format(org=account.get("org") or "the organization") if pack.disclosure_text else (
        "Hello, this is an automated call. " + str(account.get("notes", "")))
    script_decision = compliance.evaluate_script(pack.id, script_text)
    if script_decision.status != compliance.CLEARED:
        audit_mod.append("call_blocked", {**script_decision.to_dict(), "source": "google_sheets"})
        raise HTTPException(409, detail=script_decision.to_dict())

    outcome = calle_client.place_call(account["id"], account["phone"], script_text)
    opt_out = compliance.evaluate_transcript(pack.id, outcome.transcript)

    entry = audit_mod.append("call_outcome", {
        **outcome.to_dict(), "accountId": account["id"], "optOutDetected": opt_out.detected,
        "matchedPhrase": opt_out.matched_phrase, "source": "google_sheets",
    })
    # No server-side account record to update for an external source — the caller (the
    # Apps Script plugin) is responsible for writing optOutDetected back into its own
    # Suppressed column, since the spreadsheet is the system of record here, not us.
    return {**outcome.to_dict(), "optOutDetected": opt_out.detected, "auditHash": entry.hash}


@app.get("/api/audit")
async def audit_list():
    return audit_mod.list_entries()


@app.get("/api/audit/verify")
async def audit_verify():
    return audit_mod.verify()


@app.post("/api/audit/tamper")
async def audit_tamper():
    if not settings.demo_mode:
        raise HTTPException(403, "tamper demo is only reachable with DEMO_MODE=1")
    entries = audit_mod.list_entries(limit=1)
    if not entries:
        raise HTTPException(400, "audit log is empty — check or call an account first")
    last = entries[-1]
    audit_mod.tamper(last["seq"], {"tamperedAt": "demo"})
    return {"tampered": last["seq"]}
