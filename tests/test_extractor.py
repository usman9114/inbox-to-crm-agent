import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "extractor"))

import app as appmod  # noqa: E402
import llm  # noqa: E402
from schema import Extraction, review_reasons  # noqa: E402


def ex(**kw):
    base = dict(intent="sales_lead", confidence=0.9, company="Acme", contact_name="Ann", email="a@b.co", phone=None,
                budget=None, timeline=None, product_interest=None, urgency=3, summary="x")
    base.update(kw)
    return Extraction(**base)


def test_clean_lead_needs_no_review():
    assert review_reasons(ex()) == []


def test_low_confidence_goes_to_review():
    assert review_reasons(ex(confidence=0.5))


def test_lead_without_contact_goes_to_review():
    assert review_reasons(ex(email=None, phone=None))


def test_blank_strings_become_none():
    assert ex(phone="  ", budget="N/A").phone is None


@pytest.mark.parametrize("line", (ROOT / "sample_data/invalid_emails.jsonl").read_text().splitlines())
def test_invalid_input_is_rejected_with_422(line):
    r = TestClient(appmod.app).post("/extract", json=json.loads(line))
    assert r.status_code == 422


def test_retry_on_invalid_json(monkeypatch):
    good = json.dumps(dict(intent="spam", confidence=0.9, urgency=1, summary="s"))
    calls = iter(["not json", json.dumps({"intent": "bogus"}), good])
    monkeypatch.setattr(llm, "_call_openai_compatible", lambda m, model: (next(calls), 10, 5, None))
    r = llm.extract("a@b.co", "s", "body")
    assert r.extraction.intent == "spam" and r.attempts == 3


def test_gives_up_after_max_attempts(monkeypatch):
    monkeypatch.setattr(llm, "_call_openai_compatible", lambda m, model: ("nope", 1, 1, None))
    with pytest.raises(llm.ExtractionFailed):
        llm.extract("a@b.co", "s", "body")


def test_llm_failure_returns_502(monkeypatch):
    def boom(*a, **k):
        raise llm.ExtractionFailed("x")
    monkeypatch.setattr(llm, "extract", boom)
    r = TestClient(appmod.app).post("/extract", json={"from": "a@b.co", "subject": "s", "body": "hi"})
    assert r.status_code == 502
