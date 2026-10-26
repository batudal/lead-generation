---
name: lead-gen-campaign
description: Use when building an outbound lead generation campaign end-to-end — defining an ICP/thesis, discovering accounts and people, enriching contacts, syncing to CRM, and building email + LinkedIn sequences across Exa, Clay, Sixtyfour, Instantly, HeyReach, and Dynamics 365.
---

# Lead Gen Campaign Orchestrator

## Overview

Drives an outbound campaign through a fixed pipeline: **discover → source → enrich → deep-research → CRM sync → build sequences → STOP**. Claude automates every stage that has a clean API/MCP, then **hard-stops before any message is sent**. You launch manually in Instantly/HeyReach.

**Core safety principle: this skill NEVER activates a sequence.** Sequences are always created in a paused/inactive state. Activation is a human action taken in the vendor UI. Violating this is violating the purpose of the skill.

## Tool roles (locked)

| Stage | Tool | How it's driven |
|-------|------|-----------------|
| 1. Discover | **Exa** | API — semantic search: thesis → companies/people + web signals |
| 2. Source people + contacts | **Clay** | MCP — people search + pull contact data |
| 3. Primary enrich | **Clay** | MCP — waterfalls, emails, firmographics, run pre-built Functions |
| 4. Deep research (high-value only) | **Sixtyfour** | API — agentic research → personalization snippets |
| 5. CRM sync | **Dynamics 365** | Web API — dedupe + create/update leads & contacts |
| 6. Build email sequence (PAUSED) | **Instantly** | API — create campaign, load leads, build steps, leave inactive |
| 6. Build LinkedIn sequence (PAUSED) | **HeyReach** | API — create campaign, load leads, build steps, leave inactive |
| 7. Handoff | — | Summary report + manual-launch checklist. HARD STOP. |

## When to use

- Use when the user wants to plan, build, or launch an outbound campaign.
- Use when starting from a thesis/ICP (no list yet) — this is the default "Flow A".
- Do NOT use to send messages, activate sequences, or bulk-email. This skill stops before send, by design.

## Prerequisites (one-time setup)

Run `scripts/check_setup.py` to verify everything below.

1. **Clay MCP** added to Claude Code (the Clay steps use MCP tools, not a script).
2. **A pre-built Clay table + Functions.** Clay MCP cannot create tables or write to them — it can search, enrich, and run Functions that already exist. Build the table + enrichment/qualification Functions once in the Clay UI.
3. **Environment variables** (see `references/env-setup.md`):
   - `EXA_API_KEY`
   - `SIXTYFOUR_API_KEY`
   - `INSTANTLY_API_KEY`
   - `HEYREACH_API_KEY`
   - `DYNAMICS_TENANT_ID`, `DYNAMICS_CLIENT_ID`, `DYNAMICS_CLIENT_SECRET`, `DYNAMICS_RESOURCE` (e.g. `https://yourorg.crm.dynamics.com`)

## Run layout

Every campaign run writes to `runs/<YYYY-MM-DD>-<slug>/`:

```
runs/2026-06-21-fintech-cfos/
  brief.md            # stage 1 output — ICP, offer, target count, sequence angle
  candidates.json     # stage 2 (Exa) — discovered accounts/people + signals
  leads.json          # stage 3-4 — Clay-sourced + enriched + Sixtyfour snippets
  crm.json            # stage 5 — Dynamics record ids + dedupe results
  sequences.json      # stage 6 — Instantly/HeyReach campaign ids (INACTIVE)
  report.md           # stage 7 — summary + manual-launch checklist
  .checkpoint         # last completed stage, for resume
```

Checkpoints make runs **resumable**: a failed stage re-runs from where it stopped instead of restarting the pipeline.

## Pipeline

Create one todo per stage. Work them in order. After each stage, write its output file and update `.checkpoint`.

### Stage 1 — Brief
Collect from the user (or confirm if already given): ICP/thesis, the offer, target lead count, and the sequence angle. Use `references/brief-template.md`. Write `brief.md`. Do not proceed until the brief is filled.

### Stage 2 — Discover (Exa)
```
python3 scripts/exa_search.py --query "<thesis>" --num 50 --out runs/<run>/candidates.json
```
Translate the thesis into a semantic query (and optionally `--similar-to <url>` to expand from a known-good account). Review the candidates with the user before enriching — discovery is the cheapest place to correct aim.

### Stage 3 — Source people + contacts (Clay MCP)
Use Clay MCP tools (not a script):
- People search at the candidate companies with the brief's title/seniority/location filters (~20 results/query; page through).
- Pull contact data for matched people.
Merge results into `leads.json`.

### Stage 4 — Primary enrich (Clay MCP) + deep research (Sixtyfour)
- Run the pre-built Clay **enrichment waterfall** Function to fill emails/firmographics, then the **qualification** Function. Drop leads that fail qualification.
- For the high-value subset only (top accounts per the brief), run deep research:
```
python3 scripts/sixtyfour_enrich.py --in runs/<run>/leads.json --out runs/<run>/leads.json --high-value-only
```
This adds a per-lead `personalization` snippet. Write final `leads.json`.

### Stage 5 — CRM sync (Dynamics)
```
python3 scripts/dynamics_sync.py --in runs/<run>/leads.json --campaign "<slug>" --out runs/<run>/crm.json
```
Dedupes on email (and LinkedIn URL) against existing Dynamics records, creates/updates `leads`+`contacts`, and tags them with the campaign name. See `references/dynamics-field-mapping.md`. Always run `--dry-run` first and show the user the create/update/skip counts.

### Stage 6 — Build sequences (PAUSED — never activate)
Email:
```
python3 scripts/instantly_campaign.py --in runs/<run>/leads.json --brief runs/<run>/brief.md --name "<slug>" --out runs/<run>/sequences.json
```
LinkedIn:
```
python3 scripts/heyreach_campaign.py --in runs/<run>/leads.json --brief runs/<run>/brief.md --name "<slug>" --out runs/<run>/sequences.json
```
Both scripts create the campaign, add leads, and build steps **with status left inactive/paused**. They will refuse to activate. Confirm the printed status is `paused`/`draft` for each.

### Stage 7 — Handoff (HARD STOP)
Write `report.md` using `references/report-template.md`: counts at each stage, the Dynamics campaign tag, the Instantly + HeyReach campaign ids/links, and a manual-launch checklist. Then STOP and tell the user exactly where to click "go". Do not offer to launch.

## Safety gate — read before stage 6

- Sequences are created **inactive**. The skill does not activate, start, resume, or schedule sends.
- If the user says "just launch it," respond that activation is a manual step in the vendor UI by design, and point them to the campaign link in `report.md`.
- Always `--dry-run` Dynamics and review counts before the real write.
- First real use: do a **5-lead test run** into a test Instantly/HeyReach campaign and test Dynamics records before a full campaign.

## Common mistakes

| Mistake | Fix |
|---------|-----|
| Trying to create a Clay table via MCP | Not supported. Build the table + Functions in the UI once; MCP only triggers them. |
| Enriching everything with Sixtyfour | Expensive/slow. Sixtyfour is deep research for high-value targets only; Clay is primary enrichment. |
| Skipping discovery review | Bad aim multiplies downstream cost. Review `candidates.json` with the user first. |
| Writing to Dynamics without dry-run | Always `--dry-run`, confirm create/update/skip counts, then commit. |
| Letting a script activate a sequence | The scripts refuse by design. If you're tempted to add an `--activate` flag, don't. |
```
