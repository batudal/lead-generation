# Sixtyfour API — deep research (high-value only)

Base: `https://api.sixtyfour.ai` (override with `SIXTYFOUR_BASE_URL`)
Auth header: `x-api-key: $SIXTYFOUR_API_KEY`

Sixtyfour runs agentic web research on a person/company and returns structured findings you can use for personalization. It is **slower and costlier than Clay enrichment** — reserve it for the high-value subset, not the whole list.

## Enrich a lead
`POST /enrich-lead`
```json
{
  "lead": {
    "name": "Jane Doe",
    "title": "VP Compliance",
    "company": "Acme Fintech",
    "linkedin": "https://www.linkedin.com/in/janedoe",
    "email": "jane@acme.com"
  },
  "struct": {
    "recent_activity": "Notable recent posts, talks, job changes, or news in the last 6 months",
    "pain_point": "A likely pain point relevant to <our offer>",
    "personalization": "One specific, non-generic opener referencing the above"
  }
}
```
- `struct` is the schema you want back: keys = field names, values = natural-language instructions for what to find.
- Pass the offer context into the `struct` instructions so `personalization` is tailored to your pitch.

## Response (shape varies by account/version)
```json
{ "structured_data": {
    "recent_activity": "...",
    "pain_point": "...",
    "personalization": "Saw Acme just opened an EU entity — ..."
} }
```

## Usage in this skill
`scripts/sixtyfour_enrich.py`:
- Reads `leads.json`, selects `high_value == true` (unless `--all`), calls `/enrich-lead` per lead.
- Writes the returned `personalization` (and stashes the rest under `research`) back onto each lead.
- Honors `--dry-run` (prints the payloads, makes no calls) and rate-limits between calls.

> Endpoint/field names are the most likely to drift here — Sixtyfour's API is younger. If `/enrich-lead` 404s, check the dashboard's API docs and update `ENRICH_PATH` at the top of the script.
