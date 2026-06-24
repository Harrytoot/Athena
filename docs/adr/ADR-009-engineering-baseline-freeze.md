---
id: ADR-009
title: Engineering Baseline Freeze
status: Approved
version: 1.0.0
owner: Chief Architect
reviewer: Founder
created: 2026-06-24
depends:
  - ADR-001
  - ADR-002
---

# ADR-009 Engineering Baseline Freeze

## Status

Approved

---

# Context

Sprint 1 已完成工程基础设施建设。

项目已经具备：

- Git Repository
- DDD Architecture
- Clean Architecture
- Plugin Architecture
- Provider Pattern
- Docker Compose
- CI Pipeline
- Review Gate
- Documentation System
- Architecture Governance

工程基线达到可持续演进要求。

---

# Decision

即日起冻结工程基线。

以下内容未经新的 ADR 不得修改：

## Technology Stack

保持 ADR-001。

---

## Directory Structure

保持当前目录结构。

不得随意新增平级目录。

---

## Layered Architecture

保持：

```
Domain
  ↓
Application
  ↓
Infrastructure
  ↓
Presentation
```

依赖方向不得改变。

---

## Provider Pattern

所有外部系统必须通过 Provider 接入。

不得绕过 Provider。

---

## Documentation

Documentation First 持续生效。

任何重大修改必须同步更新文档。

---

## Engineering Rules

继续执行：

- Review Gate
- Definition of Done
- Review Policy
- Sprint Status

---

# Future Changes

后续任何涉及：

- 架构
- 数据库
- API
- Provider
- Plugin

的重大调整，必须新增 ADR。

不得直接修改实现。

---

# Acceptance

Engineering Baseline Freeze 生效。

Sprint 2 前不再调整基础架构。
