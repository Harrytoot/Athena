---
id: TASK-0004
title: Epic-004 Stock Detail
epic: Stock Detail
status: Pending
priority: High
dependencies:
  - ADR-001
  - RFC-001
  - TASK-0002
---

# TASK-0004 Epic-004 Stock Detail

## Goal

股票详情页面，包含 K线（预留）、技术指标（Mock）、基本面（Mock）、资金面（Mock）、AI 分析（Mock）。所有数据统一来自 Provider。

## Domain

Market, Stock, Indicator

## Tasks

### Backend

- [ ] 创建 Stock 实体 (domain/entities/stock.py)
- [ ] 创建 StockProvider 接口 (扩展 MarketProvider)
- [ ] 扩展 MockMarketProvider 提供个股数据
- [ ] 创建 GET /api/v1/stocks/{symbol} 接口（含技术指标、基本面、资金面）

### Frontend

- [ ] 创建 StockDetail 页面
- [ ] 创建 StockHeader 组件（股票名称/代码/价格/涨跌幅）
- [ ] 创建 TechnicalChart 组件（K线图占位）
- [ ] 创建 TechnicalIndicator 组件（技术指标 Mock）
- [ ] 创建 FundamentalInfo 组件（基本面 Mock）
- [ ] 创建 MoneyFlow 组件（资金面 Mock）
- [ ] 创建 AiAnalysisCard 组件（AI 分析 Mock Tab）

## Acceptance Criteria

- GET /api/v1/stocks/{symbol} 返回完整 Mock 数据
- 股票详情页面展示全部信息
- 所有数据来自 Provider

## References

- [RFC-001](../rfc/RFC-001-sprint-1-foundation-development-plan.md)
