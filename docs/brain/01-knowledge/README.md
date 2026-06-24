# 01-knowledge — Layer 1

## Purpose

Knowledge 层存储已经验证并长期有效的知识。这些知识的来源只能是：Research → Review → Approval。

Knowledge 是 Playbook 和 Decision Engine 的唯一可信输入。

## Scope

所有已验证的投资领域知识，按以下子域组织：

| 子域 | 目录 | 说明 |
|------|------|------|
| Market | [market/](./market/) | 市场结构与微观机制 |
| Macro | [macro/](./macro/) | 宏观经济指标与政策 |
| Industry | [industry/](./industry/) | 行业分析与竞争格局 |
| Factor | [factor/](./factor/) | 因子投资与风险因子 |
| Policy | [policy/](./policy/) | 监管政策与合规 |
| Sentiment | [sentiment/](./sentiment/) | 市场情绪与投资者行为 |
| Execution | [execution/](./execution/) | 交易执行与成本分析 |
| Ontology | [ontology/](./ontology/) | 领域实体定义与关系 |

## Allowed Document Types

- `KNOWLEDGE-*` — 单条已验证知识

## Required Metadata

```yaml
id: KNOWLEDGE-###
title: <title>
status: Active | Superseded
version: <semver>
domain: market | macro | industry | factor | policy | sentiment | execution | ontology
confidence: <0-100>
owner: Chief Architect
reviewer: <name>
created: <YYYY-MM-DD>
source_research: [RESEARCH-###, ...]  # 来源研究
source_evidence: [EVIDENCE-###, ...]    # 来源证据
supersedes: <id>
superseded_by: <id>
```

## Lifecycle

```
Research Validated → Review → Approved → Active → Superseded → Archived
```

Knowledge 不可直接创建，只能从通过审批的 Research 生成。

## Naming Convention

```
KNOWLEDGE-###-short-description.md
```

编号使用三位数字，从 001 开始。所有子域共享同一编号空间。

## Relationship

- **上游**: Research（02-research/）— 知识只能从已验证的研究生成
- **下游**: Playbooks（05-playbooks/）— Playbook 必须引用 Knowledge
- **下游**: Decision Engine — 决策引擎通过 Playbook 间接使用 Knowledge
- **配套**: Evidence（06-evidence/）— 每条 Knowledge 必须关联来源证据
