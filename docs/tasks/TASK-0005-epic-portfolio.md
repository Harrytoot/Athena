---
id: TASK-0005
title: Epic-005 Portfolio
epic: Portfolio
status: Pending
priority: High
dependencies:
  - ADR-001
  - RFC-001
  - TASK-0001
---

# TASK-0005 Epic-005 Portfolio

## Goal

手工录入投资组合，管理总资产、持仓、成本、浮盈亏、仓位、现金。后续版本再接券商接口。

## Domain

Portfolio, Position

## Tasks

### Backend

- [ ] 创建 Portfolio 聚合根 (domain/aggregates/portfolio.py)
- [ ] 创建 Position 实体 (domain/entities/position.py)
- [ ] 创建 PortfolioRepository 接口
- [ ] 创建 SQLAlchemy Portfolio / Position Model
- [ ] 创建 PortfolioRepositoryImpl
- [ ] 创建 PortfolioService (application/services/portfolio_service.py)
- [ ] 创建 GET /api/v1/portfolio 获取投资组合
- [ ] 创建 POST /api/v1/portfolio 创建投资组合
- [ ] 创建 POST /api/v1/portfolio/positions 添加持仓
- [ ] 创建 PATCH /api/v1/portfolio/positions/{id} 更新持仓
- [ ] 创建 DELETE /api/v1/portfolio/positions/{id} 删除持仓
- [ ] 数据库迁移：portfolios + positions 表
- [ ] 单元测试

### Frontend

- [ ] 创建 Portfolio 页面
- [ ] 创建 PortfolioSummary 组件（总资产/仓位/现金）
- [ ] 创建 PositionTable 组件（持仓列表）
- [ ] 创建 PositionForm 组件（添加/编辑持仓）
- [ ] 创建 PnLDisplay 组件（浮盈亏展示）

## Acceptance Criteria

- 手工创建投资组合
- 添加持仓后正确计算总资产
- 浮盈亏实时计算
- 仓位比例正确展示
- 支持删除/编辑持仓

## References

- [RFC-001](../rfc/RFC-001-sprint-1-foundation-development-plan.md)
