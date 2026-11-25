"""Run the extractor over the labelled emails and write eval/results.md.

    python eval/run_eval.py --provider openrouter --model anthropic/claude-haiku-4.5 --model openai/gpt-4o-mini

Each (model, email) result is cached in eval/cache/ so a crash or re-run does not re-spend money.
Cost = real token counts returned by the API x the per-token price listed by OpenRouter.
"""
import argparse
import csv
import json
import os
import re
import statistics
import sys
import urllib.request
from collections import Counter, defaultdict
from datetime import date
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "extractor"))

FIELDS = ["company", "contact_name", "email", "phone", "budget", "timeline", "product_interest"]
INTENTS = ["sales_lead", "support", "invoice", "spam", "other"]
CACHE = ROOT / "eval/cache"


def prices(model: str) -> tuple[float, float]:
    """USD per prompt / completion token, from the OpenRouter model list."""
    req = urllib.request.Request("https://openrouter.ai/api/v1/models")
    with urllib.request.urlopen(req, timeout=30) as r:
        for m in json.load(r)["data"]:
            if m["id"] == model:
                return float(m["pricing"]["prompt"]), float(m["pricing"]["completion"])
    raise SystemExit(f"model {model} not found in OpenRouter list")


def norm_text(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s@.$%-]", " ", (s or "").lower())).strip(" .")


def numbers(s: str) -> tuple:
    out = []
    for n, suffix in re.findall(r"(\d[\d,]*\.?\d*)\s*([kKmM]?)", s or ""):
        v = float(n.replace(",", "").rstrip(".") or 0)
        v *= {"k": 1e3, "m": 1e6}.get(suffix.lower(), 1)
        out.append(v)
    return tuple(sorted(out))


def compare(field: str, gold: str, pred: str | None) -> tuple[bool, bool]:
    """returns (exact, fuzzy) for a labelled (non-empty) gold value"""
    pred = pred or ""
    if not pred:
        return False, False
    if field == "phone":
        a, b = re.sub(r"\D", "", gold), re.sub(r"\D", "", pred)
        return a == b, a == b
    if field == "budget":
        a, b = numbers(gold), numbers(pred)
        exact = bool(a) and a == b
        return exact, exact or (bool(a) and set(a) <= set(b))
    a, b = norm_text(gold), norm_text(pred)
    exact = a == b
    fuzzy = exact or SequenceMatcher(None, a, b).ratio() >= 0.8 or (min(len(a), len(b)) >= 3 and (a in b or b in a))
    return exact, fuzzy


def run_one(client, model: str, row: dict) -> dict:
    f = CACHE / (model.replace("/", "_") + f"__{row['id']}.json")
    if f.exists():
        return json.loads(f.read_text())
    r = client.post("/extract", json={k: row[k] for k in ("from", "subject", "body")})
    out = {"status": r.status_code, "data": r.json()}
    if r.status_code == 200:
        CACHE.mkdir(exist_ok=True)
        f.write_text(json.dumps(out))
    return out


