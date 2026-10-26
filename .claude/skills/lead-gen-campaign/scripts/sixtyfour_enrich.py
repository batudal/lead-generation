#!/usr/bin/env python3
"""Stage 4 — Deep research on high-value leads via Sixtyfour; add personalization snippets.

Usage:
  python3 sixtyfour_enrich.py --in runs/<run>/leads.json --out runs/<run>/leads.json --high-value-only
  python3 sixtyfour_enrich.py --in leads.json --out leads.json --all --offer "compliance automation for fintechs"
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from lib.common import env, http, load_json, save_json, checkpoint, ratelimit, info  # noqa: E402

BASE = os.environ.get("SIXTYFOUR_BASE_URL", "https://api.sixtyfour.ai")
ENRICH_PATH = "/enrich-lead"   # update if the vendor changes the route (see references/sixtyfour-api.md)


def struct_for(offer):
    return {
        "recent_activity": "Notable recent posts, talks, job changes, funding, or news in the last 6 months",
        "pain_point": f"A likely pain point this person has that relates to: {offer}",
        "personalization": (
            "One specific, non-generic, one-sentence cold-outreach opener referencing the recent "
            f"activity or pain point above, in the context of: {offer}. No flattery, no 'I noticed'."
        ),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--offer", default="our offer", help="Offer context so personalization is tailored")
    grp = ap.add_mutually_exclusive_group()
    grp.add_argument("--high-value-only", action="store_true", default=True)
    grp.add_argument("--all", dest="all_leads", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    key = env("SIXTYFOUR_API_KEY")
    headers = {"x-api-key": key}
    leads = load_json(args.inp)
    struct = struct_for(args.offer)

    targets = leads if args.all_leads else [l for l in leads if l.get("high_value")]
    info(f"Sixtyfour: {len(targets)} of {len(leads)} leads selected for deep research")

    done = 0
    for lead in targets:
        payload = {
            "lead": {
                "name": lead.get("name"),
                "title": lead.get("title"),
                "company": lead.get("company"),
                "linkedin": lead.get("linkedin_url"),
                "email": lead.get("email"),
            },
            "struct": struct,
        }
        resp = http("POST", BASE + ENRICH_PATH, headers=headers, body=payload, dry_run=args.dry_run)
        if args.dry_run:
            continue
        data = resp.get("structured_data") or resp.get("data") or resp
        lead["personalization"] = data.get("personalization") if isinstance(data, dict) else None
        lead["research"] = data
        done += 1
        ratelimit(1.5)

    save_json(args.out, leads)
    run_dir = os.path.dirname(os.path.abspath(args.out))
    checkpoint(run_dir, "4-deep-research")
    print(f"Sixtyfour enriched {done} leads -> {args.out}")


if __name__ == "__main__":
    main()
