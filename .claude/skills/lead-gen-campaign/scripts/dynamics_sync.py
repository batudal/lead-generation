#!/usr/bin/env python3
"""Stage 5 — Dedupe + create/update Dynamics 365 leads, tagged with the campaign.

ALWAYS run --dry-run first and show the user create/update/skip counts before committing.

Usage:
  python3 dynamics_sync.py --in runs/<run>/leads.json --campaign "2026-06-21-fintech-cfos" --out runs/<run>/crm.json --dry-run
  python3 dynamics_sync.py --in runs/<run>/leads.json --campaign "2026-06-21-fintech-cfos" --out runs/<run>/crm.json
"""
import argparse
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(__file__))
from lib.common import env, http, load_json, save_json, checkpoint, info  # noqa: E402

# Adjust these to match your org's schema (see references/dynamics-field-mapping.md)
FIELD_LINKEDIN = "new_linkedinurl"
FIELD_CAMPAIGN = "new_campaign"


def get_token():
    tenant = env("DYNAMICS_TENANT_ID")
    body = urllib.parse.urlencode({
        "grant_type": "client_credentials",
        "client_id": env("DYNAMICS_CLIENT_ID"),
        "client_secret": env("DYNAMICS_CLIENT_SECRET"),
        "scope": env("DYNAMICS_RESOURCE").rstrip("/") + "/.default",
    }).encode()
    url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
    import urllib.request
    req = urllib.request.Request(url, data=body,
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    import json as _json
    with urllib.request.urlopen(req, timeout=60) as resp:
        return _json.loads(resp.read().decode())["access_token"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--campaign", required=True, help="Campaign slug used to tag records")
    ap.add_argument("--entity", default="leads", choices=["leads", "contacts"])
    ap.add_argument("--out", required=True)
    ap.add_argument("--no-custom-fields", action="store_true",
                    help="Skip LinkedIn/campaign custom columns if your org lacks them")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    base = env("DYNAMICS_RESOURCE").rstrip("/") + "/api/data/v9.2"
    leads = load_json(args.inp)

    token = get_token()
    info("Dynamics: authenticated.")
    headers = {
        "Authorization": f"Bearer {token}",
        "OData-MaxVersion": "4.0",
        "OData-Version": "4.0",
        "Accept": "application/json",
    }
    eset = args.entity  # 'leads' or 'contacts'

    results = []
    created = updated = skipped = 0
    for lead in leads:
        email = (lead.get("email") or "").strip()
        linkedin = (lead.get("linkedin_url") or "").strip()

        # --- dedupe ---
        existing_id = None
        if email:
            q = f"{base}/{eset}?$filter=emailaddress1 eq '{email}'&$select={eset[:-1]}id"
            found = http("GET", q, headers=headers).get("value", [])
            if found:
                existing_id = found[0].get(f"{eset[:-1]}id")
        if not existing_id and linkedin and not args.no_custom_fields:
            q = f"{base}/{eset}?$filter={FIELD_LINKEDIN} eq '{linkedin}'&$select={eset[:-1]}id"
            try:
                found = http("GET", q, headers=headers).get("value", [])
                if found:
                    existing_id = found[0].get(f"{eset[:-1]}id")
            except SystemExit:
                pass  # custom field may not exist; ignore for dedupe

        # --- build record ---
        rec = {
            "firstname": lead.get("first_name"),
            "lastname": lead.get("last_name"),
            "jobtitle": lead.get("title"),
            "emailaddress1": email or None,
            "address1_city": lead.get("location"),
            "description": lead.get("personalization"),
        }
        if eset == "leads":
            rec["companyname"] = lead.get("company")
        if not args.no_custom_fields:
            rec[FIELD_LINKEDIN] = linkedin or None
            rec[FIELD_CAMPAIGN] = args.campaign
        rec = {k: v for k, v in rec.items() if v is not None}

        # --- write ---
        if existing_id:
            http("PATCH", f"{base}/{eset}({existing_id})", headers=headers, body=rec,
                 dry_run=args.dry_run)
            updated += 1
            results.append({"email": email, "action": "updated", "id": existing_id})
        else:
            wh = dict(headers, **{"Prefer": "return=representation"})
            resp = http("POST", f"{base}/{eset}", headers=wh, body=rec, dry_run=args.dry_run)
            new_id = resp.get(f"{eset[:-1]}id") if isinstance(resp, dict) else None
            created += 1
            results.append({"email": email, "action": "created", "id": new_id})

    save_json(args.out, results)
    run_dir = os.path.dirname(os.path.abspath(args.out))
    checkpoint(run_dir, "5-crm-sync")
    tag = " [DRY-RUN — no writes made]" if args.dry_run else ""
    print(f"Dynamics sync{tag}: created {created} / updated {updated} / skipped {skipped} "
          f"({len(leads)} leads) -> {args.out}")
    if args.dry_run:
        print("Review these counts with the user, then re-run WITHOUT --dry-run to commit.")


if __name__ == "__main__":
    main()
