"""tests/test_api.py — runs in DEMO_MODE, no network, no CALL-E credentials required."""
import os

os.environ.setdefault("DEMO_MODE", "1")

from api.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

# A fixed clock inside every rule pack's call window (10:00 local), so these tests never
# flake depending on what hour they happen to run in real life.
NOON_UTC = "2026-09-11T15:00:00Z"  # 10:00 in America/Chicago (acc_cleared, acc_attempt_limit)


def test_health_reports_demo_mode():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert body["demoMode"] is True


def test_landing_page_loads():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "CallGuardian" in resp.text


def test_signup_then_signin_then_dashboard():
    email = "ops@example.test"
    resp = client.post("/signup", data={"org": "Example Ops", "email": email, "password": "correct horse"},
                        follow_redirects=False)
    assert resp.status_code == 303
    assert "cg_session" in resp.cookies

    resp2 = client.post("/signin", data={"email": email, "password": "correct horse"}, follow_redirects=False)
    assert resp2.status_code == 303

    dash = client.get("/dashboard", cookies={"cg_session": resp2.cookies["cg_session"]})
    assert dash.status_code == 200
    assert email in dash.text


def test_dashboard_redirects_when_signed_out():
    client.cookies.clear()
    resp = client.get("/dashboard", follow_redirects=False)
    assert resp.status_code == 303
    assert resp.headers["location"] == "/signin"


def test_gate_check_clears_a_consented_in_window_account():
    resp = client.post("/api/gate/check", json={"accountId": "acc_cleared", "now": NOON_UTC})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "CLEARED"
    assert body["reasons"] == []


def test_gate_check_blocks_no_consent():
    resp = client.post("/api/gate/check", json={"accountId": "acc_no_consent", "now": NOON_UTC})
    body = resp.json()
    assert body["status"] == "BLOCKED"
    assert any(r["code"] == "NO_CONSENT" for r in body["reasons"])


def test_gate_check_blocks_suppressed_account():
    resp = client.post("/api/gate/check", json={"accountId": "acc_suppressed", "now": NOON_UTC})
    body = resp.json()
    assert body["status"] == "BLOCKED"
    assert any(r["code"] == "SUPPRESSED" for r in body["reasons"])


def test_gate_check_allows_reconsented_account():
    resp = client.post("/api/gate/check", json={"accountId": "acc_reconsented", "now": NOON_UTC})
    body = resp.json()
    assert body["status"] == "CLEARED"


def test_gate_check_blocks_over_attempt_limit():
    resp = client.post("/api/gate/check", json={"accountId": "acc_attempt_limit", "now": NOON_UTC})
    body = resp.json()
    assert body["status"] == "BLOCKED"
    assert any(r["code"] == "ATTEMPT_LIMIT_EXCEEDED" for r in body["reasons"])


def test_place_call_is_refused_for_a_blocked_account():
    resp = client.post("/api/gate/place-call", json={"accountId": "acc_no_consent", "now": NOON_UTC})
    assert resp.status_code == 409
    assert resp.json()["detail"]["status"] == "BLOCKED"


def test_place_call_succeeds_and_writes_audit_entries():
    before = client.get("/api/audit").json()
    resp = client.post("/api/gate/place-call", json={"accountId": "acc_cleared", "now": NOON_UTC})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] in ("completed", "failed", "no_answer", "voicemail", "declined")
    assert body["source"] == "demo_fixture"
    assert len(body["auditHash"]) == 64  # a real sha256 hex digest, not the call id
    after = client.get("/api/audit").json()
    assert len(after) > len(before)
    assert after[-1]["hash"] == body["auditHash"]


def test_gate_check_external_for_a_sheet_row():
    resp = client.post("/api/gate/check-external", json={
        "externalId": "sheet:+15550199", "phone": "+15550199", "timezone": "America/Chicago",
        "rulePack": "appointment-reminder", "consent": {"given": False}, "suppressed": False,
        "now": NOON_UTC,
    })
    assert resp.status_code == 200
    assert resp.json()["status"] == "CLEARED"  # appointment-reminder doesn't require consent


def test_place_call_external_is_refused_outside_the_call_window():
    resp = client.post("/api/gate/place-call-external", json={
        "externalId": "sheet:+15550198", "phone": "+15550198", "timezone": "Pacific/Auckland",
        "rulePack": "us-tcpa-collections", "consent": {"given": True}, "suppressed": False,
        "now": NOON_UTC,
    })
    assert resp.status_code == 409
    assert resp.json()["detail"]["status"] == "BLOCKED"


def test_audit_chain_verifies_and_tamper_breaks_it():
    client.post("/api/gate/check", json={"accountId": "acc_cleared", "now": NOON_UTC})
    verify = client.get("/api/audit/verify").json()
    assert verify["ok"] is True

    client.post("/api/audit/tamper")
    verify_after = client.get("/api/audit/verify").json()
    assert verify_after["ok"] is False
    assert verify_after["brokenAt"] is not None
