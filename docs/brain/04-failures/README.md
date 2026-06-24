# 04-failures — Layer 4

## Purpose

Failures 层记录所有失败的案例。**禁止删除任何失败记录。**

每条记录必须说明：为什么失败、如何发现的、如何避免再次发生。

这是 Athena Brain 最宝贵的资产之一：从错误中学习。

## Scope

- 研究假设被证伪的案例
- 实验失败的案例
- 策略回撤超出预期的案例
- 数据质量问题导致错误决策的案例
- 模型失效的案例
- 交易执行失败的案例
- 任何值得记录的错误

## Allowed Document Types

- `FAILURE-*` — 单个失败记录

## Required Metadata

```yaml
id: FAILURE-###
title: <title>
status: Recorded | Analyzed | Mitigated
version: <semver>
severity: Critical | High | Medium | Low
domain: market | macro | industry | factor | policy | sentiment | execution | ontology
related_research: [RESEARCH-###, ...]
related_experiment: [EXPERIMENT-###, ...]
owner: <reporter>
created: <YYYY-MM-DD>
detected: <YYYY-MM-DD>
```

## Required Content Sections

每条 Failure 必须包含：

1. **What Failed** — 什么失败了
2. **Why It Failed** — 为什么失败
3. **How It Was Detected** — 如何发现的
4. **Impact** — 影响范围与程度
5. **Root Cause** — 根因分析
6. **Mitigation** — 如何避免再次发生
7. **Lessons Learned** — 学到的教训

## Lifecycle

```
Detected → Recorded → Analyzed → Mitigated → Archived (never deleted)
```

失败记录**永久保存，不可删除**。

## Naming Convention

```
FAILURE-###-short-description.md
```

编号使用三位数字，从 001 开始。

## Relationship

- **上游**: Research、Experiments — 失败可能来自研究或实验
- **上游**: Decisions — 决策失误记录
- **下游**: Knowledge — 从失败中学到的教训可以形成 Knowledge
- **下游**: Playbooks — Playbook 应包含风险规避措施，参考失败案例
- **被引用者**: 整个 Athena Brain — 任何新研究都应检查相关失败记录
