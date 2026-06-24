# 02-research — Layer 2

## Purpose

Research 层存储所有研究课题。每个课题必须经过完整的科学方法流程：提出假设、收集证据、设计实验、得出结论、评估置信度。

Research 是 Knowledge 的唯一来源。

## Scope

所有投资领域的研究课题，涵盖市场、宏观、行业、因子、政策、情绪、执行等多个维度。

## Allowed Document Types

- `RESEARCH-*` — 单篇研究报告

## Required Metadata

```yaml
id: RESEARCH-###
title: <title>
status: Draft | In Review | Approved | Rejected | Superseded
version: <semver>
domain: market | macro | industry | factor | policy | sentiment | execution | ontology
confidence: <0-100>
owner: <researcher>
reviewer: <name>
created: <YYYY-MM-DD>
reviewed: <YYYY-MM-DD>
links:
  hypothesis: [HYPOTHESIS-###, ...]
  evidence: [EVIDENCE-###, ...]
  experiments: [EXPERIMENT-###, ...]
  generated_knowledge: [KNOWLEDGE-###, ...]
tags: [tag1, tag2]
```

## Required Content Sections

每篇 Research 必须包含：

1. **Problem** — 研究问题描述
2. **Hypothesis** — 研究假设
3. **Evidence** — 收集的证据（引用 Evidence 层文档）
4. **Experiment** — 实验设计
5. **Conclusion** — 研究结论
6. **Confidence** — 置信度评分（0~100）及理由

## Lifecycle

```
Draft → In Review → Approved → (generates Knowledge) → Archived

Draft → In Review → Rejected → Archived
```

Rejected 的 Research 不可删除，必须保留评审意见。

## Naming Convention

```
RESEARCH-###-short-description.md
```

编号使用三位数字，从 001 开始。

## Relationship

- **上游**: Evidence（06-evidence/）— 证据支撑
- **上游**: Experiments（03-experiments/）— 实验验证
- **下游**: Knowledge（01-knowledge/）— 通过审批后生成 Knowledge
- **下游**: Failures（04-failures/）— 失败的研究记录在 Failures 层
- **下游**: Decisions（07-decisions/）— 重要研究触发决策记录
- **禁止**: 代码不得直接引用 Research，必须通过 Knowledge → Playbook 路径
