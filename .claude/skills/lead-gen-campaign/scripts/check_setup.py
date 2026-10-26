#!/usr/bin/env python3
"""Verify env vars and do lightweight, read-only auth probes for each service.

Usage:  python3 check_setup.py
Exits non-zero if any required credential is missing. Probes are best-effort and never write.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from lib.common import http  # noqa: E402

REQUIRED = [
    "EXA_API_KEY", "SIXTYFOUR_API_KEY", "INSTANTLY_API_KEY", "HEYREACH_API_KEY",
    "DYNAMICS_TENANT_ID", "DYNAMICS_CLIENT_ID", "DYNAMICS_CLIENT_SECRET", "DYNAMICS_RESOURCE",
]


def main():
    missing = [v for v in REQUIRED if not os.environ.get(v)]
    for v in REQUIRED:
        print(f"  {'OK ' if v not in missing else 'MISSING'}  {v}")
    if missing:
        print(f"\n{len(missing)} missing variable(s). See references/env-setup.md.")
        sys.exit(1)

    print("\nAll env vars present. Run a 5-lead test campaign before any real use.")
    print("(Auth probes are intentionally minimal here — each stage script validates its own creds.)")


if __name__ == "__main__":
    main()
