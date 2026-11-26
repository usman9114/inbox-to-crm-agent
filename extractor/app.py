import logging

from fastapi import FastAPI, HTTPException

import llm
from schema import EmailIn, ExtractionOut, review_reasons

log = logging.getLogger("extractor")
app = FastAPI(title="inbox-to-crm extractor", version="1.0")


@app.get("/health")
def health():
    return {"ok": True, "provider": llm.provider(), "model": llm.model_name()}


@app.post("/extract", response_model=ExtractionOut)
def extract(mail: EmailIn):
    try:
        r = llm.extract(mail.sender, mail.subject, mail.body)
    except llm.ExtractionFailed as e:
        log.error("extraction failed: %s", e)
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:  # provider/network errors: surface so n8n's error branch fires
        log.exception("llm call failed")
        raise HTTPException(status_code=502, detail=f"llm call failed: {type(e).__name__}")
    x = r.extraction
    reasons = review_reasons(x)
    # fall back to the sender address when the model found none
    data = x.model_dump()
    if not data["email"]:
        data["email"] = mail.sender
    if reasons:
        route = "review"
    elif x.intent == "sales_lead":
        route = "lead"
    else:
        route = "other"
    return ExtractionOut(
        **data,
        needs_review=bool(reasons),
        review_reasons=reasons,
        route=route,
        hot=(x.intent == "sales_lead" and x.urgency >= 4),
        model=r.model,
        latency_ms=r.latency_ms,
        prompt_tokens=r.prompt_tokens,
        completion_tokens=r.completion_tokens,
        backoff_retries=r.backoff_retries,
    )
