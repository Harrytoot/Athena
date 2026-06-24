---
id: GUIDE-001
title: Architecture Decision Rationale Guide
status: Approved
version: 1.0.0
owner: Chief Architect
reviewer: Founder
created: 2026-06-24
---

# Architecture Decision Rationale Guide

## Purpose

Athena 永久记录每一个重要架构决策的设计依据（Rationale），作为项目知识资产。

---

# Every Major Decision Must Record

每一个 ADR、RFC、PRD、RESEARCH 至少包含以下章节。

## Decision

最终决策是什么。

---

## Context

背景是什么？

为什么现在需要做这个决定？

---

## Goals

希望解决什么问题？

成功标准是什么？

---

## Alternatives

至少列出两个可行方案。

例如：

方案 A

方案 B

说明为什么没有采用。

---

## Trade-offs

记录权衡。

例如：

获得：

- 更好的扩展性
- 更低耦合
- 更高性能

代价：

- 更复杂
- 学习成本增加
- 初期开发时间增加

任何重大设计必须说明 Trade-off。

---

## Risks

当前已知风险。

包括：

技术风险

业务风险

性能风险

维护风险

---

## Future Evolution

未来预计如何演进。

例如：

Mock Provider

↓

AKShare

↓

Wind

↓

Multi Provider

记录未来升级路线。

---

## Open Questions

尚未决定的问题。

例如：

是否支持多账户？

是否支持港股？

是否支持期货？

这些问题保留，不强行提前设计。

---

## References

关联：

ADR

RFC

PRD

API

Research

Review

形成完整知识图谱。

---

# Principle

记录：

为什么这样设计。

而不是：

记录 AI 是怎么想到的。

项目的长期资产是设计依据，而不是内部推理。
