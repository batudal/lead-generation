# Dynamics 365 — CRM sync field mapping

Web API base: `${DYNAMICS_RESOURCE}/api/data/v9.2`
Auth: `Authorization: Bearer <token>` (client-credentials, scope `${DYNAMICS_RESOURCE}/.default`)

## Auth
`POST https://login.microsoftonline.com/${DYNAMICS_TENANT_ID}/oauth2/v2.0/token`
```
grant_type=client_credentials
client_id=${DYNAMICS_CLIENT_ID}
client_secret=${DYNAMICS_CLIENT_SECRET}
scope=${DYNAMICS_RESOURCE}/.default
```

## Entity choice
This skill writes to **`leads`** (entity set `leads`) by default — outbound prospects are leads until qualified. Switch to `contacts` with `--entity contacts` if your process creates contacts directly.

## Field map (our leads.json → Dynamics `lead`)
| leads.json | Dynamics field | Notes |
|------------|----------------|-------|
| `first_name` | `firstname` | |
| `last_name` | `lastname` | |
| `title` | `jobtitle` | |
| `company` | `companyname` | |
| `email` | `emailaddress1` | dedupe key |
| `linkedin_url` | *custom* e.g. `new_linkedinurl` | second dedupe key; create the column or map to an existing one |
| `location` | `address1_city` | or parse to city/country |
| `personalization` | `description` | or a custom note field |
| campaign slug | `new_campaign` / `leadsourcecode` | tag so you can segment later |

> The LinkedIn and campaign columns are commonly custom (`new_` prefix). Set the actual logical names at the top of `dynamics_sync.py` (`FIELD_LINKEDIN`, `FIELD_CAMPAIGN`) to match your org, or pass `--no-custom-fields` to skip them.

## Dedupe
Before creating, query for an existing record:
```
GET /leads?$filter=emailaddress1 eq 'jane@acme.com'&$select=leadid
```
- Match on `email` first; if empty, fall back to the LinkedIn URL custom field.
- Match found → **PATCH** (update) that `leadid`. No match → **POST** (create).
- This keeps re-runs idempotent (no duplicate leads).

## Write
- Create: `POST /leads` with `Prefer: return=representation` to get the new `leadid`.
- Update: `PATCH /leads(<leadid>)`.

`crm.json` output records `{ email, action: created|updated|skipped, leadid }` per lead.
