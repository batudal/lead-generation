#!/usr/bin/env python3
"""Stage 6 — Build an Instantly email campaign (created PAUSED) and load leads.

This script NEVER activates a campaign. Activation is a manual step in the Instantly UI.

Usage:
  python3 instantly_campaign.py --in runs/<run>/leads.json --name "2026-06-21-fintech-cfos" \
      --subject "quick idea for {{companyName}}" --out runs/<run>/sequences.json
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from lib.common import env, http, load_json, save_json, checkpoint, info, ratelimit  # noqa: E402

BASE = "https://api.instantly.ai/api/v2"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--subject", default="quick idea for {{companyName}}")
    ap.add_argument("--body", default=(
        "Hi {{firstName}},\n\n{{personalization}}\n\n"
        "<one-line value prop>. Worth a quick chat?\n\nBest,\n<you>"))
    ap.add_argument("--followup", default=(
        "Hi {{firstName}}, bumping this in case it slipped — happy to send a 2-line summary."))
    ap.add_argument("--out", required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    key = env("INSTANTLY_API_KEY")
    headers = {"Authorization": f"Bearer {key}"}

    # 1) create campaign — left in draft/paused; we never call the activate endpoint
    campaign_body = {
        "name": args.name,
        "campaign_schedule": {"schedules": [{
            "name": "Default",
            "timing": {"from": "09:00", "to": "17:00"},
            "days": {"1": True, "2": True, "3": True, "4": True, "5": True},
            "timezone": "Etc/GMT",
        }]},
        "sequences": [{"steps": [
            {"type": "email", "delay": 0, "variants": [{"subject": args.subject, "body": args.body}]},
            {"type": "email", "delay": 3, "variants": [{"subject": "", "body": args.followup}]},
        ]}],
    }
    resp = http("POST", f"{BASE}/campaigns", headers=headers, body=campaign_body, dry_run=args.dry_run)
    campaign_id = resp.get("id") if isinstance(resp, dict) else None
    status = resp.get("status") if isinstance(resp, dict) else "dry-run"
    info(f"Instantly campaign created: id={campaign_id} status={status}")

    # 2) load leads (email-eligible only)
    leads = load_json(args.inp)
    loaded = 0
    for lead in leads:
        if not lead.get("email"):
            continue
        lead_body = {
            "campaign": campaign_id,
            "email": lead["email"],
            "first_name": lead.get("first_name"),
            "last_name": lead.get("last_name"),
            "company_name": lead.get("company"),
            "personalization": lead.get("personalization") or "",
            "custom_variables": {"linkedin": lead.get("linkedin_url")},
        }
        http("POST", f"{BASE}/leads", headers=headers, body=lead_body, dry_run=args.dry_run)
        loaded += 1
        ratelimit(0.4)

    # 3) safety assertion — refuse to hand back an active campaign
    if not args.dry_run and isinstance(status, str) and status.lower() in ("active", "running"):
        sys.exit("REFUSING TO CONTINUE: campaign reports active. This skill must hand off PAUSED "
                 "campaigns only. Pause it in Instantly and re-check.")

    # merge into sequences.json (heyreach may write the same file)
    seq = load_json(args.out, default={}) if os.path.exists(args.out) else {}
    seq["instantly"] = {"campaign_id": campaign_id, "status": status, "leads_loaded": loaded,
                        "activated": False}
    save_json(args.out, seq)
    run_dir = os.path.dirname(os.path.abspath(args.out))
    checkpoint(run_dir, "6-sequences")
    print(f"Instantly: {loaded} leads loaded into PAUSED campaign {campaign_id}. "
          f"Activate manually in the Instantly UI.")


if __name__ == "__main__":
    main()
