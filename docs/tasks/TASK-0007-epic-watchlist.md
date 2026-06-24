---
id: TASK-0007
title: Epic-003 Watchlist Implementation
status: In Progress
priority: P0
dependencies:
  - ADR-001
  - ADR-002
  - RFC-001
  - TASK-0002
  - PRD-002
---

# TASK-0007 Epic-003 Watchlist Implementation

## Objective

完成 Watchlist 全流程：分组管理 + 股票维护 + 搜索。

## Provider

### StockSearchProvider

```
src/backend/app/providers/stock/
├── __init__.py
├── base.py              # StockSearchProvider 接口
└── mock_provider.py     # MockStockSearchProvider
```

## Backend Architecture

### Domain

- `domain/aggregates/watchlist.py` — Watchlist 聚合根
- `domain/entities/watchlist_item.py` — WatchlistItem 实体
- `domain/repositories/watchlist_repository.py` — Repository 接口

### Application

- `application/services/watchlist_service.py` — WatchlistService
- `application/dtos/watchlist_dtos.py` — Pydantic schemas

### Infrastructure

- `infrastructure/persistence/models/watchlist.py` — SQLAlchemy models
- `infrastructure/persistence/repositories/watchlist_repository.py` — Repository impl

### API

- `GET /api/v1/watchlists` — 列表（含 items + 实时价格）
- `POST /api/v1/watchlists` — 创建分组
- `PUT /api/v1/watchlists/{id}` — 更新分组
- `DELETE /api/v1/watchlists/{id}` — 删除分组
- `POST /api/v1/watchlists/{id}/items` — 添加股票
- `DELETE /api/v1/watchlists/{id}/items/{itemId}` — 删除股票
- `GET /api/v1/watchlists/stock/search?q=` — 搜索股票 (Mock provider)

## Tests

- [ ] Repository 单元测试
- [ ] Service 单元测试
- [ ] API 集成测试

## Acceptance Criteria

- 支持多个分组 CRUD
- 支持添加/删除/搜索股票
- 支持标签、备注、排序
- Provider 可替换
- API 与 Domain 分离
- 禁止直接操作数据库

## References

- [PRD-002](../prd/PRD-002-watchlist.md)
- [RFC-001](../rfc/RFC-001-sprint-1-foundation-development-plan.md)
- [ADR-002](../adr/ADR-002-development-principles.md)
- [DB-001](../database/DB-001-sprint-1-baseline.md)
- [API-001](../api/API-001-sprint-1-baseline.md)
