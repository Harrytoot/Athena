---
id: CONST-001
title: Definition of Done
status: Approved
version: 1.0.0
owner: Chief Architect
reviewer: Founder
---

# Definition of Done

## Purpose

统一 Athena 项目的交付质量标准。

任何 Epic、Feature、Story、Task 必须满足以下条件，方可标记为 Done。

---

# Functional

- 功能符合 PRD
- 所有 Acceptance Criteria 完成
- 无阻塞 Bug
- 无 P0/P1 缺陷

---

# Architecture

- 符合 DDD
- 符合 Clean Architecture
- 符合 Plugin Architecture
- 无跨领域依赖
- 无循环依赖

---

# Documentation

必须同步更新：

- PRD
- API
- Database
- TASK
- SPRINT_STATUS
- CHANGELOG（如适用）

文档与代码必须保持一致。

---

# Testing

至少完成：

- API Test
- Service Test

新增功能不得破坏已有测试。

---

# Review Gate

必须全部通过：

- Code Review
- Architecture Review
- Product Acceptance

缺一不可。

---

# Deployment

必须满足：

- Docker Compose 可启动
- 服务可正常访问
- 无启动异常

---

# Logging

新增模块必须输出：

- Error Log
- Warning Log（必要时）

禁止静默失败。

---

# Future Compatibility

新增功能不得破坏：

- Provider Interface
- Plugin Interface
- Domain Interface

不得为了当前需求牺牲未来扩展性。

---

# Completion

只有满足以上所有条件，Epic 才允许：Status = Done
