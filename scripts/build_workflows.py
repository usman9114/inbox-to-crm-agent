"""Generates n8n/workflow.json, n8n/error_workflow.json and the local-mock demo variant.

The exported workflows contain no credentials: Google Sheets / Slack / IMAP nodes carry no
credential block, so n8n asks you to pick or create one after import.
Run:  python scripts/build_workflows.py
"""
import copy
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN_ID, ERR_ID = "inboxcrm01", "inboxcrmerr1"
EXTRACT = "Extract (FastAPI)"

SHEET_ID = {"__rl": True, "mode": "id", "value": "YOUR_SPREADSHEET_ID"}


def sheet(name, tab, pos, cols, matching=None):
    return {
        "id": name.lower().replace(" ", "-"), "name": name, "type": "n8n-nodes-base.googleSheets", "typeVersion": 4.5, "position": pos,
        "parameters": {
            "operation": "appendOrUpdate" if matching else "append",
            "documentId": SHEET_ID,
            "sheetName": {"__rl": True, "mode": "name", "value": tab},
            "columns": {"mappingMode": "defineBelow", "value": cols, "matchingColumns": matching or [], "schema": []},
            "options": {},
        },
    }


def e(path):  # expression pointing at the extractor response of the current item
    return "={{ $('%s').item.json.%s }}" % (EXTRACT, path)


COMMON = {k: e(k) for k in ["company", "contact_name", "email", "phone", "budget", "timeline", "product_interest", "urgency", "intent", "confidence", "summary"]}
COMMON = {"received_at": "={{ $now.toISO() }}", **COMMON}
LEAD_COLS = {**COMMON, "hot": e("hot"), "status": "new"}
REVIEW_COLS = {**COMMON, "review_reasons": "={{ $('%s').item.json.review_reasons.join('; ') }}" % EXTRACT, "status": "needs review"}
OTHER_COLS = {k: COMMON[k] for k in ["received_at", "intent", "contact_name", "email", "company", "urgency", "summary"]}


def rule(value, key):
    return {
        "conditions": {
            "options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict"},
            "conditions": [{"id": f"r-{value}", "leftValue": "={{ $json.route }}", "rightValue": value,
                            "operator": {"type": "string", "operation": "equals"}}],
            "combinator": "and",
        },
        "renameOutput": True, "outputKey": key,
    }


NORMALIZE = r"""// Webhook posts {from, subject, body}; the IMAP trigger gives {from, subject, textPlain}.
const j = $json;
const src = (j.body && typeof j.body === 'object') ? j.body : j;
let from = src.from ?? '';
const m = typeof from === 'string' ? from.match(/<([^>]+)>/) : null;   // "Name <a@b.c>" -> a@b.c
if (m) from = m[1];
return [{ json: { from, subject: src.subject ?? '', body: src.body ?? src.textPlain ?? src.text ?? '' } }];"""


