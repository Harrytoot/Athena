---
id: TASK-0002
title: Epic-002 Market Center
epic: Market Center
status: In Progress
priority: P0
dependencies:
  - ADR-001
  - ADR-002
  - RFC-001
---

# TASK-0002 Epic-002 Market Center

## Goal

建立第一个用户价值闭环：Dashboard + Market Overview。Mock First，通过 MarketProvider 隔离数据源。

## Domain

Market

## Provider Architecture

```
src/backend/app/providers/market/
├── __init__.py
├── base.py              # MarketProvider 接口
├── mock_provider.py     # MockMarketProvider 实现
└── (future: akshare_provider.py)
```

业务代码只依赖 `MarketProvider` 接口，更换数据源零业务改动。

## Tasks

### Domain Layer

- [ ] 创建 MarketProvider 抽象接口 `providers/market/base.py`
- [ ] 创建 Market 领域实体 (domain/entities/market.py)
- [ ] 在 domain/entities/market.py: MarketRegime enum (Bull/Bear/Range/Volatile)
- [ ] 在 domain/entities/market.py: MarketOverview value object
- [ ] 在 domain/entities/market.py: HotSector / HotConcept value object
- [ ] 在 domain/entities/market.py: AiMarketSummary value object

### Infrastructure Layer

- [ ] 创建 MockMarketProvider 实现 `providers/market/mock_provider.py`
- [ ] 创建 MarketDataRepository 接口
- [ ] 创建 SQLAlchemy market_snapshots 表
- [ ] 数据库迁移

### Application Layer

- [ ] 创建 MarketService (application/services/market_service.py)，注入 MarketProvider
- [ ] GET /api/v1/market/overview — 返回完整市场概况
- [ ] GET /api/v1/dashboard — 返回仪表盘汇总数据

### API Response Shape

#### GET /api/v1/market/overview

```json
{
  "marketRegime": "Bull",
  "temperature": 78,
  "indices": {
    "shanghai": { "code": "000001", "name": "上证指数", "price": 3150.42, "change_pct": 0.85 },
    "shenzhen": { "code": "399001", "name": "深证成指", "price": 10420.35, "change_pct": 1.23 },
    "chi_next": { "code": "399006", "name": "创业板指", "price": 2150.18, "change_pct": 1.56 }
  },
  "turnover": 15600,
  "upCount": 3812,
  "downCount": 1286,
  "northbound": 58.7,
  "hotIndustries": [
    {"name": "半导体", "change_pct": 4.2},
    {"name": "AI", "change_pct": 3.8},
    {"name": "新能源", "change_pct": 3.1}
  ],
  "hotConcepts": [
    {"name": "ChatGPT", "change_pct": 5.1},
    {"name": "光刻机", "change_pct": 4.7},
    {"name": "存储芯片", "change_pct": 4.3}
  ],
  "summary": "市场整体震荡上行，成交量温和放大，北向资金持续流入。半导体与AI板块领涨，市场情绪偏暖。",
  "updatedAt": "2026-06-24T09:45:00Z"
}
```

#### GET /api/v1/dashboard

```json
{
  "totalAssets": "decimal",
  "totalReturnPct": "decimal",
  "watchlistCount": "int",
  "positionCount": "int",
  "marketSummary": {
    "marketRegime": "Bull",
    "temperature": 78,
    "shanghaiChangePct": 0.85,
    "shenzhenChangePct": 1.23,
    "turnover": 15600,
    "upCount": 3812,
    "downCount": 1286
  },
  "latestRecommendations": []
}
```

### Frontend — Dashboard Page (首屏)

- [ ] MarketRegimeBadge — 市场状态徽章 (Bull/Bear/Range/Volatile)
- [ ] MarketTemperatureGauge — 市场温度计 (0-100)
- [ ] IndexCard x3 — 三大指数 (价格/涨跌幅)
- [ ] MarketStatsRow — 成交额 / 涨跌家数 / 北向资金
- [ ] HotSectorList — 热点行业 Top10
- [ ] HotConceptList — 热点概念 Top10
- [ ] AiMarketSummaryCard — AI 市场摘要 (Mock)
- [ ] UpdateTimeLabel — 数据更新时间

### Frontend — Market 页面

- [ ] 复用 Dashboard 组件，展示更多细节
- [ ] PortfolioSummaryCard（持仓概览，后续 Epic 填充）

### Architecture Constraints

- ❌ 禁止页面写 `const data = {...}` 硬编码 Mock 数据
- ❌ 禁止 Controller 编写业务逻辑
- ✅ 所有数据来自 `MarketService → MarketProvider`
- ✅ 未来替换为 AKShare 只需新增 `AKShareMarketProvider`，业务零修改

### Tests

- [ ] MockMarketProvider 单元测试
- [ ] MarketService 单元测试（注入 MockMarketProvider）
- [ ] GET /api/v1/market/overview 集成测试
- [ ] GET /api/v1/dashboard 集成测试

## Acceptance Criteria

- GET /api/v1/market/overview 返回符合 shape 的完整 Mock 数据
- GET /api/v1/dashboard 返回仪表盘数据
- Dashboard 页面展示所有要求的组件（MarketRegime / Temperature / 三大指数 / 成交额 / 涨跌家数 / 北向 / 热点行业 / AI 摘要）
- 前端所有数据来自 API（不为空即通过）
- MarketProvider 接口定义清晰，MockMarketProvider 可替换
- 单元测试 + 集成测试通过

## References

- [RFC-001](../rfc/RFC-001-sprint-1-foundation-development-plan.md)
- [ADR-002 Development Principles](../adr/ADR-002-development-principles.md)
- [API-001](../api/API-001-sprint-1-baseline.md)
- [DB-001](../database/DB-001-sprint-1-baseline.md)
