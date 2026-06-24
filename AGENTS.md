# AGENTS.md — Instructions for AI Agents

## Project Identity

- **Name**: Athena
- **Phase**: Sprint 1 (Foundation)
- **Goal**: Build foundational platform (no AI Agent, auto-trading, knowledge graph, or DSL yet)

## Design Principles

1. **Documentation First** — All formal deliverables (ADR, RFC, AMS, AES, PRD, API, DB design, task breakdowns) from Chief Architect must be committed to Git with proper reference links.
2. **Plugin Architecture** — Core is extensible via plugins; avoid tight coupling.
3. **DDD** — Organize code by domain bounded contexts, not technical layers.
4. **Extensible** — Design for future capabilities without premature optimization.
5. **Testable** — Unit tests, integration tests, and contract tests required.

## Workflow Rules

- Chat content is NOT treated as requirements unless explicitly marked as a formal deliverable.
- Any changes to architecture, database, API, domain model, or tech stack require an RFC first.
- All formal docs go into `docs/{adr,rfc,ams,aes,prd,api,database,tasks}/`.
- Commit messages follow conventional commits format.

## Tech Stack (Frozen by ADR-001)

- Frontend: Next.js + React + TypeScript + Tailwind CSS + shadcn/ui
- Backend: Python 3.12 + FastAPI + SQLAlchemy 2.x + Pydantic v2
- Database: PostgreSQL 16 + Redis 7 + MinIO
- Infra: Docker Compose + Nginx
- AI Gateway: LiteLLM
- Architecture: DDD + Clean Architecture + Plugin Architecture
