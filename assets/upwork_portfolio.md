# Upwork portfolio item

**Title (40 chars max):** AI lead triage: inbox → CRM → Slack

**Role:** AI automation engineer (solo demo project)

**Description (about 300 chars):**
Demo on synthetic data. Leads sat unread in inboxes and were copied into the CRM by hand. I built an n8n workflow plus a FastAPI service that classifies each email with an LLM, extracts 9 fields to a strict schema, flags uncertain ones for review and alerts Slack on hot leads. Measured on 51 labelled emails: 100% intent accuracy, 94.5% field match, about $0.30 per 100 emails (Claude Haiku 4.5), median 1.9 s.

**Skills tags:** n8n, AI Automation, API Integration, OpenAI API, Claude, FastAPI

**Media order:** demo.gif → cover_1600x1200.png → workflow.png → sheet_result.png

**Notes for the listing:** the GIF and sheet screenshot use a local mock sink standing in for Google Sheets and Slack; say so if asked. Numbers come from `eval/results.md`.
