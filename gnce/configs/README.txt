GNCE standardized input payloads (multi-industry)
Schema: action, content, user_id, timestamp_utc, risk_indicators, meta, industry_id, profile_id (+ optional industry fields).

Meta fields:
- customer_profile_ref: relative profile reference (no absolute host paths)
- customer_profile_hash_sha256: sha256 of the ref string (placeholder for integrity binding; replace with file-content hash if desired)

Files included:
- SOCIAL_MEDIA / VLOP_SOCIAL_META payloads are in the previous pack.
- This pack adds ECOMMERCE, FINTECH, HEALTHCARE, SAAS_B2B with per-profile allow + deny examples.

Naming convention:
<industry>__<profile>__<action>__<allow|deny>__<baseline|block>.json
