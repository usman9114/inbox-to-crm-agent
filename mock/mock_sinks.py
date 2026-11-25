"""Local mock sinks for the demo: stands in for Google Sheets and Slack, which need real accounts.

POST /sheet/{tab}      upsert (Leads, keyed on email) or append a row into a local SQLite "CRM sheet"
POST /slack/{channel}  store a message as a mock Slack post
GET  /                 simple page that shows both (clearly labelled as a local mock)
Run: uvicorn mock_sinks:app --port 9000
"""
import html
import json
import os
import sqlite3
import threading
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

DB = Path(os.getenv("MOCK_DB", Path(__file__).parent / "data" / "mock.db"))
DB.parent.mkdir(parents=True, exist_ok=True)
lock = threading.Lock()
app = FastAPI(title="local mock sink")
TABS = ["Leads", "Needs review", "Other inbox", "Errors"]


def db():
    c = sqlite3.connect(DB)
    c.execute("create table if not exists rows(id integer primary key autoincrement, tab text, key text, data text)")
    c.execute("create table if not exists slack(id integer primary key autoincrement, channel text, ts text default current_timestamp, text text)")
    return c


@app.post("/sheet/{tab}")
async def sheet(tab: str, req: Request):
    row = await req.json()
    with lock, db() as c:
        key = (row.get("email") or "").lower() if tab == "Leads" else None
        hit = c.execute("select id from rows where tab=? and key=?", (tab, key)).fetchone() if key else None
        if hit:
            c.execute("update rows set data=? where id=?", (json.dumps(row), hit[0]))
        else:
            c.execute("insert into rows(tab,key,data) values(?,?,?)", (tab, key, json.dumps(row)))
    return {"ok": True, "updated": bool(hit)}


@app.post("/slack/{channel}")
async def slack(channel: str, req: Request):
    body = await req.json()
    with lock, db() as c:
        c.execute("insert into slack(channel,text) values(?,?)", (channel, body.get("text", "")))
    return {"ok": True}


@app.delete("/reset")
def reset():
    with lock, db() as c:
        c.execute("delete from rows"); c.execute("delete from slack")
    return {"ok": True}


@app.get("/rows/{tab}")
def rows(tab: str):
    with db() as c:
        return [json.loads(r[0]) for r in c.execute("select data from rows where tab=? order by id", (tab,))]


@app.get("/slack")
def slack_list():
    with db() as c:
        return [{"channel": r[0], "ts": r[1], "text": r[2]} for r in c.execute("select channel, ts, text from slack order by id")]


COLS = {
    "Leads": ["company", "contact_name", "email", "phone", "budget", "timeline", "product_interest", "urgency", "confidence", "hot", "status", "summary"],
    "Needs review": ["intent", "confidence", "contact_name", "email", "company", "review_reasons", "summary"],
    "Other inbox": ["intent", "contact_name", "email", "company", "urgency", "summary"],
    "Errors": ["failed_at", "workflow", "node", "error"],
}


@app.get("/", response_class=HTMLResponse)
def page(tab: str = "Leads"):
    e = html.escape
    tabs = "".join(f'<a class="{"on" if t == tab else ""}" href="/?tab={t}">{t}</a>' for t in TABS)
    cols = COLS.get(tab, [])
    body = "".join(
        "<tr>" + "".join(f"<td>{e(str(r.get(c, '') if r.get(c) is not None else ''))}</td>" for c in cols) + "</tr>"
        for r in rows(tab))
    msgs = "".join(f'<div class="m"><b>#{e(m["channel"])}</b> <i>{e(m["ts"])}</i><br>{e(m["text"]).replace(chr(10), "<br>")}</div>' for m in reversed(slack_list()))
    return f"""<!doctype html><meta charset=utf-8><meta http-equiv=refresh content=2><title>Local mock sink</title>
<style>body{{font:13px system-ui,sans-serif;margin:0;background:#f5f6f8;color:#1c1f26}}
header{{background:#1c1f26;color:#fff;padding:10px 16px;font-weight:600}}header span{{color:#f6c453;font-weight:500;margin-left:10px}}
.wrap{{display:flex;gap:16px;padding:16px}}.sheet{{flex:3;background:#fff;border:1px solid #d9dce3;border-radius:6px;overflow:auto}}
.slack{{flex:1;background:#fff;border:1px solid #d9dce3;border-radius:6px;padding:10px}}
.tabs a{{display:inline-block;padding:7px 14px;color:#555;text-decoration:none;border-bottom:2px solid transparent}}.tabs a.on{{color:#137333;border-color:#137333;font-weight:600}}
table{{border-collapse:collapse;width:100%}}th{{background:#eef0f4;text-align:left;position:sticky;top:0}}td,th{{border:1px solid #e2e4ea;padding:5px 8px;white-space:nowrap;max-width:260px;overflow:hidden;text-overflow:ellipsis}}
.m{{border-left:3px solid #c0392b;background:#faf7f7;padding:6px 8px;margin-bottom:8px}}h4{{margin:0 0 8px}}</style>
<header>CRM sheet and chat feed<span>LOCAL MOCK SINK (stand-in for Google Sheets and Slack, not the real services)</span></header>
<div class=wrap><div class=sheet><div class=tabs>{tabs}</div><table><tr>{''.join(f'<th>{c}</th>' for c in cols)}</tr>{body}</table></div>
<div class=slack><h4>Mock chat messages</h4>{msgs or '<i>no messages yet</i>'}</div></div>"""
