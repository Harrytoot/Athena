---
id: BRAIN-001
title: Athena Brain Governance
status: Approved
version: 1.0.0
owner: Chief Architect
reviewer: Founder
created: 2026-06-24
---

# Athena Brain Governance

## Vision

Athena Brain 是项目唯一的长期知识载体。

任何 AI、任何开发者，都应通过 Athena Brain 恢复项目上下文，而不是依赖聊天记录或个人记忆。

---

# Brain Layers

## Layer 0 - Constitution

长期稳定原则。

修改必须经过 ADR。

---

## Layer 1 - Knowledge

已经验证并长期有效的知识。

来源只能是：

Research → Review → Approval。

---

## Layer 2 - Research

所有研究课题。

每个课题必须包含：

- Problem
- Hypothesis
- Evidence
- Experiment
- Conclusion
- Confidence

---

## Layer 3 - Experiments

所有实验。

必须能够复现。

---

## Layer 4 - Failures

记录失败案例。

禁止删除。

必须说明：

- 为什么失败
- 如何发现
- 如何避免再次发生

---

## Layer 5 - Playbooks

经过验证的投资行动方案。

Decision Engine 只能引用 Playbook，不直接引用未经验证的 Research。

---

# Knowledge State Machine

Idea

↓

Hypothesis

↓

Experiment

↓

Validated

↓

Knowledge

↓

Playbook

↓

Decision Engine

---

# Governance Rules

1. 任何长期投资结论不得直接进入代码。
2. 任何长期投资结论必须先形成 Research。
3. Research 必须有 Evidence。
4. Evidence 必须可追溯。
5. Playbook 必须引用 Knowledge。
6. Decision Engine 必须引用 Playbook。
7. 每条 Knowledge 必须记录 Confidence（0~100）。

---

# AI Onboarding

任何 AI Agent 或开发者加入项目时，必须按顺序阅读：

1. Constitution
2. ADR
3. Athena Brain
4. Research
5. Playbooks

完成后方可参与开发。

---

# Success Metric

Athena 的长期成功标准不是代码规模，而是：

- Knowledge 数量与质量持续增长；
- 决策准确率持续提升；
- 新成员能够快速恢复完整上下文；
- 任何关键决策均可追溯到对应的 Research 与 Evidence。
