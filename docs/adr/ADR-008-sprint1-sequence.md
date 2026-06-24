# ADR-008 Sprint 1 Development Sequence Confirmation

## Status

Approved (2026-06-24)

## Decision

1. 暂不进入 Epic-005 Portfolio
2. 严格按既定顺序执行，不跳跃开发
3. 每个 Epic 完成后必须通过三项 Review 才能进入下一 Epic

## Current Review Status

| Epic | 代码状态 | Review 状态 |
|------|---------|------------|
| Epic-002 Market Center | ✅ `66ef627` | ⏳ Awaiting Review |
| Epic-003 Watchlist | ✅ `3fe1e30` | ⏳ Awaiting Review |
| Epic-004 Stock Detail | ✅ `290c0e0` | ⏳ Awaiting Review |
| Epic-005 Portfolio | ⚪ Pending | — |
| Epic-006 Recommendation | ⚪ Pending | — |
| Epic-001 Authentication | ⚪ Pending | — |

## Review Checklist per Epic

- [ ] Code Review — DDD 分层 / Provider Pattern / 无硬编码
- [ ] Architecture Review — 是否符合 ADR 006 架构修正
- [ ] Product Acceptance — 是否符合 AMS-001 产品定位

## Principle

禁止同时开发多个 Epic。每次只聚焦一个 Epic 的 Review 和完成。

## References

- [RFC-001 Sprint 1 Plan](../rfc/RFC-001-sprint-1-foundation-development-plan.md)
- [ADR-002 Development Principles](../adr/ADR-002-development-principles.md)
- [ADR-006 Architecture Corrections](../adr/ADR-006-architecture-corrections.md)
