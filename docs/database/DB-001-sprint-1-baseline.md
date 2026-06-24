---
id: DB-001
title: Sprint 1 Database Baseline
status: Approved
version: 1.0.0
depends:
  - RFC-001
---

# DB-001 Sprint 1 Database Baseline

## Naming Convention

- 所有表名、列名使用 snake_case
- 主键统一使用 UUID (v4)
- 所有表包含 created_at / updated_at 时间戳
- 外键命名：`{referenced_table}_id`

## Tables

### users

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, default uuid4 | 用户 ID |
| username | VARCHAR(50) | UNIQUE, NOT NULL | 用户名 |
| email | VARCHAR(255) | UNIQUE, NOT NULL | 邮箱 |
| password_hash | VARCHAR(255) | NOT NULL | 密码哈希 |
| display_name | VARCHAR(100) | | 显示名称 |
| is_active | BOOLEAN | DEFAULT true | 是否激活 |
| created_at | TIMESTAMPTZ | NOT NULL | 创建时间 |
| updated_at | TIMESTAMPTZ | NOT NULL | 更新时间 |

### watchlists

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | 自选组 ID |
| user_id | UUID | FK -> users.id, NOT NULL | 所属用户 |
| name | VARCHAR(100) | NOT NULL | 组名称 |
| sort_order | INTEGER | DEFAULT 0 | 排序 |
| created_at | TIMESTAMPTZ | NOT NULL | |
| updated_at | TIMESTAMPTZ | NOT NULL | |

### watchlist_items

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | 项目 ID |
| watchlist_id | UUID | FK -> watchlists.id, NOT NULL | 所属自选组 |
| symbol | VARCHAR(20) | NOT NULL | 股票代码 |
| name | VARCHAR(100) | | 股票名称 |
| tags | TEXT[] | DEFAULT '{}' | 标签数组 |
| note | TEXT | | 备注 |
| sort_order | INTEGER | DEFAULT 0 | 排序 |
| created_at | TIMESTAMPTZ | NOT NULL | |
| updated_at | TIMESTAMPTZ | NOT NULL | |

### portfolios

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | 投资组合 ID |
| user_id | UUID | FK -> users.id, NOT NULL | 所属用户 |
| name | VARCHAR(100) | NOT NULL | 组合名称 |
| cash | DECIMAL(18,2) | DEFAULT 0 | 现金余额 |
| created_at | TIMESTAMPTZ | NOT NULL | |
| updated_at | TIMESTAMPTZ | NOT NULL | |

### positions

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | 持仓 ID |
| portfolio_id | UUID | FK -> portfolios.id, NOT NULL | 所属组合 |
| symbol | VARCHAR(20) | NOT NULL | 股票代码 |
| name | VARCHAR(100) | | 股票名称 |
| shares | DECIMAL(18,4) | NOT NULL | 持仓数量 |
| cost_price | DECIMAL(18,4) | NOT NULL | 成本价 |
| current_price | DECIMAL(18,4) | | 当前价（定期更新） |
| created_at | TIMESTAMPTZ | NOT NULL | |
| updated_at | TIMESTAMPTZ | NOT NULL | |

### market_snapshots

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | |
| symbol | VARCHAR(20) | NOT NULL | 指数/股票代码 |
| name | VARCHAR(100) | | 名称 |
| price | DECIMAL(18,4) | NOT NULL | 当前价 |
| change_pct | DECIMAL(10,4) | | 涨跌幅 |
| volume | BIGINT | | 成交量 |
| turnover | DECIMAL(18,2) | | 成交额 |
| snapshot_time | TIMESTAMPTZ | NOT NULL | 快照时间 |
| metadata | JSONB | | 扩展数据 |
| created_at | TIMESTAMPTZ | NOT NULL | |

### recommendations

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | |
| user_id | UUID | FK -> users.id, NOT NULL | 所属用户 |
| action | VARCHAR(20) | NOT NULL | buy/hold/sell/reduce |
| symbol | VARCHAR(20) | | 关联股票（可选） |
| confidence | DECIMAL(5,2) | | 置信度 0-100 |
| reason | TEXT | | 理由 |
| risk | VARCHAR(20) | | low/medium/high |
| position_suggestion | DECIMAL(5,2) | | 建议仓位 % |
| expire_at | TIMESTAMPTZ | | 过期时间 |
| created_at | TIMESTAMPTZ | NOT NULL | |

## Indexes

- watchlists: (user_id)
- watchlist_items: (watchlist_id)
- watchlist_items: (symbol)
- portfolios: (user_id)
- positions: (portfolio_id)
- market_snapshots: (symbol, snapshot_time)
- recommendations: (user_id, created_at)

## References

- [RFC-001](../rfc/RFC-001-sprint-1-foundation-development-plan.md)
