# Athena Architecture Repository v1.0

## Status

Ratified (2026-06-24)

## Purpose

本文档是 Athena 项目的**可交付架构资产总目录**。不替代任何具体文档，而是建立可导航的索引。

---

## 1. Project Charter（项目章程）

| 文档 | 路径 |
|------|------|
| Vision | [project_charter/Vision.md](project_charter/Vision.md) |
| Mission | [project_charter/Mission.md](project_charter/Mission.md) |
| Constitution v2.1.0 (14 Articles) | [project_charter/Constitution.md](project_charter/Constitution.md) |

---

## 2. Master Specification（最高规格说明书）

| 文档 | 路径 | 章节 |
|------|------|------|
| AMS-001 | [ams/AMS-001-master-specification.md](ams/AMS-001-master-specification.md) | 10 章 |

---

## 3. Investment Ontology（投资本体）

| 文档 | 路径 | 概念数 |
|------|------|--------|
| ONT-001 | [ontology/ONT-001-investment-ontology.md](ontology/ONT-001-investment-ontology.md) | 10 概念 + 层级树 |

---

## 4. Architecture Decision Records（架构决策）

| ID | 决策 | 日期 |
|----|------|------|
| ADR-000 | 项目冻结: 名称、使命、13原则、3阶段路线 | 2026-06-24 |
| ADR-001 | 技术栈冻结: FastAPI + Next.js + PostgreSQL | 2026-06-24 |
| ADR-002 | 开发原则: User Value First, Vertical Slice | 2026-06-24 |
| ADR-003 | 10 条核心原则: Doc First, Event Bus, Explainable AI | 2026-06-24 |
| ADR-004 | Evidence-Driven AI: 证据图谱, 预测概率, 置信度, 不知为上 | 2026-06-24 |
| ADR-005 | 企业 R&D: 6 角色, TDD, 架构治理, DDD 目录 | 2026-06-24 |
| ADR-006 | 8 项架构修正: 无万能AI, DDD, Event Sourcing, CQRS, Plugin, Capability | 2026-06-24 |
| ADR-007 | Feature Store + Investment DSL | 2026-06-24 |

---

## 5. Request for Comments（设计提案）

| ID | 主题 | 状态 |
|----|------|------|
| RFC-001 | Sprint 1 Foundation | Approved |
| RFC-002 | 12-Repository Architecture | Approved |

---

## 6. Architecture Evolution Strategy

| ID | 主题 | 章节 |
|----|------|------|
| AES-001 | 四层架构 + 五大中心 + 3 阶段演进 | Data/Domain/AI/App |
| AES-002 | AI 架构: MCP, Capability Registry, Knowledge Graph, Simulation, Prompt, DSL | 6 模块 |

---

## 7. Product Architecture

| 文档 | 路径 |
|------|------|
| 5 产品架构 | [architecture/system/product-architecture.md](architecture/system/product-architecture.md) |

| Product | 定位 | Sprint 1 范围 |
|---------|------|--------------|
| A. Athena Core | 核心引擎 | Domain 骨架 |
| B. Athena Research | 研究平台 | — |
| C. Athena Studio | 策略开发 | — |
| D. Athena Terminal | 投资终端 | Dashboard + Market + Watchlist + Stock + Portfolio |
| E. Athena Brain | AI Agent | — |

---

## 8. DDD Domain Model

| Domain | 文件 | Sprint 1 实体 | 状态 |
|--------|------|-------------|------|
| **Market** | `providers/market/` | MarketOverview, MarketRegime, Indices, HotItem | 🟢 |
| **Watchlist** | `domain/repositories/` | Watchlist, WatchlistItem (Aggregate Root + Entity) | 🟢 |
| **Stock** | `providers/stock/` | StockDetail, TechnicalIndicators, MoneyFlow, AiAnalysis | 🟢 |
| **Portfolio** | TBD | 待 Epic-005 | ⚪ |
| **Recommendation** | TBD | 待 Epic-006 | ⚪ |
| **User** | `models/user.py` | User (Alpha 单用户) | 🟡 |

**Domain 目录结构（ADR-006 标准化）:**

```
domains/
├── market/
│   ├── entity/
│   ├── value_object/
│   ├── aggregate/
│   ├── repository/
│   ├── service/
│   ├── event/
│   └── policy/
├── portfolio/
├── research/
├── strategy/
├── learning/
└── shared/
    ├── kernel/
    └── events/
```

---

## 9. Database Baseline

| 文档 | 路径 | 表数 |
|------|------|------|
| DB-001 | [database/DB-001-sprint-1-baseline.md](database/DB-001-sprint-1-baseline.md) | 7 表 |

**已实现:**

| 表 | 状态 | 模型文件 |
|----|------|---------|
| users | 🟢 | `models/user.py` |
| watchlists | 🟢 | `models/watchlist.py` |
| watchlist_items | 🟢 | `models/watchlist.py` |
| portfolios | ⚪ | 待 Epic-005 |
| positions | ⚪ | 待 Epic-005 |
| market_snapshots | ⚪ | Reserved |
| recommendations | ⚪ | 待 Epic-006 |

---

## 10. API Contract

