---
id: GOV-002
title: Athena Role and Authority Governance
classification: S
status: Approved
version: 1.0.0
owner: Chief Architect
reviewer: Founder
---

# Athena Role and Authority Governance

## Purpose

建立 Athena 项目统一的角色职责、权限边界、审批流程与 RACI 治理机制，确保项目长期演进过程中职责清晰、权限明确、知识可追溯。

---

# Organizational Roles

## Founder

职责：

- 制定项目使命（Mission）
- 制定产品路线图（Roadmap）
- 定义风险偏好
- 审批战略级决策（Level S）

权限：

- 最终批准 Constitution、Mission、重大架构变更。

---

## Chief Architect

职责：

- Constitution
- Architecture
- Knowledge Governance
- Research Governance
- Investment Methodology
- Architecture Review

权限：

- 审批所有 Level A 文档。
- 审核 Level B 研究成果。

---

## Engineering Lead

职责：

- Backend
- Frontend
- API
- Database
- Provider
- Plugin
- CI/CD
- Deployment

权限：

- 维护工程资产（Level C）。
- 不得直接修改 Level S 文档。

---

## Future AI Roles

预留：

- Research Agent
- Review Agent
- Risk Officer
- Portfolio Manager
- Context Builder

所有新增 Agent 必须定义职责后方可加入。

---

# RACI Matrix

| Asset | Founder | Chief Architect | Engineering Lead |
|--------|----------|----------------|------------------|
| Constitution | A | A | R(Implement only) |
| ADR | C | A | R |
| RFC | C | A | R |
| Research | C | A | R |
| Code | I | C | A |
| Database | I | A | R |
| API | I | A | R |
| Deployment | I | A | R |

说明：

- R = Responsible
- A = Accountable
- C = Consulted
- I = Informed

---

# Approval Flow

Research

↓

Review

↓

Chief Architect

↓

Founder（如涉及 Level S）

↓

Playbook

↓

Decision

↓

Implementation

---

# Release Governance

Feature

↓

Review

↓

Architecture Review

↓

Founder Acceptance

↓

Release Tag

↓

Knowledge Update

---

# Naming Convention

统一命名：

ADR-xxx

RFC-xxx

RESEARCH-xxx

PLAYBOOK-xxx

EVIDENCE-xxx

DECISION-xxx

FAILURE-xxx

RULE-xxx

TASK-xxxx

EPIC-xxx

---

# Git Commit Convention

推荐：

feat(module):

fix(module):

refactor(module):

research(topic):

docs(section):

governance(area):

---

# Success Criteria

任何角色都拥有：

- 明确职责
- 明确权限
- 明确审批边界
- 明确知识责任

Athena 的组织治理可持续演进，不依赖个人记忆或单一 AI。
