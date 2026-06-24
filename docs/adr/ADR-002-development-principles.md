# ADR-002 Development Principles

## Status

Approved (2026-06-24)

## Decision

Athena 项目采用以下开发原则：

### 1. User Value First

任何 Sprint 优先开发能够直接产生用户价值的功能。

不得为了技术完整性而优先开发基础设施。

### 2. Vertical Slice

每一个 Epic 必须完成：UI → API → Domain → Database → Provider → Test，形成完整闭环。

### 3. Mock First

第一阶段所有外部依赖统一采用 Provider。Provider 可以 Mock → AKShare → Tushare → Wind。业务代码不得修改。

### 4. Human First

任何自动交易能力必须晚于分析能力。Athena 第一阶段是辅助决策，不是自动交易。

### 5. Documentation First

任何 Feature 必须：PRD → API → Database → TASK → Implementation。

### 6. Repository Is Source Of Truth

Git Repository 为唯一可信来源。聊天内容不得作为正式需求。

## Sprint 1 Development Order (CTO Mandate)

| Priority | Epic | Status |
|----------|------|--------|
| P0 | Epic-002 Market Center | First |
| P0 | Epic-003 Watchlist | Second |
| P0 | Epic-004 Stock Detail | Third |
| P0 | Epic-005 Portfolio | Fourth |
| P1 | Epic-006 Recommendation | Fifth |
| P1 | Epic-001 Authentication | Last |

> Rationale: Sprint 1 is single-user Alpha. Authentication is not user value — market analysis is.

## Measurement

Athena 不以"完成多少代码"衡量进度，而以"完成多少用户价值闭环"衡量进度。

## Acceptance

本 ADR 从 Sprint 1 开始执行。

## References

- CTO Directive (2026-06-24)
- [ADR-001](ADR-001-sprint-1-tech-stack-freeze.md)
- [RFC-001](../rfc/RFC-001-sprint-1-foundation-development-plan.md)
