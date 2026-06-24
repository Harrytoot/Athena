---
id: BRAIN-002
title: Knowledge Index Specification
status: Approved
version: 1.0.0
owner: Chief Architect
reviewer: Founder
created: 2026-06-24
---

# BRAIN-002 Knowledge Index Specification

## Purpose

Athena Brain 中的每一份知识资产都必须可检索、可关联、可追溯。

本规范定义统一 Metadata、Brain Index 和 Context Builder 的输入格式。

---

# 1. Unified Metadata

所有知识文档（ADR、RFC、Research、Evidence、Playbook、Decision、Failure）必须包含统一 YAML Header。

标准字段：

```yaml
id:
title:
type:
status:
version:
owner:
reviewer:
created:
updated:
confidence:
tags:
references:
related:
```

说明：

* `id`：唯一标识。
* `type`：Research、ADR、Playbook 等。
* `confidence`：0~100，仅适用于研究类文档。
* `references`：引用的文档。
* `related`：关联但非直接引用的文档。

---

# 2. Brain Index

新增：

brain/index.json

由程序自动生成。

禁止人工修改。

每次 CI 自动更新。

包含：

* 文档列表
* Metadata
* 标签
* 引用关系
* 更新时间

---

# 3. Knowledge Graph

Brain Index 必须支持：

Research

↓

Evidence

↓

Knowledge

↓

Playbook

↓

Decision

↓

Rule

↓

Code

形成完整可追溯链路。

---

# 4. Context Builder

新增 Context Builder。

输入：

* 当前任务
* Brain Index
* Sprint Status

输出：

Context.md

作为 AI 的上下文恢复文件。

---

# 5. CI Integration

GitHub Actions 新增：

Knowledge Index Check。

检查：

* Metadata 是否完整
* 引用是否存在
* ID 是否唯一
* YAML 是否合法

失败则禁止合并。

---

# Success Criteria

Athena Brain 中任何知识资产均可：

* 快速检索；
* 自动恢复上下文；
* 自动生成知识图谱；
* 支撑未来多 AI 协同工作。
