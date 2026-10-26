#!/usr/bin/env python3
"""Stage 2 — Discover accounts/people with Exa, normalize into candidates.json.

Usage:
  python3 exa_search.py --query "Series B fintechs hiring a Head of Compliance" --num 50 --out runs/<run>/candidates.json
  python3 exa_search.py --similar-to https://known-good-account.com --num 25 --out runs/<run>/candidates.json
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from lib.common import env, http, save_json, checkpoint  # noqa: E402

BASE = "https://api.exa.ai"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", help="Semantic query describing the page/company you want to find")
    ap.add_argument("--similar-to", help="Seed URL to find look-alike accounts")
    ap.add_argument("--num", type=int, default=50)
    ap.add_argument("--type", default="auto", choices=["auto", "neural", "keyword"])
    ap.add_argument("--out", required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not args.query and not args.similar_to:
        ap.error("provide --query or --similar-to")

    key = env("EXA_API_KEY")
    headers = {"x-api-key": key}

    if args.similar_to:
        url = f"{BASE}/findSimilar"
        body = {"url": args.similar_to, "numResults": args.num,
                "contents": {"text": {"maxCharacters": 1000}, "highlights": True}}
    else:
        url = f"{BASE}/search"
        body = {"query": args.query, "type": args.type, "numResults": args.num,
                "contents": {"text": {"maxCharacters": 1000}, "highlights": True}}

    if args.dry_run:
        print(f"[dry-run] would POST {url} with {body}")
        return

    resp = http("POST", url, headers=headers, body=body)
    results = resp.get("results", [])

    candidates = []
    for r in results:
        signal = ""
        if r.get("highlights"):
            signal = " … ".join(r["highlights"])[:500]
        elif r.get("text"):
            signal = r["text"][:500]
        candidates.append({
            "company": None,          # resolved later by Clay people search
            "title": r.get("title"),
            "url": r.get("url"),
            "published": r.get("publishedDate"),
            "signal": signal,
            "source": "exa",
        })

    save_json(args.out, candidates)
    run_dir = os.path.dirname(os.path.abspath(args.out))
    checkpoint(run_dir, "2-discover")
    print(f"Exa returned {len(candidates)} candidates -> {args.out}")
    print("Review these with the user before enriching (cheapest place to fix aim).")


if __name__ == "__main__":
    main()
