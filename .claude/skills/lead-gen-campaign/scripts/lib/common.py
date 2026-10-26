"""Shared helpers for the lead-gen-campaign scripts. Stdlib only — no pip installs."""
import json
import os
import sys
import time
import urllib.request
import urllib.error


def env(name, required=True, default=None):
    val = os.environ.get(name, default)
    if required and not val:
        die(f"Missing required environment variable: {name}  (see references/env-setup.md)")
    return val


def die(msg, code=1):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def info(msg):
    print(msg, file=sys.stderr)


def http(method, url, headers=None, body=None, dry_run=False, timeout=60):
    """Make a JSON HTTP request. Returns parsed JSON (or {} on empty body).

    On dry_run, prints what would be sent and returns a stub instead of calling.
    Retries once on 429/5xx with a short backoff.
    """
    headers = dict(headers or {})
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers.setdefault("Content-Type", "application/json")

    if dry_run and method.upper() in ("POST", "PATCH", "PUT", "DELETE"):
        info(f"[dry-run] {method} {url}")
        if body is not None:
            info("[dry-run] body: " + json.dumps(body)[:800])
        return {"_dry_run": True}

    for attempt in range(2):
        req = urllib.request.Request(url, data=data, headers=headers, method=method.upper())
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode().strip()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            detail = ""
            try:
                detail = e.read().decode()[:500]
            except Exception:
                pass
            if e.code in (429, 500, 502, 503, 504) and attempt == 0:
                info(f"  {e.code} from {url} — retrying in 3s...")
                time.sleep(3)
                continue
            die(f"{method} {url} -> {e.code} {e.reason}\n{detail}")
        except urllib.error.URLError as e:
            die(f"{method} {url} -> network error: {e.reason}")


def load_json(path, default=None):
    if not os.path.exists(path):
        if default is not None:
            return default
        die(f"Input file not found: {path}")
    with open(path) as f:
        return json.load(f)


def save_json(path, data):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    info(f"  wrote {path}")


def checkpoint(run_dir, stage):
    """Record the last completed stage so a run can resume."""
    if not run_dir:
        return
    os.makedirs(run_dir, exist_ok=True)
    with open(os.path.join(run_dir, ".checkpoint"), "w") as f:
        f.write(stage)


def ratelimit(seconds=1.0):
    time.sleep(seconds)
