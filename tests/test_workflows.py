import json
from pathlib import Path

N8N = Path(__file__).resolve().parents[1] / "n8n"


def test_workflows_have_no_credentials():
    for f in [N8N / "workflow.json", N8N / "error_workflow.json", *(N8N / "demo-local-mock").glob("*.json")]:
        wf = json.loads(f.read_text())
        assert all("credentials" not in n for n in wf["nodes"]), f


def test_main_workflow_has_expected_nodes():
    wf = json.loads((N8N / "workflow.json").read_text())
    types = {n["type"] for n in wf["nodes"]}
    assert {"n8n-nodes-base.webhook", "n8n-nodes-base.emailReadImap", "n8n-nodes-base.httpRequest", "n8n-nodes-base.switch",
            "n8n-nodes-base.googleSheets", "n8n-nodes-base.slack"} <= types
    assert wf["settings"]["errorWorkflow"] == json.loads((N8N / "error_workflow.json").read_text())["id"]