def main_workflow():
    nodes = [
        {"id": "note", "name": "Notes", "type": "n8n-nodes-base.stickyNote", "typeVersion": 1, "position": [-80, -240],
         "parameters": {"width": 520, "height": 200, "content": "## Inbox to CRM\nTwo triggers feed one pipeline: a form/webhook POST and an IMAP mailbox (disabled until you add IMAP credentials).\nThe extractor service classifies the intent, extracts the fields and decides if a human must review. Any failure raises the error workflow."}},
        {"id": "wh", "name": "Inbound email webhook", "type": "n8n-nodes-base.webhook", "typeVersion": 2, "position": [0, 60],
         "webhookId": "inbound-email-0001", "parameters": {"httpMethod": "POST", "path": "inbound-email", "responseMode": "onReceived", "options": {}}},
        {"id": "imap", "name": "IMAP mailbox", "type": "n8n-nodes-base.emailReadImap", "typeVersion": 2, "position": [0, 260], "disabled": True,
         "parameters": {"mailbox": "INBOX", "postProcessAction": "read", "options": {}}},
        {"id": "norm", "name": "Normalize email", "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [260, 160],
         "parameters": {"jsCode": NORMALIZE}},
        {"id": "ext", "name": EXTRACT, "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [500, 160],
         "parameters": {"method": "POST", "url": "http://extractor:8000/extract", "sendBody": True, "specifyBody": "json",
                        "jsonBody": "={{ JSON.stringify({ from: $json.from, subject: $json.subject, body: $json.body }) }}",
                        "options": {"timeout": 60000}}},
        {"id": "sw", "name": "Route", "type": "n8n-nodes-base.switch", "typeVersion": 3, "position": [740, 160],
         "parameters": {"rules": {"values": [rule("lead", "Lead"), rule("review", "Needs review"), rule("other", "Other intent")]}, "options": {}}},
        sheet("Sheet: Leads", "Leads", [1000, 20], LEAD_COLS, ["email"]),
        sheet("Sheet: Needs review", "Needs review", [1000, 180], REVIEW_COLS),
        sheet("Sheet: Other inbox", "Other inbox", [1000, 340], OTHER_COLS),
        {"id": "hot", "name": "Hot lead?", "type": "n8n-nodes-base.if", "typeVersion": 2.2, "position": [1240, 20],
         "parameters": {"conditions": {"options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict"},
                                       "conditions": [{"id": "hot1", "leftValue": e("hot"), "rightValue": "",
                                                       "operator": {"type": "boolean", "operation": "true", "singleValue": True}}],
                                       "combinator": "and"}, "options": {}}},
        {"id": "slack", "name": "Slack: hot lead", "type": "n8n-nodes-base.slack", "typeVersion": 2.3, "position": [1480, -20],
         "parameters": {"select": "channel", "channelId": {"__rl": True, "mode": "name", "value": "#hot-leads"},
                        "text": "=Hot lead (urgency " + "{{ " + "$('%s').item.json.urgency" % EXTRACT + " }}/5): {{ $('%s').item.json.company || 'unknown company' }}, {{ $('%s').item.json.contact_name || '' }} <{{ $('%s').item.json.email }}>\n{{ $('%s').item.json.summary }}" % (EXTRACT, EXTRACT, EXTRACT, EXTRACT),
                        "otherOptions": {}}},
    ]
    conns = {
        "Inbound email webhook": [["Normalize email"]],
        "IMAP mailbox": [["Normalize email"]],
        "Normalize email": [[EXTRACT]],
        EXTRACT: [["Route"]],
        "Route": [["Sheet: Leads"], ["Sheet: Needs review"], ["Sheet: Other inbox"]],
        "Sheet: Leads": [["Hot lead?"]],
        "Hot lead?": [["Slack: hot lead"], []],
    }
    return {
        "id": MAIN_ID, "name": "Inbox to CRM agent", "nodes": nodes,
        "connections": {k: {"main": [[{"node": n, "type": "main", "index": 0} for n in out] for out in v]} for k, v in conns.items()},
        "settings": {"executionOrder": "v1", "errorWorkflow": ERR_ID}, "active": False,
        "versionId": "6f1d6a4e-0b57-4c0e-9d0a-5b0c7a111111", "pinData": {},
    }


