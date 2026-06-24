---
id: TASK-0003
title: Epic-003 Watchlist
epic: Watchlist
status: Pending
priority: High
dependencies:
  - ADR-001
  - RFC-001
  - TASK-0001
---

# TASK-0003 Epic-003 Watchlist

## Goal

创建/删除自选组、添加/删除股票、标签、排序、备注。禁止直接操作数据库，必须经过 Domain。

## Domain

Watchlist

## Tasks

### Backend

- [ ] 创建 Watchlist 聚合根 (domain/aggregates/watchlist.py)
- [ ] 创建 WatchlistItem 实体 (domain/entities/watchlist_item.py)
- [ ] 创建 WatchlistRepository 接口
- [ ] 创建 SQLAlchemy Watchlist / WatchlistItem Model
- [ ] 创建 WatchlistRepositoryImpl
- [ ] 创建 WatchlistService (application/services/watchlist_service.py)
- [ ] 创建 POST /api/v1/watchlists 创建自选组
- [ ] 创建 DELETE /api/v1/watchlists/{id} 删除自选组
- [ ] 创建 POST /api/v1/watchlists/{id}/items 添加股票
- [ ] 创建 DELETE /api/v1/watchlists/{id}/items/{item_id} 删除股票
- [ ] 创建 GET /api/v1/watchlists 列表（含项目）
- [ ] 创建 PATCH /api/v1/watchlists/{id}/items/{item_id} 更新标签/备注/排序
- [ ] 数据库迁移：watchlists + watchlist_items 表
- [ ] 单元测试

### Frontend

- [ ] 创建 Watchlist 页面
- [ ] 创建 WatchlistGroupCard 组件（自选组展示）
- [ ] 创建 WatchlistGroupForm 组件（创建/编辑组）
- [ ] 创建 StockSearch 组件（搜索添加股票）
- [ ] 创建 StockListItem 组件（展示股票 + 操作菜单）
- [ ] 创建 TagEditor 组件（添加/删除标签）

## Acceptance Criteria

- 创建自选组成功，展示在列表
- 删除自选组后不再显示
- 搜索并添加股票到自选组
- 删除自选组中的股票
- 支持标签、备注编辑
- 支持排序功能

## References

- [RFC-001](../rfc/RFC-001-sprint-1-foundation-development-plan.md)
