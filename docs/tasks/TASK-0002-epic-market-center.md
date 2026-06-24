---
id: TASK-0002
title: Epic-002 Market Center
epic: Market Center
status: Pending
priority: High
dependencies:
  - ADR-001
  - RFC-001
---

# TASK-0002 Epic-002 Market Center

## Goal

展示市场概览数据（Mock Provider 第一阶段），Provider 必须通过接口提供，禁止页面写死数据。

## Domain

Market

## Tasks

### Backend

- [ ] 创建 Market 领域实体 (domain/entities/market.py)
- [ ] 创建 MarketProvider 接口 (domain/repositories/market_provider.py)
- [ ] 创建 MockMarketProvider 实现 (infrastructure/market/mock_provider.py)
- [ ] 创建 MarketService (application/services/market_service.py)
- [ ] 创建 GET /api/v1/market/overview 接口
- [ ] 创建 GET /api/v1/dashboard 接口
- [ ] 数据库迁移：market_snapshots 表
- [ ] 单元测试

### Frontend

- [ ] 创建 Dashboard 页面（登录后首页）
- [ ] 创建 Market 页面
- [ ] 创建 IndexCard 组件（上证/深证/创业板指数展示）
- [ ] 创建 MarketOverview 组件（成交额/涨跌家数/北向资金）
- [ ] 创建 HotSector 组件（热点行业）
- [ ] 创建 MarketTemperature 组件（市场温度）
- [ ] 创建 AiSummaryCard 组件（AI 摘要 Mock）

## Mock Data Shape

```json
{
  "indices": {
    "shanghai": { "code": "000001", "name": "上证指数", "price": 3150.42, "change_pct": 0.85 },
    "shenzhen": { "code": "399001", "name": "深证成指", "price": 10420.35, "change_pct": 1.23 },
    "chi_next": { "code": "399006", "name": "创业板指", "price": 2150.18, "change_pct": 1.56 }
  },
  "turnover": 9850.42,
  "advance_count": 2450,
  "decline_count": 1680,
  "northbound_flow": 42.5,
  "hot_sectors": ["半导体", "AI", "新能源"],
  "market_temperature": 65,
  "ai_summary": "市场整体震荡上行，成交量温和放大。"
}
```

## Acceptance Criteria

- GET /api/v1/market/overview 返回 Mock 数据
- 前端页面的所有数据来自 Provider（无硬编码）
- 上证/深证/创业板指数正确展示
- Dashboard 展示核心指标摘要

## References

- [RFC-001](../rfc/RFC-001-sprint-1-foundation-development-plan.md)
