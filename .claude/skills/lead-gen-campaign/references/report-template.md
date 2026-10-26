# Handoff report template

Copy into `runs/<run>/report.md` at stage 7. This is the last thing the skill produces — it ends at "ready to launch," not "launched."

```markdown
# Campaign report — <slug>  (<date>)

## Funnel
| Stage | Tool | Count |
|-------|------|-------|
| Discovered | Exa | <n candidates> |
| Sourced | Clay | <n people> |
| Enriched + qualified | Clay | <n passed> |
| Deep-researched | Sixtyfour | <n high-value> |
| Synced to CRM | Dynamics | created <c> / updated <u> / skipped <s> |
| Email sequence | Instantly | <n leads loaded> |
| LinkedIn sequence | HeyReach | <n leads loaded> |

## Artifacts
- Dynamics campaign tag: `<new_campaign value>`
- Instantly campaign: <id> — <app link> — status: **<paused/draft>**
- HeyReach campaign: <id> — <app link> — status: **<paused>**

## ⚠️ Manual launch checklist (you do this)
- [ ] Review Instantly sequence copy + sending mailboxes/warmup
- [ ] Review HeyReach connection note + sending LinkedIn account limits
- [ ] Spot-check 5 leads' personalization in each tool
- [ ] Confirm sending schedule + daily caps
- [ ] **Activate** in Instantly  (UI → Launch)
- [ ] **Start** in HeyReach  (UI → Start campaign)

Nothing has been sent. Both sequences are paused and waiting on you.
```
```
