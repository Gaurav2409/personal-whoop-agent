# Privacy Policy — personal-whoop-agent

_Last updated: 2026-09-19_

This is a **personal, single-user** integration that lets the app owner's own
AI agent harnesses (e.g. Hermes, Claude) read their own WHOOP data.

**What data is accessed:** via the WHOOP OAuth API with the scopes
`read:profile`, `read:body_measurement`, `read:cycles`, `read:recovery`,
`read:sleep`, `read:workout` — i.e., the owner's own profile, body
measurements, physiological cycles/strain, recovery, sleep, and workout records.

**How data is used:** requests are made on demand by the owner's locally
running software and passed to the owner's locally configured AI assistant to
answer questions about their own health and training data. Data is **not**
sold, shared, or transferred to any third party. No WHOOP data is persisted
beyond short-lived OAuth tokens.

**Where tokens live:** OAuth access/refresh tokens and app credentials are
stored only in the owner's local Windows credential manager (keychain) on the
owner's own machine.

**Data deletion / revocation:** the owner can revoke access at any time by
running `python -m whoop_mcp --revoke`, by removing the app in the WHOOP app
settings, or by contacting the contact email registered for this app in the
WHOOP Developer Dashboard.

**Contact:** the email listed in the WHOOP Developer Dashboard for this app.
