# 05-playbooks — Layer 5

## Purpose

Playbooks 层存储经过验证的投资行动方案。

Decision Engine **只能**引用 Playbook，**不得**直接引用未经验证的 Research。这是确保决策安全性的最后一道防线。

## Scope

- 选股策略
- 择时规则
- 仓位管理方案
- 风险控制规则
- 组合再平衡方案
- 止损/止盈规则
- 事件驱动策略
- 不同市场环境下的行动方案

## Allowed Document Types

- `PLAYBOOK-*` — 单个 Playbook

## Required Metadata

```yaml
id: PLAYBOOK-###
title: <title>
status: Draft | Review | Approved | Active | Deprecated
version: <semver>
category: selection | timing | position | risk | rebalance | exit | event-driven
activation_conditions: <触发条件描述>
owner: <author>
reviewer: <name>
created: <YYYY-MM-DD>
last_reviewed: <YYYY-MM-DD>
references:
  knowledge: [KNOWLEDGE-###, ...]  # 必须
  research: [RESEARCH-###, ...]    # 可选（通过 Knowledge 间接引用）
  failures: [FAILURE-###, ...]     # 相关失败案例
confidence: <0-100>
```

## Required Content Sections

每个 Playbook 必须包含：

1. **Objective** — 目标
2. **Trigger Conditions** — 触发条件
3. **Action Steps** — 具体行动步骤
4. **Risk Controls** — 风险控制措施
5. **Exit Conditions** — 退出条件
6. **Knowledge Basis** — 引用的 Knowledge 清单
7. **Limitations** — 已知局限性
8. **Performance History** — 历史表现（如有）

## Lifecycle

```
Draft → Review → Approved → Active → Deprecated → Archived
```

Playbook 必须定期 Review（至少每季度一次）。

## Naming Convention

```
PLAYBOOK-###-short-description.md
```

编号使用三位数字，从 001 开始。

## Relationship

- **上游（必须）**: Knowledge（01-knowledge/）— Playbook 必须引用 Knowledge
- **上游（可选）**: Research（02-research/）— 可通过 Knowledge 间接引用
- **上游（参考）**: Failures（04-failures/）— 风险规避措施
- **下游**: Decision Engine — **唯一合法输入**
- **禁止**: Decision Engine 直接使用 Research 或未经验证的策略
