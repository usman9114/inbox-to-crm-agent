"""Provider-agnostic LLM call. LLM_PROVIDER = zai (default) | openrouter | openai | anthropic."""
import json
import os
import threading
import time
from dataclasses import dataclass

from pydantic import ValidationError

from prompts import RETRY_NOTE, SYSTEM, user_message
from schema import Extraction

TOOL_NAME = "record_extraction"
DEFAULTS = {
    "zai": "glm-4.5-flash",
    "openrouter": "anthropic/claude-haiku-4.5",
    "openai": "gpt-4o-mini",
    "anthropic": "claude-haiku-4-5",
}
MAX_ATTEMPTS = int(os.getenv("LLM_MAX_ATTEMPTS", "3"))


class ExtractionFailed(Exception):
    pass


@dataclass
class Result:
    extraction: Extraction
    model: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: int
    cost_usd: float | None = None
    attempts: int = 1
    backoff_retries: int = 0


def provider() -> str:
    return os.getenv("LLM_PROVIDER", "zai").lower()


def model_name() -> str:
    return os.getenv("LLM_MODEL") or DEFAULTS[provider()]


def _schema() -> dict:
    return Extraction.model_json_schema()


def _call_openai_compatible(messages: list[dict], model: str):
    from openai import OpenAI

    p = provider()
    tool_choice = {"type": "function", "function": {"name": TOOL_NAME}}
    if p == "zai":
        # Z.ai GLM: OpenAI-compatible; only tool_choice "auto" is supported, thinking off for speed
        client = OpenAI(api_key=os.environ["ZAI_API_KEY"], base_url=os.getenv("ZAI_BASE_URL", "https://api.z.ai/api/paas/v4"),
                        timeout=90, max_retries=0)
        extra = {"extra_body": {"thinking": {"type": "disabled"}}}
        tool_choice = "auto"
    elif p == "openrouter":
        client = OpenAI(api_key=os.environ["OPENROUTER_API_KEY"], base_url="https://openrouter.ai/api/v1", timeout=60)
        extra = {"extra_body": {"usage": {"include": True}}}
    else:
        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"], timeout=60)
        extra = {}
    resp = _with_backoff(lambda: client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0,
        max_tokens=800,
        tools=[{"type": "function", "function": {"name": TOOL_NAME, "description": "Record the triage result", "parameters": _schema()}}],
        tool_choice=tool_choice,
        **extra,
    ))
    msg = resp.choices[0].message
    raw = msg.tool_calls[0].function.arguments if msg.tool_calls else _strip_fences(msg.content or "")
    u = resp.usage
    cost = getattr(u, "cost", None) if u else None
    return raw, (u.prompt_tokens if u else 0), (u.completion_tokens if u else 0), cost


def _strip_fences(text: str) -> str:
    """Models that answer in plain text sometimes wrap the JSON in a markdown fence."""
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1] if "\n" in t else ""
        t = t.rsplit("```", 1)[0]
    return t.strip()


_retries = threading.local()


def _with_backoff(fn, tries: int = 6):
    """Retry rate limits (429), Z.ai 'service overloaded' (code 1305) and 5xx with exponential backoff."""
    from openai import APIConnectionError, APIStatusError, APITimeoutError

    for i in range(tries):
        if i:
            _retries.n = getattr(_retries, "n", 0) + 1
        try:
            return fn()
        except APIStatusError as e:
            retryable = e.status_code == 429 or e.status_code >= 500 or "1305" in str(e)
            if not retryable or i == tries - 1:
                raise
        except (APIConnectionError, APITimeoutError):
            if i == tries - 1:
                raise
        time.sleep(min(60, 2 ** i))


def _call_anthropic(messages: list[dict], model: str):
    import anthropic

    client = anthropic.Anthropic(timeout=60)
    system = messages[0]["content"]
    resp = client.messages.create(
        model=model,
        max_tokens=800,
        temperature=0,
        system=system,
        messages=messages[1:],
        tools=[{"name": TOOL_NAME, "description": "Record the triage result", "input_schema": _schema()}],
        tool_choice={"type": "tool", "name": TOOL_NAME},
    )
    block = next((b for b in resp.content if b.type == "tool_use"), None)
    raw = json.dumps(block.input) if block else ""
    return raw, resp.usage.input_tokens, resp.usage.output_tokens, None


def extract(sender: str, subject: str, body: str) -> Result:
    model = model_name()
    call = _call_anthropic if provider() == "anthropic" else _call_openai_compatible
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user_message(sender, subject, body)}]
    t0 = time.perf_counter()
    _retries.n = 0
    pt = ct = 0
    cost = None
    last_err = "no output"
    for attempt in range(1, MAX_ATTEMPTS + 1):
        raw, p, c, k = call(messages, model)
        pt, ct = pt + p, ct + c
        if k is not None:
            cost = (cost or 0) + k
        try:
            ex = Extraction.model_validate(json.loads(raw))
            return Result(ex, model, pt, ct, int((time.perf_counter() - t0) * 1000), cost, attempt, _retries.n)
        except (json.JSONDecodeError, ValidationError, TypeError) as err:
            last_err = str(err)[:400]
            messages = messages[:2] + [
                {"role": "assistant", "content": raw or "(empty)"},
                {"role": "user", "content": RETRY_NOTE.format(error=last_err)},
            ]
    raise ExtractionFailed(f"invalid output after {MAX_ATTEMPTS} attempts: {last_err}")
