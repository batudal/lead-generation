#!/usr/bin/env python3
"""Stage 6 — Build a HeyReach LinkedIn list and (optionally) attach it to a PAUSED campaign.

This script NEVER starts/resumes a campaign. Starting is a manual step in the HeyReach UI.
Step content (connection note, messages) is defined on a prepared campaign template in the UI.

Usage:
  python3 heyreach_campaign.py --in runs/<run>/leads.json --name "2026-06-21-fintech-cfos" \
      --campaign-id 9876 --out runs/<run>/sequences.json
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from lib.common import env, http, load_json, save_json, checkpoint, info  # noqa: E402

BASE = "https://api.heyreach.io/api/public"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--name", required=True, help="List name (use the campaign slug)")
    ap.add_argument("--campaign-id", type=int, help="Existing PAUSED campaign to attach the list to")
    ap.add_argument("--out", required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    key = env("HEYREACH_API_KEY")
    headers = {"X-API-KEY": key}

    # 1) create empty list
    resp = http("POST", f"{BASE}/list/CreateEmptyList", headers=headers,
                body={"name": args.name}, dry_run=args.dry_run)
    list_id = resp.get("id") or resp.get("listId") if isinstance(resp, dict) else None
    info(f"HeyReach list created: id={list_id}")

    # 2) add LinkedIn-eligible leads (keyed on profile URL, not email)
    leads = load_json(args.inp)
    hr_leads, skipped = [], 0
    for lead in leads:
        url = lead.get("linkedin_url")
        if not url:
            skipped += 1
            continue
        hr_leads.append({
            "firstName": lead.get("first_name"),
            "lastName": lead.get("last_name"),
            "profileUrl": url,
            "companyName": lead.get("company"),
            "position": lead.get("title"),
            "customUserFields": [{"name": "personalization",
                                  "value": lead.get("personalization") or ""}],
        })

    if hr_leads:
        # batch in chunks of 100
        for i in range(0, len(hr_leads), 100):
            chunk = hr_leads[i:i + 100]
            http("POST", f"{BASE}/list/AddLeadsToListV2", headers=headers,
                 body={"listId": list_id, "leads": chunk}, dry_run=args.dry_run)

    # 3) optionally attach the list to an existing PAUSED campaign
    attached = False
    if args.campaign_id:
        http("POST", f"{BASE}/campaign/AddLeadsToCampaignV2", headers=headers,
             body={"campaignId": args.campaign_id, "listId": list_id}, dry_run=args.dry_run)
        attached = True

    # NOTE: we deliberately do NOT call /campaign/Resume or any start endpoint.

    seq = load_json(args.out, default={}) if os.path.exists(args.out) else {}
    seq["heyreach"] = {"list_id": list_id, "campaign_id": args.campaign_id,
                       "leads_loaded": len(hr_leads), "skipped_no_linkedin": skipped,
                       "attached": attached, "started": False}
    save_json(args.out, seq)
    run_dir = os.path.dirname(os.path.abspath(args.out))
    checkpoint(run_dir, "6-sequences")
    print(f"HeyReach: {len(hr_leads)} leads in list {list_id} "
          f"({skipped} skipped, no LinkedIn URL). Campaign remains PAUSED — start it manually.")


if __name__ == "__main__":
    main()