def evaluate(model: str, rows, labels) -> dict:
    from fastapi.testclient import TestClient
    import app as appmod

    os.environ["LLM_MODEL"] = model
    client = TestClient(appmod.app)
    pin, pout = prices(model)
    res = {}
    for row in rows:
        res[row["id"]] = run_one(client, model, row)
        print(model, row["id"], res[row["id"]]["status"], flush=True)

    ok = {i: r["data"] for i, r in res.items() if r["status"] == 200}
    failed = [i for i, r in res.items() if r["status"] != 200]
    n = len(rows)
    correct = {i: ok[i]["intent"] == labels[i]["intent"] for i in ok}
    cm = defaultdict(Counter)
    for i, d in ok.items():
        cm[labels[i]["intent"]][d["intent"]] += 1

    fe = Counter(); ff = Counter(); ft = Counter(); false_fill = Counter(); empties = Counter()
    for i, d in ok.items():
        for fld in FIELDS:
            gold = labels[i][fld]
            if gold:
                ft[fld] += 1
                e, fz = compare(fld, gold, d.get(fld))
                fe[fld] += e; ff[fld] += fz
            else:
                empties[fld] += 1
                false_fill[fld] += bool(d.get(fld)) and fld != "email"
    urg_exact = sum(d["urgency"] == int(labels[i]["urgency"]) for i, d in ok.items())
    urg_near = sum(abs(d["urgency"] - int(labels[i]["urgency"])) <= 1 for i, d in ok.items())

    lat = [d["latency_ms"] for d in ok.values()]
    in_tok = sum(d["prompt_tokens"] for d in ok.values())
    out_tok = sum(d["completion_tokens"] for d in ok.values())
    cost = in_tok * pin + out_tok * pout
    review = [i for i, d in ok.items() if d["needs_review"]]
    nonrev = [i for i in ok if i not in review]
    gold_hot = {i for i in ok if labels[i]["intent"] == "sales_lead" and int(labels[i]["urgency"]) >= 4}
    pred_hot = {i for i, d in ok.items() if d["hot"]}
    return dict(
        model=model, n=n, failed=failed, intent_acc=sum(correct.values()) / len(ok),
        intent_correct=sum(correct.values()), cm=cm,
        field_exact={f: (fe[f], ft[f]) for f in FIELDS}, field_fuzzy={f: ff[f] for f in FIELDS},
        exact_all=sum(fe.values()) / sum(ft.values()), fuzzy_all=sum(ff.values()) / sum(ft.values()),
        n_fields=sum(ft.values()), false_fill=sum(false_fill.values()), n_empty=sum(empties[f] for f in FIELDS if f != "email"),
        urg_exact=urg_exact / len(ok), urg_near=urg_near / len(ok),
        review_pct=len(review) / len(ok), review=review,
        acc_nonreview=sum(correct[i] for i in nonrev) / max(1, len(nonrev)),
        acc_review=(sum(correct[i] for i in review) / len(review)) if review else None,
        lat_median=statistics.median(lat), lat_p95=sorted(lat)[int(0.95 * (len(lat) - 1))],
        in_tok=in_tok, out_tok=out_tok, cost_total=cost, cost_100=cost / len(ok) * 100,
        price=(pin, pout), hot=(len(gold_hot & pred_hot), len(gold_hot), len(pred_hot)),
        wrong=[(i, labels[i]["intent"], ok[i]["intent"]) for i in ok if not correct[i]],
    )


def pct(x): return f"{100 * x:.1f}%"


