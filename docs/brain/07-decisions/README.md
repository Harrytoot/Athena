# 07-decisions — Decision Records

## Purpose

Decisions 层记录 Athena 项目中的所有重要决策，形成完整的决策追溯链。

每条决策记录应包含：决策内容、决策依据、考虑过的替代方案、决策后果。

## Scope

- 投资决策（策略选择、仓位调整等）
- 架构决策（与 ADR 互补，记录 ADR 之外的决策）
- 研究路线决策
- 数据源选择决策
- 技术选型决策（非架构层面）
- 任何需要记录上下文的重要选择

## Allowed Document Types

- `DECISION-*` — 单条决策记录

## Required Metadata

```yaml
id: DECISION-###
title: <title>
status: Proposed | Accepted | Deprecated | Superseded
version: <semver>
decision_type: investment | architecture | research | data | technical
domain: market | macro | industry | factor | policy | sentiment | execution | ontology
owner: <decision_maker>
reviewer: <name>
created: <YYYY-MM-DD>
decided: <YYYY-MM-DD>
reviewed: <YYYY-MM-DD>
supersedes: [DECISION-###, ...]
superseded_by: [DECISION-###, ...]
references:
  knowledge: [KNOWLEDGE-###, ...]
  research: [RESEARCH-###, ...]
  evidence: [EVIDENCE-###, ...]
  playbook: [PLAYBOOK-###, ...]
  adr: [ADR-###, ...]
```

## Required Content Sections

每条 Decision 必须包含：

1. **Context** — 决策背景
2. **Decision** — 决策内容
3. **Rationale** — 决策理由
4. **Alternatives Considered** — 考虑过的替代方案
5. **Consequences** — 决策后果（正面与负面）
6. **Evidence Basis** — 证据基础

## Lifecycle

```
Proposed → Accepted → Active → Deprecated → Archived

Proposed → Rejected (保留记录)
```

## Naming Convention

```
DECISION-###-short-description.md
```

编号使用三位数字，从 001 开始。

## Relationship

- **上游**: Knowledge、Research、Evidence、Playbooks — 决策依据
- **下游**: Failures（04-failures/）— 错误决策记录
- **补充**: ADR（../adr/）— 架构决策另有 ADR 体系
- **被引用者**: 所有 Brain 层级 — 重要决策需在各层文档中引用
