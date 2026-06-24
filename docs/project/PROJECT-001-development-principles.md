# Athena Development Principles

## Principle 1：Architecture First, Evolution Later

Athena 的顶层架构保持稳定。

禁止频繁重构顶层架构。

允许通过新增模块、替换实现、优化算法持续演进。

---

## Principle 2：Sprint Must Produce Deliverables

每个 Sprint 必须有可运行、可验证的产出。

禁止只有文档没有代码。

禁止只有设计没有验证。

---

## Principle 3：Ideas Enter Backlog First

所有新的想法默认进入 Product Backlog。

只有经过评审并排入 Sprint 后才能开发。

---

## Principle 4：Fact Over Assumption

任何算法进入生产前必须经过：

开发 → 回测 → 验证 → Review。

禁止未经验证直接进入正式模型。

---

## Principle 5：Milestone Driven

项目以 Milestone 为核心推进，而不是以文档数量或理论数量衡量进度。

每个 Milestone 必须能够被实际使用。
