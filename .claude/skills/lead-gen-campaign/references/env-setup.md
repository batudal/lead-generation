# Environment setup

The scripts read all credentials from environment variables. Set them in your shell profile, a `.envrc`, or export them before a run. **Never commit keys.**

```bash
# Exa — https://dashboard.exa.ai  (Settings → API Keys)
export EXA_API_KEY="exa_..."

# Sixtyfour — https://app.sixtyfour.ai  (Settings → API)
export SIXTYFOUR_API_KEY="..."
# Optional override if your account uses a different base:
# export SIXTYFOUR_BASE_URL="https://api.sixtyfour.ai"

# Instantly v2 — https://app.instantly.ai  (Settings → Integrations → API)
export INSTANTLY_API_KEY="..."

# HeyReach — https://app.heyreach.io  (Settings → API keys)
export HEYREACH_API_KEY="..."

# Dynamics 365 — Azure AD app registration with Dataverse access (client-credentials)
export DYNAMICS_TENANT_ID="<aad-tenant-guid>"
export DYNAMICS_CLIENT_ID="<app-registration-client-id>"
export DYNAMICS_CLIENT_SECRET="<client-secret>"
export DYNAMICS_RESOURCE="https://yourorg.crm.dynamics.com"   # no trailing slash, no /api path
```

## Dynamics app registration (one-time)

1. Azure Portal → App registrations → New registration.
2. Certificates & secrets → new client secret → copy the value into `DYNAMICS_CLIENT_SECRET`.
3. In Dynamics/Power Platform admin: create an **Application User** bound to that app's client id, and give it a security role that can create/update `lead` and `contact` (e.g. a custom role or Sales). Without the Application User, the token authenticates but every write returns 403.
4. Token endpoint used by the script:
   `https://login.microsoftonline.com/<tenant>/oauth2/v2.0/token` with `scope=<resource>/.default`.

## Verify

```bash
python3 scripts/check_setup.py
```

This checks each env var is present and does a lightweight auth probe per service (no writes).

## Endpoint-version note

API endpoints in `references/*-api.md` reflect the documented shapes as of skill creation. Vendors revise these. If a script returns 404/401 on a call that should work, open the matching reference doc, confirm the current endpoint/auth header against the vendor docs, and update the constant at the top of the script.
