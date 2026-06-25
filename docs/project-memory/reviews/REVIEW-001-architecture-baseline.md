# Review-001: Architecture Baseline Review

| Field | Value |
|-------|-------|
| Epic | Architecture Baseline (Sprint 1 Foundation) |
| Reviewer | OpenCode (AI Agent) |
| Date | 2026-06-24 |
| Gate | Architecture Review |
| Result | **PASS (with fixes applied)** |
| Commit | d984f10 |

## Scorecard

| # | Check | Grade |
|---|-------|-------|
| 1 | DDD Layer Isolation | PASS |
| 2 | Provider Injection | PASS |
| 3 | Dependency Injection | PASS |
| 4 | Repository Isolation | PASS |
| 5 | Layout | PASS |
| 6 | API Client | PASS |
| 7 | Error Handling | PARTIAL |
| 8 | Theme | FAIL |
| 9 | Table Component | FAIL |
| 10 | Docker Compose | PASS |
| 11 | .env.example | FAIL → **FIXED** |
| 12 | Pre-commit Hooks | FAIL → **FIXED** |
| 13 | CI Pipeline | FAIL → **FIXED** |
| 14 | README Setup | PARTIAL → **FIXED** |

## Critical Issues Resolved

1. **Domain entity decoupling** — Created `domain/entities/watchlist.py` with pure domain entities (dataclasses). Repository interface now depends on domain, not application. Service converts domain → DTO at application boundary.

2. **Empty domain model** — `domain/entities/watchlist.py` now contains `Watchlist` (aggregate root) and `WatchlistItem` with domain behavior (`add_item`, `remove_item`, `add_tag`).

3. **`.env.example`** — Created with all required variables.

4. **Pre-commit hooks** — `.pre-commit-config.yaml` with trailing-whitespace, end-of-file-fixer, ruff.

5. **CI pipeline** — `.github/workflows/ci.yml` with backend (lint + test placeholder) and frontend (typecheck + build) jobs.

6. **README** — Added Quick Start section with Docker and local dev instructions.

## Remaining Gaps (Non-blocking for Sprint 1)

- No `error.tsx` / `loading.tsx` (Next.js route-level) — accept for Sprint 1
- No ThemeProvider / dark mode — Sprint 2
- No reusable Table component — accept inline `<table>` for Sprint 1
- Empty `tests/` directory — must fix before Sprint 1 completion per Definition of Done
- `domain/entities/`, `value_objects/`, `aggregates/` subdirectories mostly empty — will fill as Epics progress

## Decision

**PASS** — Architecture baseline is sound. Critical issues fixed. Remaining gaps are acceptable for Sprint 1 scope.
