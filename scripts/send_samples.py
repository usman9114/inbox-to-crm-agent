"""Post the sample emails to the n8n webhook so you can watch the flow run.

    python scripts/send_samples.py                # first 10 valid samples
    python scripts/send_samples.py --all          # all 51
    python scripts/send_samples.py --invalid      # 4 malformed inputs -> error branch
    python scripts/send_samples.py --ids e001 e021 --delay 3
"""
import argparse
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    return [json.loads(line) for line in open(ROOT / "sample_data" / name) if line.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default=os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/inbound-email"))
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--invalid", action="store_true", help="send the malformed emails instead")
    ap.add_argument("--ids", nargs="*")
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--delay", type=float, default=1.0, help="seconds between posts")
    a = ap.parse_args()

    rows = load("invalid_emails.jsonl" if a.invalid else "emails.jsonl")
    if a.ids:
        rows = [r for r in rows if r["id"] in a.ids]
    elif not a.all and not a.invalid:
        rows = rows[: a.limit]
    for r in rows:
        req = urllib.request.Request(a.url, data=json.dumps(r).encode(), headers={"content-type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                print(f"{r['id']}: HTTP {resp.status} {r.get('subject', '')[:50]}")
        except urllib.error.URLError as e:
            print(f"{r['id']}: failed to post ({e})")
        time.sleep(a.delay)


if __name__ == "__main__":
    main()
