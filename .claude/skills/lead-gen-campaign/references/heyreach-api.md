# HeyReach API — LinkedIn sequence (created PAUSED)

Base: `https://api.heyreach.io/api/public`
Auth header: `X-API-KEY: $HEYREACH_API_KEY`

HeyReach models work as **Campaigns** that draw leads from **Lists**. The typical flow: create a list → add leads to the list → create/attach a campaign that uses the list → leave it paused.

## Create a lead list
`POST /list/CreateEmptyList`
```json
{ "name": "2026-06-21-fintech-cfos" }
```
Returns a list id.

## Add leads to the list
`POST /list/AddLeadsToListV2`
```json
{
  "listId": 12345,
  "leads": [{
    "firstName": "Jane",
    "lastName": "Doe",
    "profileUrl": "https://www.linkedin.com/in/janedoe",
    "companyName": "Acme Fintech",
    "position": "VP Compliance",
    "customUserFields": [{ "name": "personalization", "value": "Saw Acme just opened an EU entity — ..." }]
  }]
}
```
- LinkedIn campaigns key on `profileUrl`, not email. Leads without a `linkedin_url` are skipped for HeyReach.

## Campaigns
- `GET /campaign/GetAll` — list campaigns.
- `POST /campaign/AddLeadsToCampaignV2` — attach leads (by list or directly) to an existing campaign.
- Sequence **steps** (connection request, message, delays) are defined on the campaign template in the HeyReach UI. The skill attaches leads to a prepared, paused campaign rather than authoring step content via API.

## DO NOT CALL (start — manual only)
- `POST /campaign/Resume` / any start/activate endpoint. The human starts the campaign in the UI.

## Usage in this skill
`scripts/heyreach_campaign.py` creates a list, adds LinkedIn-eligible leads with `personalization`, and (if `--campaign-id` is given) attaches the list to that paused campaign. It never resumes/starts a campaign and prints the paused status for confirmation.