def report(results: list[dict], provider: str) -> str:
    L = [f"# Eval results", "",
         f"Run date: {date.today()}. Labelled set: {results[0]['n']} synthetic emails (`eval/labels.csv`). "
         f"Provider path: `{provider}` (one API, both vendors' models). Extractor code path: `POST /extract`, temperature 0, tool-calling with a Pydantic schema.", "",
         "Generated by `eval/run_eval.py`; nothing in this file is typed by hand.", "", "## Headline", "",
         "| Metric | " + " | ".join(f"`{r['model']}`" for r in results) + " |",
         "|---|" + "---|" * len(results)]
    def row(name, fn): L.append(f"| {name} | " + " | ".join(fn(r) for r in results) + " |")
    row("Intent accuracy", lambda r: f"{pct(r['intent_acc'])} ({r['intent_correct']}/{r['n'] - len(r['failed'])})")
    row("Field match, exact (labelled fields)", lambda r: f"{pct(r['exact_all'])} of {r['n_fields']}")
    row("Field match, fuzzy (labelled fields)", lambda r: f"{pct(r['fuzzy_all'])} of {r['n_fields']}")
    row("Urgency exact / within ±1", lambda r: f"{pct(r['urg_exact'])} / {pct(r['urg_near'])}")
    row("Fields filled where label is empty", lambda r: f"{r['false_fill']} of {r['n_empty']}")
    row("Routed to human review", lambda r: f"{pct(r['review_pct'])} ({len(r['review'])} emails)")
    row("Intent accuracy: auto-routed / reviewed", lambda r: f"{pct(r['acc_nonreview'])} / " + (pct(r['acc_review']) if r['acc_review'] is not None else "n/a"))
    row("Hot-lead alerts: correct / expected / fired", lambda r: f"{r['hot'][0]} / {r['hot'][1]} / {r['hot'][2]}")
    row("Median latency (sequential calls)", lambda r: f"{r['lat_median'] / 1000:.2f} s")
    row("p95 latency", lambda r: f"{r['lat_p95'] / 1000:.2f} s")
    row("Tokens in / out (total)", lambda r: f"{r['in_tok']:,} / {r['out_tok']:,}")
    row("Cost per 100 emails", lambda r: f"${r['cost_100']:.3f}")
    row("Total cost of this run", lambda r: f"${r['cost_total']:.4f}")
    row("Requests that failed", lambda r: str(len(r["failed"])) + (f" ({', '.join(r['failed'])})" if r["failed"] else ""))
    for r in results:
        L += ["", f"## `{r['model']}`", "", "Per-field match (exact / fuzzy / labelled):", "",
              "| Field | Exact | Fuzzy | Labelled |", "|---|---|---|---|"]
        for f in FIELDS:
            e, t = r["field_exact"][f]
            L.append(f"| {f} | {e} | {r['field_fuzzy'][f]} | {t} |")
        L += ["", "Confusion (rows = label, columns = prediction):", "",
              "| label \\ pred | " + " | ".join(INTENTS) + " |", "|---|" + "---|" * len(INTENTS)]
        for g in INTENTS:
            L.append(f"| {g} | " + " | ".join(str(r["cm"][g][p]) for p in INTENTS) + " |")
        L += ["", "Wrong intents: " + (", ".join(f"{i} (label {g}, predicted {p})" for i, g, p in r["wrong"]) or "none"),
              "", "Routed to review: " + (", ".join(r["review"]) or "none"),
              "", f"Price used: ${r['price'][0] * 1e6:.2f} / ${r['price'][1] * 1e6:.2f} per million input / output tokens (OpenRouter list)."]
    L += ["", "## How the numbers are defined", "",
          "- Intent accuracy: predicted intent equals the label.",
          "- Field match is scored only where the label is non-empty. Exact = equal after lower-casing and removing punctuation; phone compares digits only; budget compares the numeric amounts (so `$2,000/month` equals `up to $2,000 per month`). Fuzzy = exact, or string similarity >= 0.8, or one string contains the other (budget: every labelled amount appears in the answer).",
          "- `Fields filled where label is empty` counts hallucination-like fills for company, name, phone, budget, timeline and product interest (email is excluded because the sender address is always available).",
          "- Review = confidence below 0.7, an invalid extracted email, or a sales lead with no contact detail or no company/name.",
          "- Latency is wall time of the whole `/extract` call including retries, one request at a time, from a shared container over a proxy. Treat it as indicative.",
          "- Cost = actual prompt and completion tokens returned by the API x listed price. Cached prompt discounts are not assumed.",
          "- 51 emails is a small set, so one email moves a percentage by about 2 points. These are demo-scale numbers, not a benchmark."]
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", default="openrouter")
    ap.add_argument("--model", action="append", required=True)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--out", default=str(ROOT / "eval/results.md"))
    a = ap.parse_args()
    os.environ["LLM_PROVIDER"] = a.provider
    rows = [json.loads(l) for l in open(ROOT / "sample_data/emails.jsonl")][: a.limit]
    labels = {r["id"]: r for r in csv.DictReader(open(ROOT / "eval/labels.csv"))}
    results = [evaluate(m, rows, labels) for m in a.model]
    Path(a.out).write_text(report(results, a.provider))
    (ROOT / "eval/results.json").write_text(json.dumps(
        [{k: v for k, v in r.items() if k != "cm"} for r in results], indent=1, default=list))
    print("wrote", a.out)


if __name__ == "__main__":
    main()
