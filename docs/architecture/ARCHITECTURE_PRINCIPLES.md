---
id: ARCH-001
title: Athena Architecture Principles
status: Approved
version: 1.0.0
owner: Chief Architect
---

# Athena Architecture Principles

## Core Principles

Athena 的所有设计必须遵循以下原则：

1. Documentation First
2. Domain Driven Design
3. Clean Architecture
4. Plugin First
5. Provider First
6. Human In The Loop
7. Explainable Decision
8. Testability First
9. Repository Is Source Of Truth
10. Long-term Evolution

---

## Engineering Principles

任何实现都必须：

先抽象 → 再实现

不得：先写死 → 再重构

---

## Provider Rule

所有外部数据必须经过 Provider。

禁止：Controller → 第三方接口

---

## Domain Rule

所有业务规则只能位于 Domain。

禁止：Controller / Repository / Frontend 包含业务规则。

---

## API Rule

API 仅负责：DTO / Validation / Routing

不得包含：Business Logic

---

## Frontend Rule

Frontend 仅负责：Display / Interaction / State

不得：计算投资逻辑。

---

## Investment Rule

投资逻辑全部位于：Strategy / Indicator / Feature / Recommendation

禁止散落各层。

---

## Future Rule

所有设计优先考虑未来五年的可扩展性，而不是当前开发速度。
