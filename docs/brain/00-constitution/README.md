# 00-constitution — Layer 0

## Purpose

Constitution 定义 Athena 项目的长期稳定原则。这些原则是项目的基石，任何修改必须通过 ADR 流程。

## Scope

- 项目愿景与使命
- 核心设计原则
- 不可妥协的架构约束
- 伦理与合规底线
- 长期演进策略

## Allowed Document Types

- `PRINCIPLE-*` — 单一原则文档
- `CONSTITUTION-*` — 宪法级文档（跨原则整合）

## Required Metadata

```yaml
id: PRINCIPLE-###
title: <title>
status: Active | Superseded
version: <semver>
owner: Chief Architect
reviewer: <name>
created: <YYYY-MM-DD>
supersedes: <id>  # if applicable
superseded_by: <id>  # if applicable
adh: <ADR-###>  # 批准该原则的 ADR
```

## Lifecycle

```
Proposed → Approved (via ADR) → Active → Superseded (via ADR) → Archived
```

原则不可直接删除，只能被新原则取代。

## Naming Convention

```
PRINCIPLE-###-short-description.md
CONSTITUTION-###-short-description.md
```

编号使用三位数字，从 001 开始。

## Relationship

- **被引用者**: ADR（批准修改宪法时必须引用）
- **引用**: 无（宪法是最底层约束，不引用其他 Brain 层级）
- **与代码的关系**: 所有代码必须符合宪法原则
