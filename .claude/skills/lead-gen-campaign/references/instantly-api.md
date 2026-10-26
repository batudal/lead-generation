# Instantly API (v2) — email sequence (created PAUSED)

Base: `https://api.instantly.ai/api/v2`
Auth header: `Authorization: Bearer $INSTANTLY_API_KEY`

## Create campaign (paused)
`POST /campaigns`
```json
{
  "name": "2026-06-21-fintech-cfos",
  "campaign_schedule": {
    "schedules": [{
      "name": "Default",
      "timing": { "from": "09:00", "to": "17:00" },
      "days": { "1": true, "2": true, "3": true, "4": true, "5": true },
      "timezone": "Etc/GMT"
    }]
  },
  "sequences": [{
    "steps": [
      { "type": "email", "delay": 0, "variants": [{ "subject": "...", "body": "..." }] },
      { "type": "email", "delay": 3, "variants": [{ "subject": "", "body": "..." }] }
    ]
  }]
}
```
- New campaigns are **not sending** until explicitly activated — the create call leaves it in draft/paused. This skill never calls the activate endpoint.
- `delay` is days to wait before the step.
- Use `{{firstName}}`, `{{companyName}}` and custom variables in `body`; pass per-lead values when adding leads.

## Add a lead
`POST /leads`
```json
{
  "campaign": "<campaign_id>",
  "email": "jane@acme.com",
  "first_name": "Jane",
  "last_name": "Doe",
  "company_name": "Acme Fintech",
  "personalization": "Saw Acme just opened an EU entity — ...",
  "custom_variables": { "linkedin": "https://www.linkedin.com/in/janedoe" }
}
```

## DO NOT CALL (activation — manual only)
- `POST /campaigns/{id}/activate` — starts sending. The human does this in the UI. The script must never call it.

## Usage in this skill
`scripts/instantly_campaign.py` creates the campaign from the brief's angle, adds each lead from `leads.json` with `personalization`, then prints the campaign id + status. It asserts status is not "active" and exits.
