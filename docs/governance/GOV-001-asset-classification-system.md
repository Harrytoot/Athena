---
id: GOV-001
title: Athena Asset Classification System
classification: S
status: Approved
version: 1.0.0
owner: Chief Architect
reviewer: Founder
---

# Athena Asset Classification System

## Purpose

建立 Athena 全项目统一的工程资产分级制度，规范所有文档、知识、代码及研究资产的生命周期、修改权限和治理流程。

---

# Level S — Strategic Asset

定义：

Athena 的长期核心资产。

包括：

- Constitution
- Brain
- Memory
- Ontology
- Philosophy
- Governance

生命周期：

Permanent

修改要求：

- ADR
- Chief Architect Approval
- Founder Approval

禁止直接修改。

---

# Level A — Architecture Asset

包括：

- ADR
- RFC
- Database
- API Standard
- Deployment
- DDD
- Engineering Rules

生命周期：

Long-term

修改要求：

Architecture Review。

---

# Level B — Business Asset

包括：

- PRD
- Research
- Evidence
- Playbook
- Decision
- Factor
- Risk
- Portfolio

生命周期：

Iterative

修改要求：

Business Review。

---

# Level C — Engineering Asset

包括：

- API
- Provider
- Plugin
- SQL
- Docker
- Scripts
- CI/CD

生命周期：

Version-based

可由 Engineering Lead 独立维护。

---

# Level D — Working Asset

包括：

- Sprint
- Checklist
- Meeting Notes
- Temporary Docs

生命周期：

Sprint

结束后归档。

---

# Level X — Experimental Asset

包括：

- Prototype
- Experiment
- Prompt
- POC
- Backtest Trial

允许失败。

允许废弃。

必须记录实验结果。

---

# Mandatory Metadata

所有文档必须增加：

```yaml
classification:
```

可选值：

S
A
B
C
D
X

---

# Review Matrix

| Level | OpenCode | Chief Architect | Founder |
|--------|----------|----------------|----------|
| S | Read Only | Approve | Approve |
| A | Proposal | Approve | Optional |
| B | Implement | Review | Optional |
| C | Maintain | Optional | No |
| D | Maintain | No | No |
| X | Experiment | Review Result | No |

---

# Standard Header

所有由 Chief Architect 发布的正式工程资产必须包含：

ARCHITECT MODE

Document Level

Git

OpenCode

Action

Approval

Blocking

Target File

作为统一治理入口。

---

# Success Criteria

任何项目资产都能够明确：

- 重要等级
- 生命周期
- 修改权限
- 审批流程
- Git 管理策略
- Review 策略
