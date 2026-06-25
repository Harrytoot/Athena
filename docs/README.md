# Athena Documentation

> 文档总入口。所有正式交付文档的导航起点。

## 快速导航

| 你想做什么 | 从这里开始 |
|-----------|-----------|
| 了解项目是什么 | [项目章程](project-charter/) |
| 理解架构决策 | [ADR 目录](adr/) |
| 找到某个规范文档 | [架构仓库索引](ARCHITECTURE_REPOSITORY.md) |
| 写一个新的设计提案 | [RFC 目录](rfc/) + [写作指南](GUIDE-001-architecture-decision-rationale.md) |
| 查看当前 Sprint 进度 | [Sprint 状态](roadmap/SPRINT_STATUS.md) |
| 查看领域术语定义 | [术语表](glossary/GLOSSARY.md) |
| 新人入职学习 | [Brain 引导](brain/README.md) |

---

## 文档目录结构

### 1. 项目基础

| 目录 | 说明 | 文档数 |
|------|------|--------|
| [project-charter/](project-charter/) | 项目章程：Vision, Mission, Constitution | 3 |
| [constitution/](constitution/) | 领域宪法：投资宪法, 决策OS, Definition of Done | 3 |
| [project/](project/) | 开发原则 | 1 |
| [governance/](governance/) | 治理规范：资产分类, 角色权限, 组织手册 | 3 |

### 2. 架构设计

| 目录 | 说明 | 文档数 |
|------|------|--------|
| [adr/](adr/) | Architecture Decision Records — 架构决策记录 | 11 |
| [rfc/](rfc/) | Request for Comments — 设计提案 | 3 |
| [aes/](aes/) | Architecture Evolution Strategy — 演进策略 | 2 |
| [ams/](ams/) | Athena Master Specification — 最高规格说明书 | 1 |
| [architecture/](architecture/) | 系统架构原则与产品架构 | 2 |

### 3. 领域模型

| 目录 | 说明 | 文档数 |
|------|------|--------|
| [investment/](investment/) | 投资框架：信号概率, 投资假设, 市场状态引擎 | 3 |
| [ontology/](ontology/) | 投资本体论 | 1 |
| [product/](product/) | 产品蓝图 | 1 |
| [algorithms/](algorithms/) | 算法规范：技术面, 基本面, 情绪分析, 组合优化 | 1+4 |

### 4. 工程规范

| 目录 | 说明 | 文档数 |
|------|------|--------|
| [api/](api/) | API 契约 | 1 |
| [database/](database/) | 数据库设计 | 1 |
| [data/](data/) | 数据/特征合约 | 1 |
| [prd/](prd/) | 产品需求文档 | 1 |
| [engineering/](engineering/) | 工程标准：编码规范, Git 流程, 测试策略, 错误码, 配置规范 | 1+5 |

### 5. 规划与跟踪

| 目录 | 说明 | 文档数 |
|------|------|--------|
| [roadmap/](roadmap/) | 能力路线图 + Sprint 状态 | 2 |
| [sprint/](sprint/) | Sprint 定义 | 1 |
| [tasks/](tasks/) | Epic/Task 任务分解 | 7 |

### 6. 知识操作系统

| 目录 | 说明 | 文档数 |
|------|------|--------|
| [brain/](brain/) | Athena Brain — 9 层知识结构 | 2+8 |

### 7. 运行态记录

| 目录 | 说明 | 文档数 |
|------|------|--------|
| [project-memory/](project-memory/) | 日报, 审查策略, 审查记录, 交接文档 | 4 |
| [architecture-state/](architecture-state/) | 当前架构里程碑状态 | 1 |

### 8. 参考

| 目录 | 说明 | 文档数 |
|------|------|--------|
| [glossary/](glossary/) | 领域术语表 | 1 |
| [GUIDE-001](GUIDE-001-architecture-decision-rationale.md) | 架构决策理由写作指南 | 1 |
| [ARCHITECTURE_REPOSITORY.md](ARCHITECTURE_REPOSITORY.md) | 可交付架构资产总目录 | 1 |

---

## 文档类型与编号规则

所有正式文档遵循 `{TYPE}-{NNN}-{kebab-case-name}.md` 格式：

| 前缀 | 类型 | 存放目录 | 需要 RFC? |
|------|------|---------|----------|
| `ADR-` | Architecture Decision Record | `adr/` | 是 |
| `RFC-` | Request for Comments | `rfc/` | 不适用 |
| `AES-` | Architecture Evolution Strategy | `aes/` | 是 |
| `AMS-` | Athena Master Specification | `ams/` | 是 |
| `PRD-` | Product Requirements Document | `prd/` | 否 |
| `API-` | API Specification | `api/` | 是 |
| `DB-` | Database Design | `database/` | 是 |
| `TASK-` | Task/Epic Breakdown | `tasks/` | 否 |
| `BRAIN-` | Brain Knowledge Doc | `brain/` | 否 |
| `CONSTITUTION-` | Domain Constitution | `constitution/` | 是 |
| `GOV-` | Governance Document | `governance/` | 是 |
| `INV-ARCH-` | Investment Architecture | `investment/` | 是 |
| `ONT-` | Ontology Definition | `ontology/` | 是 |
| `PRODUCT-` | Product Blueprint | `product/` | 是 |
| `DATA-` | Data/Feature Contract | `data/` | 是 |
| `ALG-` | Algorithm Specification | `algorithms/` | 否 |
| `ROADMAP-` | Roadmap Document | `roadmap/` | 否 |
| `SPRINT-` | Sprint Definition | `sprint/` | 否 |
| `REVIEW-` | Review Record | `project-memory/reviews/` | 否 |

---

## 维护规则

1. 新文档创建后，如属于架构/数据库/API/领域模型/技术栈变更，更新 `ARCHITECTURE_REPOSITORY.md`
2. 目录结构变更需更新本文档的目录表
3. 交叉引用统一使用相对于 `docs/` 的路径，如 `[ADR-001](adr/ADR-001-sprint-1-tech-stack-freeze.md)`
4. 所有目录名使用 kebab-case

---
*Last updated: 2026-06-25*
