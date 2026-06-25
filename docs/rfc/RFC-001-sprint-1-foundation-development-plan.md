---
id: RFC-001
title: Sprint 1 Foundation Development Plan
status: Approved
version: 1.0.0
owner: Chief Architect
reviewer: Founder
created: 2026-06-24
depends:
  - ADR-001
related:
  - TASK-0001
  - TASK-0002
  - TASK-0003
---

# RFC-001 Sprint 1 Foundation Development Plan

## Status

Approved

---

# Review

Commit:

773efd9

Review Result:

PASS

Architecture Score: ★★★★★

Documentation Score: ★★★★★

Engineering Quality: ★★★★★

OpenCode 已完成 Foundation 初始化，允许进入 Sprint 1 Feature 开发阶段。

---

# Sprint Goal

Sprint 1 的目标不是实现 AI，也不是实现自动交易。

唯一目标：

建立可以持续演进的投资操作系统基础平台。

Definition：

系统能够部署运行，并完成一条完整的业务闭环：

Login → Dashboard → Market → Watchlist → Portfolio → Recommendation

---

# Development Order (CTO Mandate)

见 [ADR-002 Development Principles](../adr/ADR-002-development-principles.md)。

| Priority | Epic | Rationale |
|----------|------|-----------|
| P0 | Epic-002 Market Center | 市场分析是核心用户价值 |
| P0 | Epic-003 Watchlist | 自选股是个人投资入口 |
| P0 | Epic-004 Stock Detail | 个股是决策基本单元 |
| P0 | Epic-005 Portfolio | 持仓是资产管理的核心 |
| P1 | Epic-006 Recommendation | 基于持仓和市场的规则引擎 |
| P1 | Epic-001 Authentication | 单用户 Alpha，登录非当前价值 |

---

# Sprint Scope

本阶段包含六个 Epic。

## Epic-001 Authentication

目标：

完成基础认证能力。

功能：

- Login
- Logout
- JWT
- Refresh Token（预留）
- User Profile

暂不实现：

- RBAC
- OAuth
- 多用户权限

---

## Epic-002 Market Center

第一阶段采用 Mock Provider。

展示：

- 上证指数
- 深证指数
- 创业板指数
- 成交额
- 涨跌家数
- 北向资金
- 热点行业
- 市场温度
- AI 摘要（Mock）

Provider 必须通过接口提供。

禁止页面写死数据。

---

## Epic-003 Watchlist

功能：

- 创建自选组
- 删除自选组
- 添加股票
- 删除股票
- 标签
- 排序
- 备注

领域：

Watchlist

禁止直接操作数据库。

必须经过 Domain。

---

## Epic-004 Stock Detail

支持：

股票详情页面。

包含：

- K线（预留）
- 技术指标（Mock）
- 基本面（Mock）
- 资金面（Mock）
- AI 分析（Mock）

所有数据统一来自 Provider。

---

## Epic-005 Portfolio

第一阶段：

采用手工录入。

功能：

- 总资产
- 持仓
- 成本
- 浮盈亏
- 仓位
- 现金

后续版本再接券商接口。

---

## Epic-006 Recommendation

第一阶段：

采用 Rule Engine。

禁止调用 LLM。

Recommendation 包含：

- Action
- Confidence
- Reason
- Risk
- Position Suggestion
- Expire Time

---

# Domain Model

冻结以下领域：

- User
- Market
- Watchlist
- Stock
- Portfolio
- Position
- Indicator
- Feature
- Recommendation
- Strategy
- Backtest
- Notification

不得新增 Utils、Manager、Business 等非领域目录。

---

# Database Baseline

建立以下核心表：

- users
- watchlists
- watchlist_items
- portfolios
- positions
- market_snapshots
- recommendations

数据库命名统一 snake_case。

---

# API Baseline

建立：

- POST /api/v1/auth/login
- GET /api/v1/dashboard
- GET /api/v1/market/overview
- GET /api/v1/watchlists
- POST /api/v1/watchlists
- DELETE /api/v1/watchlists/{id}
- GET /api/v1/portfolio
- GET /api/v1/stocks/{symbol}
- GET /api/v1/recommendations

Swagger 必须自动生成。

---

# UI Navigation

冻结左侧菜单：

- Dashboard
- Market
- Watchlist
- Portfolio
- Research
- Strategy
- Backtest
- AI Center
- Settings

未经 ADR 不允许增加一级菜单。

---

# Architecture Rules

必须遵守：

- DDD
- Clean Architecture
- Plugin Architecture
- Documentation First

禁止：

- Controller 编写业务逻辑
- 页面写死 Mock 数据
- Service 成为业务垃圾桶
- Repository 跨领域访问

---

# Daily Report

每个开发日提交：

```text
Today
Completed
Changed
Risk

Tomorrow
Plan
```

保存：

docs/project-memory/DAILY_REPORT.md

---

# Deliverables

Sprint 1 完成后应达到：

- 登录可用
- Dashboard 可展示
- 市场概览可展示
- 自选股可维护
- 持仓可维护
- Recommendation 页面可展示
- Docker Compose 一键启动
- README 完整
- OpenAPI 自动生成
- 基础测试通过

---

# Acceptance Criteria

- 所有页面可以访问。
- Docker Compose 可以一键启动。
- 前后端联调通过。
- API 文档完整。
- 不违反 DDD 分层。
- 所有 Mock 数据来自 Provider。
- 能部署到服务器。
