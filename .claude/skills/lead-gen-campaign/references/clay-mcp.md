# Clay MCP — source + primary enrichment

Clay is driven via its **MCP server** (added to Claude Code), not a script in this skill.

Reference: https://www.clay.com/mcp

## What Clay MCP can do
- **People search** at target companies — filter by title, seniority, location. ~20 results per query; page through for more.
- **Enrich contacts** — work history and 150+ data providers (waterfalls).
- **Run pre-built Functions** — enrichment waterfalls, lead qualification, outbound prep that your ops team built in the Clay UI.
- **Query Clay Audiences.**

## What Clay MCP CANNOT do
- Create tables or write rows to a table.
- Full campaign management.
- Company-level search (Enterprise + Audiences only).

**Implication:** build the table + Functions once in the Clay UI. The skill triggers existing Functions; it does not author them.

## How stages 3–4 use it

**Stage 3 — Source people + contacts**
1. For each candidate company/URL from `candidates.json`, run people search with the brief's title/seniority/location filters.
2. Pull contact data for matched people.
3. Merge into `leads.json` with at minimum: `name`, `title`, `company`, `linkedin_url`, `email` (may be empty pre-enrichment), `domain`.

**Stage 4 — Primary enrich + qualify**
1. Run the enrichment-waterfall Function to fill `email`, firmographics, phone where allowed.
2. Run the qualification Function; drop leads that fail.
3. Hand the surviving high-value subset to `sixtyfour_enrich.py` for deep research.

## leads.json shape (canonical for the rest of the pipeline)
```json
[{
  "name": "Jane Doe",
  "first_name": "Jane",
  "last_name": "Doe",
  "title": "VP Compliance",
  "company": "Acme Fintech",
  "domain": "acme.com",
  "email": "jane@acme.com",
  "linkedin_url": "https://www.linkedin.com/in/janedoe",
  "location": "London, UK",
  "high_value": true,
  "qualified": true,
  "personalization": null,
  "source": "clay"
}]
```
Keep this shape — every downstream script reads it.
