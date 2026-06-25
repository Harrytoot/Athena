# Review Policy

## Rule

每一个 Epic 必须经过三个 Gate。只有三项全部通过，Epic 才允许标记为 **Done**。

任何一个 Gate 未通过：禁止进入下一 Epic。

---

## Three Gates

| # | Gate | 审查人 | 检查内容 |
|---|------|--------|---------|
| 1 | **Code Review** | OpenCode | DDD 分层、Provider Pattern、无硬编码、代码风格 |
| 2 | **Architecture Review** | Chief Architect | 架构合规、模块边界、扩展性、ADR 一致 |
| 3 | **Product Acceptance** | Founder | 用户价值闭环、业务闭环完整性 |

---

## Review Record

每次 Review 必须生成独立记录文件，永久保存，不得覆盖历史 Review。

```
docs/project-memory/reviews/
├── EPIC-002-review-001.md
├── EPIC-002-review-002.md  (如有 Re-review)
├── EPIC-003-review-001.md
└── ...
```

---

## Review Document Template

```markdown
# Review: Epic-XXX

| Field | Value |
|-------|-------|
| Epic | 002 |
| Reviewer | |
| Date | |
| Gate | Code / Architecture / Product |
| Result | PASS / FAIL |

## Checklist

- [ ] Item 1
- [ ] Item 2

## Findings

(if any)

## Decision

PASS / FAIL with reason
```

---

## Epic State Machine

```
Pending → In Progress → Implemented → Review → Done
                                          ↓
                                        FAIL → In Progress (rework)
```

---

## Version

1.0.0

## References

- [ADR-008 Sprint 1 Sequence Confirmation](../adr/ADR-008-sprint1-sequence.md)
- [Constitution Article III — Documentation First](../project-charter/Constitution.md)
