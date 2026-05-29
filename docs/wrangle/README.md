# Wrangle — Drummond_NetOps

> **Headline.** A focused, well-structured Webex bot for Cisco CUCM operations — clean layer boundaries and good coverage of the voice domain — with RBAC defined but not enforced, no automated tests, no production hosting, and one dead-code file that looks like the access control list but isn't.

**Audited at.** `e00fc16` on 2026-05-27
**Scope.** Full repo — all files under `app/`, `schema/`, `create_webhook.py`, `requirements.txt`
**Approx. lines read.** ~4,000 Python lines across ~30 files

## Index

1. [Repo shape & entry points](01-repo-shape.md)
2. [Startup flow](02-startup-flow.md)
3. [Architecture & module boundaries](03-architecture.md)
4. [Data model](04-data-model.md)
5. [Data layer](05-data-layer.md)
6. UI layer — N/A. No UI. All output is plain-text Webex messages.
7. [Infrastructure](07-infrastructure.md)
8. [Auth](08-auth.md)
9. [External integrations](09-integrations.md)
10. [Tests & verification](10-tests.md)
11. [Build, deploy, environments](11-build-deploy.md)
12. [Smells & risks](12-smells-and-risks.md)
13. [Dependency inventory](13-dependencies.md)
14. [Open questions](questions.md)

## What I couldn't audit

- `test_sql.py` — appears to be a dev scratch file; not read
- `app/palo/` — empty stub, nothing to audit
- `app/utils/` — empty, nothing to audit
- `scripts/` — empty
- `logs/` — empty at time of audit
- The actual `dbo.users` SQL Server schema — inferred from app code, not inspected directly