| 文档 | 路径 | 端点数 |
|------|------|--------|
| API-001 | [api/API-001-sprint-1-baseline.md](api/API-001-sprint-1-baseline.md) | 10 |

**已实现：**

| 端点 | 状态 | 路由文件 |
|------|------|---------|
| GET /api/v1/market/overview | 🟢 | `api/v1/market.py` |
| GET /api/v1/dashboard | 🟢 | `api/v1/dashboard.py` |
| GET /api/v1/stocks/{symbol} | 🟢 | `api/v1/stock.py` |
| GET/POST/PUT/DELETE /api/v1/watchlists | 🟢 | `api/v1/watchlist.py` |
| POST/DELETE /api/v1/watchlists/{id}/items | 🟢 | `api/v1/watchlist.py` |
| GET /api/v1/watchlists/stock/search | 🟢 | `api/v1/watchlist.py` |
| POST /api/v1/auth/login | ⚪ | 待 Epic-001 |
| GET /api/v1/portfolio | ⚪ | 待 Epic-005 |
| GET /api/v1/recommendations | ⚪ | 待 Epic-006 |

---

## 11. Provider Architecture

| Provider | 接口文件 | Mock 实现 | 状态 |
|----------|---------|----------|------|
| MarketProvider | `providers/market/base.py` | `mock_provider.py` | 🟢 |
| StockSearchProvider | `providers/stock/base.py` | `mock_provider.py` | 🟢 |
| StockDetailProvider | `providers/stock/detail_base.py` | `mock_detail_provider.py` | 🟢 |
| LLMProvider | — | ⚪ | Sprint 2 |
| BrokerProvider | — | ⚪ | Sprint 2 |

---

## 12. Agent Protocol（设计冻结）

| 条目 | 规范 | 实现 |
|------|------|------|
| Agent 通信 | Event Bus only | Sprint 2 |
| Agent 输出 | Confidence + Evidence + Reason | Sprint 2 |
| Agent 注册 | Capability Registry | Sprint 2 |
| Meta Agent | 动态权重调度 | Sprint 2 |

14 Agent 定义见 [AES-001](aes/AES-001-four-layer-architecture.md)。

---

## 13. DSL Specification（设计冻结）

| 条目 | 规范 | 实现 |
|------|------|------|
| 语法 | WHEN/AND/THEN/ALLOCATE/STOP_LOSS | Sprint 2 |
| 编译器 | DSL → Feature Calls → Execution | Sprint 2 |
| Feature 引用 | `Feature("name")` | Sprint 2 |

详见 [ADR-007](adr/ADR-007-feature-store-dsl.md)。

---

## 14. UI Design System

| 条目 | 状态 |
|------|------|
| 框架 | Tailwind CSS + shadcn/ui ✅ |
| 布局 | Sidebar + Main Content ✅ |
| 颜色系统 | 红涨绿跌 (中国习惯) ✅ |
| 组件库 | 15+ 组件已创建 ✅ |
| 设计规范文档 | ⚪ 待创建 |

---

## 15. Development Standards

| 条目 | 状态 |
|------|------|
| 语言 | Python 3.12 (Backend) / TypeScript (Frontend) ✅ |
| 代码风格 | Ruff (Python) / ESLint (TS) ⚪ |
| 提交规范 | Conventional Commits ✅ |
| 分支策略 | Trunk-based (master) ✅ |
| TDD | Test before code (ADR-005) ⚪ |

---

## 16. Testing Strategy

| 层级 | 框架 | 状态 |
|------|------|------|
| Unit Test | pytest + pytest-asyncio | ⚪ |
| Integration Test | httpx (FastAPI TestClient) | ⚪ |
| Contract Test | OpenAPI schema validation | ⚪ |
| E2E Test | Playwright / TBD | ⚪ Sprint 2 |

---

## 17. OpenCode Task Tree

| Epic | 任务 ID | 状态 |
|------|---------|------|
| Epic-002 Market Center | TASK-0002 | 🟢 |
| Epic-003 Watchlist | TASK-0003, TASK-0007 | 🟢 |
| Epic-004 Stock Detail | — | 🟢 |
| Epic-005 Portfolio | TASK-0005 | ⚪ |
| Epic-006 Recommendation | TASK-0006 | ⚪ |
| Epic-001 Authentication | TASK-0001 | ⚪ |

---

## 18. Future Architecture Assets（Gap Analysis）

| 待建资产 | 计划 |
|----------|------|
| C4 Architecture Diagrams (Context, Container, Component, Code) | Sprint 2 |
| Agent Protocol v1.0 (detailed) | Sprint 2 |
| DSL Specification v1.0 (full grammar) | Sprint 2 |
| UI Design System v1.0 (Figma/Storybook) | Sprint 2 |
| Feature Store Schema | Sprint 2 |
| Knowledge Graph Schema (Neo4j/Cypher) | Sprint 3 |
| Event Catalog (all domain events) | Sprint 2 |
| Capability Catalog | Sprint 2 |
| Prompt Library v1.0 | Sprint 2 |
| Test Suite (unit + integration + contract) | Sprint 1 completion |

---

**Version:** 1.0.0  
**Maintained by:** Documentation Engineer (OpenCode)
