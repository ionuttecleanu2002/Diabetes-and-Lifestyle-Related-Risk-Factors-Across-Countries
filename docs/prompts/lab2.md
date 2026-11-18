# Lab 2 Implementation Prompts

All dates below are **2026-11-18**. The initial request was a 621-line attached master prompt; it is identified by title and summarized rather than copied in full.

## Prompt 1 — Complete the Lab 2 assignment

- Tool and model: Copilot SDK in VS Code; mai-code-2-flash
- Date: 2026-11-18
- Prompt: Attached “# MASTER PROMPT — Complete Lab 2: Global Health Data Platform.” It requested project inspection first, then phased extraction, transformation, cleaning, database migration/loading, imports, notebook, verification, documentation, tests, and a stop for approval after each phase. It prohibited pushing and automatic commits until approval.
- Result: The repository was inspected, then the user approved implementation sequentially through Phase 5. Unit tests were added and the database changes were implemented.
- Your changes: Extraction, transformations, cleaning/IQR, model/migration, idempotent loader, and corresponding tests. Phase 1–5 local commits are present in Git history.

## Prompt 2 — Approve Phase 1

- Tool and model: Copilot SDK in VS Code; mai-code-2-flash
- Date: 2026-11-18
- Prompt: “go with phase 1”
- Result: Began raw extraction implementation.
- Your changes: WHO, World Bank, and OWID extraction modules with caching, response handling and tests.

## Prompt 3 — Continue Phase 2

- Tool and model: Copilot SDK in VS Code; mai-code-2-flash
- Date: 2026-11-18
- Prompt: “continue with phase 2”
- Result: Began source transformations.
- Your changes: Added the three normalized transformation modules and tests.

## Prompt 4 — Continue cleaning phase

- Tool and model: Copilot SDK in VS Code; mai-code-2-flash
- Date: 2026-11-18
- Prompt: “continue with the next one”
- Result: Began Phase 3 after explaining the extraction/transformation distinction.
- Your changes: Added cleaning rules, IQR flags and tests.

## Prompt 5 — Continue Phase 4

- Tool and model: Copilot SDK in VS Code; mai-code-2-flash
- Date: 2026-11-18
- Prompt: “continue with 4”
- Result: Began the database model and Alembic migration.
- Your changes: Added the `is_outlier` model field, migration configuration, migration, schema update and tests.

## Prompt 6 — Check PostgreSQL readiness and configure credentials

- Tool and model: Copilot SDK in VS Code; mai-code-2-flash
- Date: 2026-11-18
- Prompt: “first check if postgresql is installed and ready to be used in our case,” followed by “add a .env to be used for the database connection and also reset the user and password to admin acces123”
- Result: PostgreSQL was found running. At the first check, the requested role was absent and administrative access was unavailable. The user confirmed database `diabetes_health`, role scope limited to this database, and password spelling `acces123`.
- Your changes: Added ignored local `.env`. The role/database setup command was provided; subsequent environment checks confirmed the database role was provisioned by the user.

## Prompt 7 — Continue Phase 5

- Tool and model: Copilot SDK in VS Code; gpt-6-luna
- Date: 2026-11-18
- Prompt: “continue with 5”
- Result: Began PostgreSQL loading implementation.
- Your changes: Added transactional, chunked upserts and import-log behavior with tests.

## Prompt 8 — Continue Phases 6–10 and commit each phase

- Tool and model: Copilot SDK in VS Code; gpt-6-luna
- Date: 2026-11-18
- Prompt: “continue on with all of them from 6 to 10 but after each phase do a git add . and a commit with a short message like the commits that are stored currecntly but not yet pushed”
- Result: Continued through Phase 6 onward and created local commits after Phases 6, 7, and 8. No push was performed.
- Your changes: Added source import scripts and orchestration, exploration notebook, and verification SQL. Ran PostgreSQL migration and imports where endpoints were reachable; documented unavailable WHO and World Bank values.
