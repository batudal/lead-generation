# Exa API — discovery

Base: `https://api.exa.ai`
Auth header: `x-api-key: $EXA_API_KEY`

## Search
`POST /search`
```json
{
  "query": "Series B fintech companies hiring a Head of Compliance",
  "type": "auto",                // "neural" | "keyword" | "auto"
  "numResults": 50,
  "contents": { "text": { "maxCharacters": 1000 }, "highlights": true }
}
```
- `type: "auto"` lets Exa pick neural vs keyword. Use `neural` for thesis/concept queries, `keyword` for exact phrases.
- Phrase queries as a *description of the page you want to find*, not a question. "Companies that recently raised a Series B in climate hardware" beats "who raised climate money".

## Find similar
`POST /findSimilar`
```json
{ "url": "https://example-good-account.com", "numResults": 25, "contents": { "text": true } }
```
Use to expand from one known-good account into look-alikes.

## Response shape
```json
{ "results": [
  { "title": "...", "url": "https://...", "publishedDate": "...",
    "author": "...", "text": "...", "highlights": ["..."] }
] }
```

## Usage in this skill
`scripts/exa_search.py` normalizes results into `candidates.json`:
```json
[{ "company": null, "title": "...", "url": "...", "signal": "<highlight/text snippet>", "source": "exa" }]
```
`company` is often null from raw web results — Clay's people search (stage 3) resolves people + company from these URLs/signals.