def error_workflow():
    nodes = [
        {"id": "et", "name": "Error Trigger", "type": "n8n-nodes-base.errorTrigger", "typeVersion": 1, "position": [0, 100], "parameters": {}},
        {"id": "sl", "name": "Slack: error alert", "type": "n8n-nodes-base.slack", "typeVersion": 2.3, "position": [260, 20],
         "parameters": {"select": "channel", "channelId": {"__rl": True, "mode": "name", "value": "#automation-alerts"},
                        "text": "=Workflow failed: {{ $json.workflow.name }}\nNode: {{ $json.execution.lastNodeExecuted }}\nError: {{ $json.execution.error.message }}\nExecution: {{ $json.execution.url }}",
                        "otherOptions": {}}},
        sheet("Sheet: Errors", "Errors", [260, 200], {
            "failed_at": "={{ $now.toISO() }}", "workflow": "={{ $json.workflow.name }}", "node": "={{ $json.execution.lastNodeExecuted }}",
            "error": "={{ $json.execution.error.message }}", "execution_id": "={{ $json.execution.id }}"}),
    ]
    return {
        "id": ERR_ID, "name": "Inbox to CRM: error handler", "nodes": nodes,
        "connections": {"Error Trigger": {"main": [[{"node": "Slack: error alert", "type": "main", "index": 0},
                                                       {"node": "Sheet: Errors", "type": "main", "index": 0}]]}},
        "settings": {"executionOrder": "v1"}, "active": False,
        "versionId": "6f1d6a4e-0b57-4c0e-9d0a-5b0c7a222222", "pinData": {},
    }


def demo_variant(wf, extractor_url, mock_url, suffix):
    """Swap the Google Sheets and Slack nodes for HTTP calls to the local mock sink (demo only)."""
    wf = copy.deepcopy(wf)
    wf["name"] += " (local mock sink)"
    wf["id"] = wf["id"] + suffix
    if "settings" in wf and "errorWorkflow" in wf["settings"]:
        wf["settings"]["errorWorkflow"] = ERR_ID + suffix
    for n in wf["nodes"]:
        p = n["parameters"]
        if n["type"] == "n8n-nodes-base.googleSheets":
            tab = p["sheetName"]["value"]
            cols = p["columns"]["value"]
            expr = ", ".join(f"{json.dumps(k)}: ({v[3:-3].strip()})" if v.startswith("={{") else f"{json.dumps(k)}: {json.dumps(v)}" for k, v in cols.items())
            n["type"], n["typeVersion"] = "n8n-nodes-base.httpRequest", 4.2
            n["name"] = n["name"] + " (mock)"
            n["parameters"] = {"method": "POST", "url": f"{mock_url}/sheet/{tab}", "sendBody": True, "specifyBody": "json",
                               "jsonBody": "={{ JSON.stringify({ " + expr + " }) }}", "options": {}}
        elif n["type"] == "n8n-nodes-base.slack":
            n["type"], n["typeVersion"] = "n8n-nodes-base.httpRequest", 4.2
            n["name"] = n["name"] + " (mock)"
            n["parameters"] = {"method": "POST", "url": f"{mock_url}/slack/{p['channelId']['value'].lstrip('#')}", "sendBody": True,
                               "specifyBody": "json", "jsonBody": "={{ JSON.stringify({ text: `" + re.sub(r"\{\{\s*(.*?)\s*\}\}", r"${\1}", p["text"][1:].replace("`", "'")) + "` }) }}", "options": {}}
        elif n["name"] == EXTRACT:
            p["url"] = f"{extractor_url}/extract"
    return wf


def rename_connections(wf, orig):
    names = {o["name"]: n["name"] for o, n in zip(orig["nodes"], wf["nodes"])}
    wf["connections"] = {names[k]: {"main": [[dict(c, node=names[c["node"]]) for c in out] for out in v["main"]]} for k, v in wf["connections"].items()}
    return wf


def write(path, obj):
    (ROOT / path).write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main, err = main_workflow(), error_workflow()
    write("n8n/workflow.json", main)
    write("n8n/error_workflow.json", err)
    demo_dir = ROOT / "n8n/demo-local-mock"
    demo_dir.mkdir(exist_ok=True)
    for orig, name in ((main, "workflow"), (err, "error_workflow")):
        d = rename_connections(demo_variant(orig, "http://localhost:8000", "http://localhost:9000", "m"), orig)
        write(f"n8n/demo-local-mock/{name}.json", d)
    print("ok")
