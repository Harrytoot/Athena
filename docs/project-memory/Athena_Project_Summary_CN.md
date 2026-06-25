# Athena 项目全面总结

> **交接文档 — 供下一个AI继续设计指导**
> 生成日期：2026-06-25 | Sprint 1 (Foundation) — 全部6个Epic已实现，进入Review阶段

---

## 目录

1. [项目身份](#1-项目身份)
2. [技术栈](#2-技术栈)
3. [核心设计原则 (14条Constitution)](#3-核心设计原则)
4. [架构决策记录](#4-架构决策记录)
5. [领域模型](#5-领域模型)
6. [数据库设计](#6-数据库设计)
7. [API设计](#7-api设计)
8. [后端代码结构](#8-后端代码结构)
9. [前端代码结构](#9-前端代码结构)
10. [基础设施](#10-基础设施)
11. [Sprint 1 完成状态](#11-sprint-1-完成状态)
12. [Sprint 2 规划](#12-sprint-2-规划)
13. [Athena Brain 知识操作系统](#13-athena-brain-知识操作系统)
14. [正式文档清单](#14-正式文档清单)
15. [关键文件路径速查](#15-关键文件路径速查)
16. [Git提交历史](#16-git提交历史)
17. [目录结构全览](#17-目录结构全览)
18. [给下一个AI的指导要点](#18-给下一个ai的指导要点)
19. [附录：产品架构5大产品](#附录产品架构5大产品)
20. [附录：Sprint 2详细定义](#附录sprint-2详细定义)
21. [附录：工程标准要点](#附录工程标准要点)
22. [附录：命名规范](#附录命名规范)

---

## 1. 项目身份

| 项目 | 说明 |
|------|------|
| **名称** | Athena — AI投资操作系统 |
| **定位** | 数字投资伙伴 (Digital Investment Partner)，**非**股票交易App/量化系统/自动交易机器人 |
| **当前阶段** | Sprint 1 (Foundation) — 全部6个Epic已实现，进入Review阶段 |
| **启动日期** | 2026-06-24 |
| **目标** | 构建可信、可解释、持续学习的AI投资OS，提升长期**决策质量**而非短期收益 |

### 核心投资生命周期

```
Observe → Research → Understand → Reason → Decide → Execute → Review → Learn
```

### 五大核心能力

1. **Observe** — 持续市场感知
2. **Understand** — 解释变化原因
3. **Reason** — 模拟情景
4. **Recommend** — 有证据支撑的建议
5. **Learn** — 从决策中持续改进

### 目标用户 (V1)

**专业个人投资者** (Professional Individual Investor)

### 三阶段路线图

| 阶段 | 名称 | 周期 | 内容 |
|------|------|------|------|
| Phase A | Research OS | ~6个月 | 数据采集、分析、特征工程、研究平台 |
| Phase B | Decision OS | ~6个月 | AI决策引擎、知识图谱、推荐系统 |
| Phase C | Execution OS | ~6个月 | 交易执行、组合优化、持续学习 |

> Sprint 1 是 Phase A 的 Foundation（基础）

---

## 2. 技术栈

> **ADR-001 冻结，任何变更需新ADR**

| 层 | 技术 | 版本 |
|----|------|------|
| **前端** | Next.js + React + TypeScript | 14.x / 18.x |
| **前端样式** | Tailwind CSS + shadcn/ui | 3.x |
| **后端** | Python + FastAPI + SQLAlchemy + Pydantic | 3.12 / 2.x / v2 |
| **数据库** | PostgreSQL + Redis + MinIO | 16 / 7 / latest |
| **基础设施** | Docker Compose + Nginx | — |
| **AI Gateway** | LiteLLM | — |
| **架构模式** | DDD + Clean Architecture + Plugin Architecture | — |

### Sprint 1 明确排除的范围

- AI Agent 系统
- 自动交易 / 量化回测
- 知识图谱 (Neo4j)
- 投资 DSL 编译器
- 事件溯源 (Event Sourcing) / CQRS

---

## 3. 核心设计原则

> **项目宪法 Constitution v2.1.0 — 14条，不可违反**

| 条款 | 原则 | 说明 |
|------|------|------|
| **I** | Identity | 始终是"数字投资伙伴"，不是交易工具 |
| **II** | Trustworthy AI | 每个推荐必须有证据链 (Evidence Chain) |
| **III** | Documentation First | 先写PRD再写代码 |
| **IV** | Architecture Governance | Plugin/Provider模式，Event Bus |
| **V** | AI Safety | AI**永远不直接控制交易**，人类最终决策 |
| **VI** | Measure Everything | 度量Agent/策略/因子/模型/Prompt |
| **VII** | Feature Gate | 新功能必须回答3个投资问题 |
| **VIII** | Repository is Source of Truth | Git仓库是唯一真相源 |
| **IX** | Constitution Amendable | 通过RFC→ADR流程修订宪法 |
| **X** | Evidence Driven | 证据图 (Evidence Graph) 而非简单规则 |
| **XI** | Predict Probability, Not Price | 预测概率，不预测价格 |
| **XII** | Confidence Required | 所有AI输出必须标注置信度 (0-100) |
| **XIII** | "I Don't Know" | 允许输出"无法判断"/"等待"/"无机会" |
| **XIV** | Architecture Budget | 防止复杂性蔓延，控制架构预算 |

### 投资原则 (CONSTITUTION-002)

- **概率优于预测** — Probability over Prediction
- **证据优先** — Evidence First
- **人类最终决策** — Human Final Authority
- **风险先于收益** — Risk Before Return
- **长期一致性** — Long-term Consistency
- **持续学习** — Continuous Learning
- **完全可追溯** — Full Traceability

---

## 4. 架构决策记录

> 共11个ADR，全部已批准 (Approved)

### ADR-000: 项目冻结
- 项目命名为 **Athena**
- 确立13项核心原则
- 三阶段路线图 (Research → Decision → Execution)
- 6个月一个阶段

### ADR-001: 技术栈冻结
- 前端：Next.js + React + TypeScript + Tailwind + shadcn/ui
- 后端：Python 3.12 + FastAPI + SQLAlchemy 2.x + Pydantic v2
- 数据库：PostgreSQL 16 + Redis 7 + MinIO
- 基础设施：Docker Compose + Nginx + LiteLLM
- 架构：DDD + Clean Architecture + Plugin Architecture

### ADR-002: 开发原则
- User Value First, Vertical Slice, Mock First, Human First, Documentation First
- Sprint 1的开发顺序：Market Center → Watchlist → Stock Detail → Portfolio → Recommendation → Authentication
- **认证放在最后**，因为Sprint 1是单用户Alpha版

### ADR-003: 10条核心工程与投资原则
- Documentation First, Everything Has Version, Event-Driven Agent Communication
- AI Safety (Human In The Loop), Explainable AI
- Fully Replaceable Modules (AKShare→Wind, OpenAI→Qwen → 零代码变更)
- Four-Layer Architecture, Three-Tier Intelligence (Rule/ML/LLM)
- Decision Quality > Alpha, Feature Gate

### ADR-004: 证据驱动AI
- Evidence-Driven（非规则驱动）— 每个推荐有多维度证据强度
- Predict Probability, Not Price
- 所有AI输出必须有Confidence (0-100)
- "I Don't Know" 是合法输出
- 文档标准化：RFC + ADR + PRD 格式

### ADR-005: 企业R&D流程与团队结构
- **6个角色**：Founder, Chief Architect (ChatGPT), Software Engineer (OpenCode), QA Architect, Data Architect, AI Governance
- **TDD流程**：PRD → Test Case → Code → CI → Merge
- **架构治理流程**：Idea → RFC → Review → ADR → PRD → Task → Code
- **DDD Monorepo目录结构**定义
- **Provider Pattern**强化
- **数据标准**：股票代码 `600519.SH`，ISO 8601日期，人民币(元)，Decimal(18,4)

### ADR-006: 8项架构修正
1. **拒绝"万能AI"** — 纯粹投资OS；拒绝ChatGPT聊天、新闻门户、社交、OA
2. **DDD强制执行** — 6个领域，组织为 Entity/ValueObject/Aggregate/Repository/Service/Event/Policy
3. **Event Sourcing** — 保存事件流而非当前状态（Sprint 2+实现）
4. **CQRS** — 命令/查询分离（Sprint 2+实现）
5. **Plugin System** — 只有Kernel是稳定的，其他都是Plugin
6. **AI非中心** — LLM只是Reasoning层的实现手段
7. **Prompt as Template** — 所有Prompt版本化、可配置
8. **Capability Registry** — 注册能力，而非注册Agent

### ADR-007: 特征存储与投资DSL
- **Feature Store**：统一特征管理（technical, fundamental, money_flow, policy, sentiment, market）
- **投资DSL语法示例**：
  ```
  WHEN Market.Regime == BULL
  AND Feature("policy_score") > 80
  THEN ALLOCATE 8% TO Stock("600519.SH")
  ```
- DSL编译链：`Athena DSL → Compiler → Feature Calls + Capability Calls → Execution Plan`
- Sprint 2+实现

### ADR-008: Sprint 1开发序列
- 严格顺序执行Epic（禁止并行）
- 每个Epic必须通过3门审查：Code Review + Architecture Review + Product Acceptance
- 当前状态（文档记录时间）：Epic 002-004 已实现，等待审查

### ADR-009: 工程基线冻结
- 冻结项：技术栈、目录结构、分层架构（Domain→Application→Infrastructure→Presentation）、Provider Pattern、Documentation First
- 所有未来的架构/数据库/API/Provider/Plugin变更需要新ADR

### ADR-010: Athena Brain 引入
- 引入 Athena Brain 作为项目**唯一的长期知识载体**
- Knowledge、Research、Code 三层分离，不同治理
- **Brain层级**：Constitution (L0) → Knowledge (L1) → Research (L2) → Experiments (L3) → Failures (L4) → Playbooks (L5)
- **知识状态机**：Idea → Hypothesis → Experiment → Validated → Knowledge → Playbook → Decision Engine
- **7条治理规则**（核心：没有长期投资结论可以直接进入代码）
- AI Onboarding 顺序：Constitution → ADR → Brain → Research → Playbooks

---

## 5. 领域模型

### 6个核心限界上下文

```
Research → Market → Decision → Portfolio → Execution → Learning
```

| 领域 | 核心对象 | Sprint 1实现 |
|------|----------|-------------|
| **Market** | MarketRegime, MarketOverview, MarketSnapshot, HotSector, AiMarketSummary | ✅ |
| **Research** | Company, Financial, Valuation, Factor, Feature | ❌ Sprint 2+ |
| **Decision** | Evidence, Reason, Confidence, Recommendation | ✅ (推荐CRUD) |
| **Portfolio** | Cash, Position, Order, Portfolio | ✅ |
| **Execution** | Broker, Order, Execution | ❌ Sprint 3+ |
| **Learning** | Experiment, Review, Knowledge | ❌ Sprint 2+ |

### Sprint 1 实现的领域实体 (8个)

| 实体 | 文件 | 说明 |
|------|------|------|
| User | `domain/entities/user.py` | 用户dataclass |
| MarketOverview | `domain/entities/market.py` | 市场概览 + MarketRegime枚举 |
| MarketSnapshot | `domain/entities/market.py` | 市场快照 |
| HotSector | `domain/entities/market.py` | 热门板块 |
| AiMarketSummary | `domain/entities/market.py` | AI市场摘要 |
| WatchlistItem | `domain/entities/watchlist.py` | 自选股票项 |
| Portfolio | `domain/entities/portfolio.py` | 投资组合（含PnL、权重、集中度检查等业务逻辑） |
| Position | `domain/entities/portfolio.py` | 持仓 |
| Recommendation | `domain/entities/recommendation.py` | 推荐（含Action/Source/Priority枚举） |

### 聚合根 (1个)

- **WatchlistAggregate** (`domain/aggregates/watchlist.py`) — DDD聚合根，管理自选组及其股票项

### 值对象 (2个)

- **Money** — 不可变dataclass，Decimal精度，货币安全算术运算
- **Percentage** — 百分比值对象

### 仓库接口 (3个)

- `UserRepository`
- `WatchlistRepository`
- `PortfolioRepository`

---

## 6. 数据库设计

> 7张表，全部 UUID PK，snake_case命名，timestamptz时间戳

```sql
-- 用户表
users (
    id UUID PRIMARY KEY,
    username VARCHAR UNIQUE NOT NULL,
    email VARCHAR UNIQUE NOT NULL,
    password_hash VARCHAR NOT NULL,
    display_name VARCHAR,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
)

-- 自选组
watchlists (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    name VARCHAR NOT NULL,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
)

-- 自选股票项
watchlist_items (
    id UUID PRIMARY KEY,
    watchlist_id UUID REFERENCES watchlists(id) ON DELETE CASCADE,
    symbol VARCHAR NOT NULL,
    name VARCHAR,
    tags TEXT[],
    note TEXT,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
)

-- 投资组合
portfolios (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    name VARCHAR NOT NULL,
    cash DECIMAL(18,4) DEFAULT 0,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
)

-- 持仓
positions (
    id UUID PRIMARY KEY,
    portfolio_id UUID REFERENCES portfolios(id) ON DELETE CASCADE,
    symbol VARCHAR NOT NULL,
    name VARCHAR,
    shares DECIMAL(18,4),
    cost_price DECIMAL(18,4),
    current_price DECIMAL(18,4),
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
)

-- 市场快照
market_snapshots (
    id UUID PRIMARY KEY,
    symbol VARCHAR NOT NULL,
    name VARCHAR,
    price DECIMAL(18,4),
    change_pct DECIMAL(18,4),
    volume BIGINT,
    turnover DECIMAL(18,4),
    snapshot_time TIMESTAMPTZ,
    metadata JSONB,
    created_at TIMESTAMPTZ
)

-- 推荐
recommendations (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    action VARCHAR NOT NULL,       -- BUY/SELL/HOLD/REDUCE
    symbol VARCHAR NOT NULL,
    confidence INTEGER,            -- 0-100
    reason TEXT,
    risk TEXT,
    position_suggestion TEXT,
    expire_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
)
```

### 索引策略

- `users`: user_id (PK)
- `watchlists`: user_id, created_at
- `watchlist_items`: watchlist_id, symbol
- `portfolios`: user_id
- `positions`: portfolio_id, symbol
- `market_snapshots`: (symbol, snapshot_time)
- `recommendations`: (user_id, created_at)

---

## 7. API设计

- **Base URL**: `/api/v1`
- **认证**: JWT Bearer Token
- **命名规范**: RESTful，名词复数，kebab-case URL，camelCase JSON

### 全部端点 (14+)

```
POST   /api/v1/auth/login              # 登录 -> { access_token, token_type }
GET    /api/v1/auth/me                 # 当前用户信息
GET    /api/v1/dashboard               # 仪表盘概览

GET    /api/v1/market/overview         # 市场概览
                                       # 返回: 指数列表, 成交额, 涨跌家数,
                                       #       北向资金, 热点板块, AI摘要

GET    /api/v1/stocks/{symbol}         # 股票详情
                                       # 返回: 基本信息, 技术指标, 资金流, AI分析

GET    /api/v1/watchlists              # 获取自选组列表
POST   /api/v1/watchlists              # 创建自选组
DELETE /api/v1/watchlists/{id}         # 删除自选组

POST   /api/v1/watchlists/{id}/items   # 向自选组添加股票
DELETE /api/v1/watchlists/{id}/items/{item_id}  # 从自选组移除股票
PATCH  /api/v1/watchlists/{id}/items/{item_id}  # 更新股票项

GET    /api/v1/portfolio               # 获取投资组合
POST   /api/v1/portfolio               # 创建投资组合
POST   /api/v1/portfolio/positions     # 添加持仓
PATCH  /api/v1/portfolio/positions/{id}  # 编辑持仓
DELETE /api/v1/portfolio/positions/{id}  # 删除持仓

GET    /api/v1/recommendations         # 获取推荐列表
```

---

## 8. 后端代码结构

> DDD四层架构：Domain → Application → Infrastructure → Presentation

```
src/backend/
├── app/
│   ├── main.py                    # FastAPI入口，lifespan上下文管理器
│   │                              # 注册7个路由，自动发现插件
│   ├── config.py                  # Pydantic Settings（从.env加载）
│   │                              # DB/Redis/MinIO/JWT/LiteLLM配置
│   │
│   ├── api/                       # 【表示层 / Presentation】
│   │   ├── deps.py                # 依赖注入（get_db, get_current_user等）
│   │   └── v1/
│   │       ├── auth.py            # POST login, GET me
│   │       ├── dashboard.py       # GET dashboard
│   │       ├── market.py          # GET market/overview
│   │       ├── stock.py           # GET stocks/{symbol}
│   │       ├── watchlist.py       # CRUD watchlists + items
│   │       ├── portfolio.py       # CRUD portfolios + positions
│   │       └── recommendation.py  # GET recommendations
│   │
│   ├── domain/                    # 【领域层】纯Python，零框架依赖
│   │   ├── entities/              # 6个实体文件
│   │   │   ├── user.py            # User dataclass
│   │   │   ├── market.py          # MarketRegime枚举, MarketOverview,
│   │   │   │                      #   MarketSnapshot, HotSector, AiMarketSummary
│   │   │   ├── stock.py           # Stock实体
│   │   │   ├── watchlist.py       # WatchlistItem实体
│   │   │   ├── portfolio.py       # Portfolio + Position实体
│   │   │   │                      #   含业务逻辑: PnL计算, 权重, 集中度检查
│   │   │   └── recommendation.py  # Recommendation实体
│   │   │                          #   含枚举: Action(BUY/SELL/HOLD/REDUCE),
│   │   │                          #   Source(AI/MANUAL/RULE), Priority(HIGH/MED/LOW)
│   │   ├── aggregates/            # DDD聚合根
│   │   │   └── watchlist.py       # WatchlistAggregate
│   │   ├── repositories/          # 仓库接口（抽象）
│   │   │   ├── user_repository.py
│   │   │   ├── watchlist_repository.py
│   │   │   └── portfolio_repository.py
│   │   ├── value_objects/         # 值对象
│   │   │   ├── Money.py           # 不可变，Decimal精度，货币安全算术
│   │   │   └── Percentage.py
│   │   └── services/              # 领域服务
│   │       └── __init__.py
│   │
│   ├── application/               # 【应用层】编排领域对象
│   │   ├── services/              # 6个应用服务
│   │   │   ├── auth_service.py
│   │   │   ├── market_service.py
│   │   │   ├── stock_service.py
│   │   │   ├── watchlist_service.py
│   │   │   ├── portfolio_service.py
│   │   │   └── recommendation_service.py
│   │   ├── dtos/                  # 5个DTO文件
│   │   │   ├── auth_dtos.py
│   │   │   ├── market_dtos.py
│   │   │   ├── watchlist_dtos.py
│   │   │   ├── portfolio_dtos.py
│   │   │   └── recommendation_dtos.py
│   │   └── interfaces/
│   │
│   ├── infrastructure/            # 【基础设施层】
│   │   ├── persistence/
│   │   │   ├── base.py            # SQLAlchemy declarative_base
│   │   │   ├── session.py         # AsyncSession工厂
│   │   │   ├── models/            # 3个SQLAlchemy模型
│   │   │   │   ├── user.py        # UserModel
│   │   │   │   ├── watchlist.py   # WatchlistModel + WatchlistItemModel
│   │   │   │   └── portfolio.py   # PortfolioModel + PositionModel
│   │   │   └── repositories/      # 3个仓库实现
│   │   │       ├── user_repository.py
│   │   │       ├── watchlist_repository.py
│   │   │       └── portfolio_repository.py
│   │   ├── auth.py                # JWT token生成/验证 + bcrypt密码哈希
│   │   ├── ai_gateway/            # LiteLLM AI网关（预留）
│   │   ├── cache/                 # Redis缓存（预留）
│   │   ├── messaging/             # Event Bus事件总线（预留）
│   │   └── storage/               # MinIO对象存储（预留）
│   │
│   ├── providers/                 # 【Provider模式】数据源抽象层
│   │   ├── __init__.py            # Provider自动加载器
│   │   ├── market/
│   │   │   ├── base.py            # MarketProvider 抽象接口
│   │   │   ├── mock_provider.py   # MockMarketProvider (Sprint 1使用)
│   │   │   └── redis_provider.py  # 带Redis缓存的Provider
│   │   └── stock/
│   │       ├── base.py            # StockSearchProvider 抽象接口
│   │       ├── detail_base.py     # StockDetailProvider 抽象接口
│   │       ├── mock_provider.py   # MockStockSearchProvider
│   │       ├── mock_detail_provider.py  # MockStockDetailProvider
│   │       └── redis_provider.py  # 带Redis缓存的Provider
│   │
│   └── plugins/                   # 【插件系统】
│       ├── base.py                # PluginBase ABC (含生命周期方法)
│       └── registry.py            # PluginRegistry (自动发现+加载)
│
├── tests/                         # 136个测试全部通过
│   ├── conftest.py                # pytest fixtures (async client, test DB等)
│   └── api/
│       ├── test_health.py
│       ├── test_auth_api.py       # 5个测试
│       ├── test_market_api.py     # 3个测试
│       ├── test_stock_api.py      # 2个测试
│       ├── test_watchlist_api.py  # 10个测试
│       ├── test_portfolio_api.py  # 7个测试
│       └── test_recommendation_api.py  # 3个测试
│
├── alembic/                       # 数据库迁移
├── alembic.ini
├── pyproject.toml                 # Python项目配置（pytest, ruff）
├── requirements.txt               # 14个依赖
└── Dockerfile
```

### 关键设计决策

| 设计 | 说明 |
|------|------|
| **Provider模式** | 数据源抽象接口，切换AKShare→Wind零业务代码变更 |
| **Mock优先** | Sprint 1全部使用Mock数据，Sprint 2接入真实AKShare |
| **领域实体** | 纯dataclass，不含框架依赖，业务逻辑在实体方法内 |
| **值对象** | Money/Percentage不可变，保证类型安全 |
| **仓库模式** | 接口在domain层，实现在infrastructure层 |
| **插件系统** | PluginBase提供lifecycle (init/start/stop/health_check) |

---

## 9. 前端代码结构

```
src/frontend/
├── app/                           # Next.js App Router (11个页面)
│   ├── layout.tsx                 # 根布局
│   │                              # - 10项侧边导航栏
│   │                              # - 5项激活: Dashboard, Market, Watchlist,
│   │                              #            Portfolio, Recommend
│   │                              # - 5项禁用占位: Research, Strategy,
│   │                              #            Backtest, AI Center, Settings
│   ├── page.tsx                   # 首页 -> 重定向到 /dashboard
│   ├── globals.css
│   ├── dashboard/
│   │   └── page.tsx               # 仪表盘 (7个子组件)
│   ├── market/
│   │   └── page.tsx               # 市场概览
│   ├── watchlist/
│   │   └── page.tsx               # 自选股管理
│   ├── portfolio/
│   │   └── page.tsx               # 投资组合
│   ├── recommendation/
│   │   └── page.tsx               # 推荐列表
│   ├── stocks/
│   │   └── [symbol]/
│   │       └── page.tsx           # 股票详情 (动态路由)
│   ├── login/
│   │   └── page.tsx               # 登录页
│   └── register/
│       └── page.tsx               # 注册页
│
├── components/
│   ├── ui/                        # 12个UI组件
│   │   ├── MarketRegimeBadge.tsx  # 牛/熊/震荡/高波动 标记
│   │   ├── MarketTemperatureGauge.tsx  # 市场温度计 (0-100)
│   │   ├── IndexCard.tsx          # 指数卡片 (价格, 涨跌幅)
│   │   ├── MarketStatsRow.tsx     # 成交额/涨跌家数/北向资金 行
│   │   ├── HotSectorList.tsx      # 热点行业/概念 列表
│   │   ├── AiMarketSummaryCard.tsx # AI市场摘要 卡片
│   │   ├── UpdateTimeLabel.tsx    # 数据时效 标记
│   │   ├── AiSummaryCard.tsx      # AI分析摘要 卡片
│   │   ├── GroupSidebar.tsx       # 自选组侧边栏
│   │   ├── StockSearch.tsx        # 股票代码搜索器
│   │   ├── TechnicalCard.tsx      # 技术指标卡片
│   │   └── MoneyFlowCard.tsx      # 资金流展示卡片
│   └── UserMenu.tsx               # 用户登录/登出菜单
│
├── lib/                           # API客户端 (6个文件)
│   ├── api.ts                     # 市场概览 + 股票详情
│   ├── auth.ts                    # 登录/注册/获取用户/Token管理
│   ├── watchlist-api.ts           # 自选股CRUD + 股票搜索
│   ├── portfolio-api.ts           # 投资组合CRUD
│   ├── recommendation-api.ts      # 推荐列表
│   └── utils.ts
│
├── types/                         # TypeScript类型 (6个文件)
│   ├── auth.ts                    # TokenResponse, UserResponse
│   ├── market.ts                  # MarketOverview等
│   ├── stock.ts                   # StockDetail
│   ├── watchlist.ts               # Watchlist, StockSearchResult
│   ├── portfolio.ts               # PortfolioDTO, PositionCreate
│   └── recommendation.ts         # RecommendationDTO
│
├── hooks/                         # React Hooks
├── package.json                   # Next.js 14, React 18, Tailwind 3, lucide-react
├── next.config.mjs
├── tailwind.config.ts
├── tsconfig.json
├── postcss.config.js
└── Dockerfile
```

### 前端关键细节

- API Base URL 通过 `NEXT_PUBLIC_API_URL` 环境变量配置
- Token 存储在 `localStorage` 键名 `athena_token`
- 所有 API 调用经过 `lib/` 下的客户端函数
- 所有 11 个页面静态生成成功

---

## 10. 基础设施

### Docker Compose 开发环境 (7个服务)

```yaml
services:
  postgres:
    image: postgres:16-alpine
    ports: ["5432:5432"]
    environment:
      POSTGRES_USER: athena
      POSTGRES_PASSWORD: athena
      POSTGRES_DB: athena
    healthcheck: pg_isready

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
    healthcheck: redis-cli ping

  minio:
    image: minio/minio:latest
    ports: ["9000:9000", "9001:9001"]
    environment:
      MINIO_ROOT_USER: athena
      MINIO_ROOT_PASSWORD: athena_secret

  nginx:
    image: nginx:alpine
    ports: ["80:80"]
    depends_on: [backend, frontend]
    # 反向代理: / -> frontend:3000, /api/ -> backend:8000

  backend:
    build: src/backend
    ports: ["8000:8000"]
    depends_on:
      postgres: {condition: service_healthy}
      redis: {condition: service_healthy}
      minio: {condition: service_healthy}

  frontend:
    build: src/frontend
    ports: ["3000:3000"]
    depends_on: [backend]

  data-worker:
    build: data_worker
    depends_on: [redis]
```

### 生产环境 (`docker-compose.prod.yml`)

- 移除 Nginx（假设使用外部反向代理）
- 移除 data-worker
- 使用 `.env.production` 管理所有密钥
- 添加 `restart: unless-stopped`
- 添加 Docker bridge 网络 `athena`
- Redis 启用 `--appendonly yes` 持久化

### 部署脚本 (`infra/scripts/`)

| 脚本 | 功能 |
|------|------|
| `deploy.sh` | 一键部署 |
| `deploy_fix.sh` | 部署修复 |
| `rollback.sh` | 回滚到指定 commit |
| `backup.sh` | 数据库 + MinIO 每日备份 (30天保留) |
| `healthcheck.sh` | 健康检查 |

### Nginx 配置 (`infra/nginx/athena.conf`)

- 路径路由：`/athena/` → Frontend (3000)，`/athena/api/` → Backend (8000)
- HTTPS + Security Headers
- Rate Limit (限流)
- CORS 白名单
- 非 root 容器运行

---

## 11. Sprint 1 完成状态

> 截至 2026-06-25

### 整体状态

| 指标 | 数值 |
|------|------|
| 后端测试 | **136 passed** (0.37s，0 warnings) |
| 前端构建 | ✅ 成功 (11个页面全部静态生成) |
| 领域实体 | 8个 |
| 聚合根 | 1个 (WatchlistAggregate) |
| 仓库接口 | 3个 |
| API测试覆盖率 | 6/6 Epics (100%) |
| 前端页面 | 11个 |
| 弃用警告 | 0 (来自本项目代码) |
| 构建状态 | ✅ Backend + Frontend 全部通过 |

### 各Epic完成情况

| Epic | 描述 | 状态 | API测试 |
|------|------|------|---------|
| Epic-001 | Authentication | ✅ 完成 | 5 |
| Epic-002 | Market Center | ✅ 完成 | 3 |
| Epic-003 | Watchlist | ✅ 完成 | 10 |
| Epic-004 | Stock Detail | ✅ 完成 | 2 |
| Epic-005 | Portfolio | ✅ 完成 | 7 |
| Epic-006 | Recommendation | ✅ 完成 | 3 |

### 架构里程碑

- 工程基线 (Engineering Baseline)：🟢 完成 (2026-06-24)
- Athena Brain 基础：🟢 完成 (2026-06-24)

---

## 12. Sprint 2 规划

> 主题：**数据层 (Data Layer)** — 替换Mock为真实数据

| Epic | 内容 |
|------|------|
| Epic-004 | Provider Interface 规范化 |
| Epic-005 | AKShare Provider 实现 |
| Epic-006 | Data Normalizer (数据标准化管道) |
| Epic-007 | Feature Model (特征模型) |
| Epic-008 | Provider Health Check |

**目标**：用 AKShare 真实数据替换全部 Mock 数据，Alembic 数据库迁移

---

## 13. Athena Brain 知识操作系统

> 项目的**长期知识载体**，Knowledge/Research/Code 三层治理

### 层级结构

```
docs/brain/
├── README.md                                        # Brain 概览 + AI入职指南
├── BRAIN-001-athena-brain-governance.md             # 7条治理规则
├── BRAIN-002-knowledge-index-specification.md       # 知识索引规范
│
├── 00-constitution/                                 # L0: 宪法
│   └── CONSTITUTION-001-memory-system.md            # 记忆系统宪法
│
├── 01-knowledge/                                    # L1: 已验证知识 (按领域)
│   └── (按投资领域分类的知识条目)
│
├── 02-research/                                     # L2: 研究课题
│   └── README.md                                    # (空, 等待内容)
│
├── 03-experiments/                                  # L3: 可复现实验
│
├── 04-failures/                                     # L4: 失败记录 (永不可删除)
│
├── 05-playbooks/                                    # L5: 投资剧本
│   └── README.md                                    # (空, 等待内容)
│
├── 06-evidence/                                     # 原始证据
│
├── 07-decisions/                                    # 决策记录
│
└── 08-glossary/                                     # 领域术语
```

### 知识状态机

```
Idea → Hypothesis → Experiment → Validated → Knowledge → Playbook → Decision Engine
```

### 7条治理规则

1. **没有长期投资结论可以直接进入代码**
2. 任何结论必须先形成 Research
3. Research 必须有 Evidence
4. Evidence 必须可追溯
5. Playbook 必须引用 Knowledge
6. Decision Engine 必须引用 Playbook
7. 每个 Knowledge 条目必须记录 Confidence (0-100)

### AI 入职顺序

```
Constitution → ADR → Brain → Research → Playbooks
```

---

## 14. 正式文档清单

### 架构决策记录 (docs/adr/)

| 编号 | 标题 | 状态 |
|------|------|------|
| ADR-000 | 项目冻结 (Project Freeze) | ✅ Approved |
| ADR-001 | 技术栈冻结 (Tech Stack Freeze) | ✅ Approved |
| ADR-002 | 开发原则 (Development Principles) | ✅ Approved |
| ADR-003 | 核心工程与投资原则 (10 Principles) | ✅ Approved |
| ADR-004 | 证据驱动AI (Evidence-Driven AI) | ✅ Approved |
| ADR-005 | 企业R&D流程与团队结构 | ✅ Approved |
| ADR-006 | 8项架构修正 | ✅ Approved |
| ADR-007 | 特征存储与投资DSL | ✅ Approved |
| ADR-008 | Sprint 1开发序列 | ✅ Approved |
| ADR-009 | 工程基线冻结 | ✅ Approved |
| ADR-010 | Athena Brain 引入 | ✅ Approved |

### 请求评论 (docs/rfc/)

| 编号 | 标题 | 状态 |
|------|------|------|
| RFC-001 | Sprint 1 Foundation开发计划 | ✅ Approved |
| RFC-002 | 12仓库架构 | ✅ Approved |
| RFC-003 | 部署架构 | ✅ Approved |

### 总规范 (docs/ams/)

| 编号 | 标题 |
|------|------|
| AMS-001 | Master Specification (10章) |

### 架构演进策略 (docs/aes/)

| 编号 | 标题 |
|------|------|
| AES-001 | 四层架构 (Four-Layer Architecture) |
| AES-002 | AI架构 (AI Architecture) |

### 产品文档 (docs/prd/)

| 编号 | 标题 |
|------|------|
| PRD-002 | Watchlist功能需求 |

### API与数据库 (docs/api/, docs/database/)

| 编号 | 标题 |
|------|------|
| API-001 | Sprint 1 API规范 |
| DB-001 | Sprint 1 数据库设计 |

### 工程标准 (docs/engineering/)

- `ATHENA_ENGINEERING_STANDARD.md` — 10部分完整工程标准
- `ENGINEERING_STANDARD_INDEX.md` — 标准索引

### Brain治理 (docs/brain/)

- `BRAIN-001` — Brain治理规则
- `BRAIN-002` — 知识索引规范
- `CONSTITUTION-001` — 记忆系统宪法

### 其他文档

| 目录 | 内容 |
|------|------|
| `docs/project-charter/` | Constitution.md, Vision, Mission |
| `docs/ontology/` | ONT-001 投资本体论 |
| `docs/glossary/` | GLOSSARY.md 术语表 |
| `docs/architecture/` | ARCH-001 架构原则, 系统/Agent/AI/数据/EventBus架构 |
| `docs/governance/` | GOV-001 资产分类, GOV-002 角色治理, GOV-003 组织手册 |
| `docs/product/` | PRODUCT-001 自适应投资OS蓝图 |
| `docs/project/` | PROJECT-001 开发原则 |
| `docs/data/` | DATA-001 特征合约 |
| `docs/ai/` | Agent Spec, Prompt (预留) |
| `docs/roadmap/` | 能力路线图 + Sprint状态 |
| `docs/sprint/` | Sprint-002 定义 |
| `docs/tasks/` | 7个任务规范文件 |
| `docs/constitution/` | DoD, 投资宪法, 决策OS宪法 |
| `docs/project-memory/` | 日报 + 审查策略 + 审查记录 |

---

## 15. 关键文件路径速查

| 类别 | 文件路径 |
|------|----------|
| **项目宪法** | `docs/project-charter/Constitution.md` |
| **总规范文档** | `docs/ams/AMS-001-master-specification.md` |
| **技术栈ADR** | `docs/adr/ADR-001-tech-stack-freeze.md` |
| **工程基线ADR** | `docs/adr/ADR-009-engineering-baseline-freeze.md` |
| **API规范** | `docs/api/API-001-sprint1-api-spec.md` |
| **数据库设计** | `docs/database/DB-001-sprint1-database-design.md` |
| **Sprint 1计划** | `docs/rfc/RFC-001-sprint1-foundation-plan.md` |
| **部署架构** | `docs/rfc/RFC-003-deployment-architecture.md` |
| **架构仓库索引** | `docs/ARCHITECTURE_REPOSITORY.md` |
| **工程标准** | `docs/engineering/ATHENA_ENGINEERING_STANDARD.md` |
| **术语表** | `docs/glossary/GLOSSARY.md` |
| **Sprint状态** | `docs/roadmap/SPRINT_STATUS.md` |
| **AI代理指令** | `AGENTS.md` |
| **后端配置** | `src/backend/app/config.py` |
| **后端入口** | `src/backend/app/main.py` |
| **前端布局** | `src/frontend/app/layout.tsx` |
| **Docker Compose** | `docker-compose.yml` |
| **生产Compose** | `docker-compose.prod.yml` |
| **环境变量模板** | `.env.example`, `.env.production`, `.env.staging` |

---

## 16. Git提交历史

> 最近30次提交 (逆序)

| Commit | 消息 |
|--------|------|
| `1a7aa9a` | Merge branch 'master' |
| `d997249` | docs: Athena Brain constitution, governance, investment framework, product, project, roadmap docs |
| `0dd767a` | feat: Epic-001 Authentication — JWT login/register |
| `39e5c70` | feat: Epic-006 Recommendation + test suite (34 tests) |
| `356692c` | feat(brain): initialize Athena Brain knowledge operating system |
| `8d96b73` | docs: GUIDE-001 architecture decision rationale guide |
| `37384cd` | feat: Epic-005 Portfolio — portfolio management CRUD |
| `fd1ae30` | fix: plugins/__init__.py import, Dockerfile arg, docker-compose revert |
| `d91d48c` | fix: MarketRegimeBadge import path and env vars |
| `1f8b8a5` | fix: next.config.ts → next.config.mjs + env vars fix |
| `4ecd788` | fix: frontend Dockerfile npm ci → npm install (no lockfile) |
| `d755aea` | Initial commit |
| `5bc3721` | feat: RFC-003 Deployment Architecture — production infra |
| `fb098cf` | docs: ADR-009 Engineering Baseline Freeze |
| `34d44ff` | fix: Architecture Baseline Review — 6 critical issues resolved |
| `9a11019` | docs: ARCH-001 — 10 Architecture Principles |
| `d984f10` | docs: Definition of Done (CONST-001) |
| `3dc0806` | docs: Review Policy — 3-Gate Epic review process |
| `e8828f1` | docs: ADR-008 Sprint 1 Sequence Confirmation |
| `991f4fe` | docs: Athena Engineering Standard v1.0 |
| `8600ef3` | docs: Architecture Repository v1.0 |
| `2e797a0` | docs: ADR-006, ADR-007, Product Architecture, Constitution v2.1.0 |
| `a120793` | docs: RFC-002 revised — 12-repo architecture |
| `e26edce` | docs: ADR-005 Enterprise R&D + AES-002 AI Architecture |
| `f91df6f` | docs: AMS-001 Master Specification + Investment Ontology |
| `8be8678` | docs: ADR-004 Evidence-Driven AI — Constitution v2.0.0 |
| `75d5b51` | docs: ADR-000 Project Freeze — mission, 13 principles, 3-phase roadmap |
| `174e40d` | docs: Project Charter — Constitution, Vision, Mission |
| `1977cc1` | docs: ADR-003, AES-001, RFC-002 — architecture & principles baseline |
| `290c0e0` | feat: Epic-004 Stock Detail — provider, API, full page |

---

## 17. 目录结构全览

```
Athena/
├── AGENTS.md                          # AI 代理指令
├── README.md                          # 项目概述 + 快速开始
├── .env.example                       # 开发环境变量模板
├── .env.production                    # 生产环境变量模板
├── .env.staging                       # 预发布环境变量模板
├── .pre-commit-config.yaml            # Pre-commit hooks
│
├── .github/                           # GitHub Actions CI/CD
├── .opencode/                         # OpenCode 配置
│
├── docker-compose.yml                 # 开发环境 Docker Compose (7服务)
├── docker-compose.prod.yml            # 生产环境 Docker Compose (5服务)
├── docker/                            # Docker 配置
│   ├── nginx/
│   ├── minio/
│   ├── postgres/
│   └── redis/
│
├── infra/
│   ├── nginx/
│   │   └── athena.conf               # Nginx 反向代理配置
│   └── scripts/
│       ├── deploy.sh                  # 一键部署
│       ├── deploy_fix.sh              # 部署修复
│       ├── rollback.sh                # 回滚到指定 commit
│       ├── backup.sh                  # 备份 (DB + MinIO, 30天保留)
│       └── healthcheck.sh             # 健康检查
│
├── src/
│   ├── backend/                       # Python FastAPI 后端
│   │   ├── app/                       # 参见第8节详细结构
│   │   ├── tests/                     # 136个测试 (全部通过)
│   │   ├── alembic/                   # 数据库迁移
│   │   ├── alembic.ini
│   │   ├── pyproject.toml
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   └── frontend/                      # Next.js 前端
│       ├── app/                       # 参见第9节详细结构
│       ├── components/
│       ├── lib/
│       ├── types/
│       ├── hooks/
│       ├── package.json
│       ├── next.config.mjs
│       ├── tailwind.config.ts
│       ├── tsconfig.json
│       └── Dockerfile
│
├── data_worker/                       # 后台数据采集 Worker
│   └── Dockerfile
│
├── scripts/                           # 项目脚本
│
└── docs/                              # 全部正式文档 (30+)
    ├── adr/                           # 11个架构决策记录
    ├── rfc/                           # 3个请求评论
    ├── ams/                           # 1个总规范 (10章)
    ├── aes/                           # 2个架构演进策略
    ├── prd/                           # 1个产品需求文档
    ├── api/                           # 1个API规范
    ├── database/                      # 1个数据库设计
    ├── engineering/                   # 工程标准 (10部分) + 索引
    ├── glossary/                      # 领域术语表
    ├── roadmap/                       # 能力路线图 + Sprint状态
    ├── sprint/                        # Sprint-002 定义
    ├── tasks/                         # 7个任务规范
    ├── constitution/                  # 宪法相关 (DoD, 投资宪法, 决策OS宪法)
    ├── project-charter/               # 项目章程 (Constitution, Vision, Mission)
    ├── ontology/                      # 投资本体论
    ├── architecture/                  # 架构原则
    ├── governance/                    # 治理 (资产分类, 角色治理, 组织手册)
    ├── product/                       # 产品蓝图
    ├── project/                       # 开发原则
    ├── data/                          # 特征合约
    ├── ai/                            # Agent Spec, Prompt (预留)
    ├── brain/                         # Athena Brain (8层)
    ├── project-memory/                # 日报 + 审查策略 + 审查记录
    ├── ARCHITECTURE_REPOSITORY.md     # 主架构索引
    └── GUIDE-001-*.md                # 架构决策理由指南
```

---

## 18. 给下一个AI的指导要点

### 当前状态
1. **Sprint 1 全部代码已实现**，使用 Mock 数据，136个测试全部通过
2. **当前处于 Review 阶段**，每个 Epic 需要通过 Code Review + Architecture Review + Product Acceptance 三关
3. 前端11个页面静态生成成功，后端6个Epic全部可运行

### 下一步工作
4. **Sprint 2 核心任务**：接入真实数据，替换 Mock Provider 为 AKShare
5. 任何架构/数据库/API/领域模型/技术栈变更，**必须先写RFC，再走ADR流程**
6. **Provider Pattern 是关键抽象**：所有外部数据源都通过 Provider 接口接入

### 架构约束
7. **遵循DDD四层结构**：domain → application → infrastructure → presentation
8. **Athena Brain 是长期知识载体**：投资结论必须经过 Brain 的知识状态机，不能直接进代码
9. **AI 永远不直接控制交易** — 这是宪法级约束，不可突破
10. **所有文档在 `docs/` 目录下按类型分目录管理**

### 命名规范
11. 股票代码格式：`600519.SH`（上交所）/ `000858.SZ`（深交所）
12. 日期格式：ISO 8601
13. 金额单位：人民币(元)，使用 Decimal(18,4)
14. 后端命名：snake_case，前端：camelCase
15. 事件命名：`{Subject}{Verb}Event` (如 `MarketSnapshotUpdatedEvent`)
16. Prompt 命名：`{agent}_{capability}_v{version}.md`

### 代码质量
17. PEP8 (Python)，TypeScript strict mode
18. 所有代码必须有类型标注
19. 0 弃用警告容忍度
20. 遵循 conventional commits 格式提交

---

## 附录：产品架构5大产品

| 产品 | 用途 | Sprint 1 范围 |
|------|------|--------------|
| **A. Athena Core** | 核心引擎 (DDD Domain, Event Bus, Plugin Kernel) | Domain 骨架 |
| **B. Athena Research** | 研究平台 (Feature Store, Backtest, Factor Research) | — (Sprint 2+) |
| **C. Athena Studio** | 策略开发 (DSL Editor, Strategy Builder, Simulation) | — (Sprint 3+) |
| **D. Athena Terminal** | 投资终端 (Dashboard, Market, Portfolio) | Dashboard + Market + Watchlist + Stock + Portfolio |
| **E. Athena Brain** | AI Agent (Capability Registry, Agents, LLM, Knowledge Graph) | 设计冻结 |

---

## 附录：Sprint 2详细定义

> Sprint 2 主题：**数据层 (Data Layer)**

**目标**：用 AKShare 真实数据替换全部 Mock 数据，建立完整的数据管道

| Epic | 名称 | 描述 |
|------|------|------|
| Epic-004 | Provider Interface | Provider 接口规范化，定义标准数据合约 |
| Epic-005 | AKShare Provider | 实现 AKShare 数据源 Provider |
| Epic-006 | Data Normalizer | 数据标准化管道 (Bronze→Silver→Gold) |
| Epic-007 | Feature Model | 统一特征模型 (Technical, Fundamental, MoneyFlow, etc.) |
| Epic-008 | Provider Health Check | Provider 健康检查与监控 |

### 数据管道 (Data Pipeline)

```
Provider (AKShare) → Normalizer → Feature Store → API
                   ↓
              Redis Cache
```

### 未来架构演进 (Sprint 3+)

- Event Sourcing + CQRS 实现 (ADR-006 已设计)
- AI Agent 系统 (14+ Agents, AES-001/002 已设计)
- Event Bus 事件总线
- Capability Registry 能力注册中心
- Investment DSL 编译器 (ADR-007 已设计)
- Feature Store 特征存储
- Knowledge Graph 知识图谱 (Neo4j)
- Continuous Backtesting 持续回测
- Investment Memory 投资记忆系统
- Paper Trading → Small Capital → Production 决策验证管道
- 12-repo 迁移 (RFC-002)
- C4 架构图

---

## 附录：工程标准要点

> 来源：`docs/engineering/ATHENA_ENGINEERING_STANDARD.md` (v1.0, 10部分)

### Athena 语言 (ATHL)

| 术语 | 含义 | 误用警示 |
|------|------|----------|
| BULL / BEAR / RANGE / VOLATILE | 市场状态 | — |
| BUY / SELL / HOLD / REDUCE | 推荐动作 | — |
| Recommendation ≠ Signal | 推荐≠信号 | 推荐含证据链，信号只是触发 |
| Confidence ≠ Score | 置信度≠分数 | 置信度是概率，分数是排序 |
| Evidence ≠ Reason | 证据≠理由 | 证据是事实，理由是逻辑 |

### 精确术语定义

- **Portfolio**: 一个账户的总资产组合，含 Cash + Positions
- **Position**: 单只股票的持仓 (symbol, shares, cost_price, current_price)
- **Allocation**: 资金分配比例
- **Exposure**: 风险敞口
- **PnL**: (current_price - cost_price) × shares
- **Regime**: 市场状态 (BULL/BEAR/RANGE/VOLATILE)
- **Breadth**: 市场宽度 (上涨家数占比)
- **Liquidity**: 流动性
- **Sentiment**: 市场情绪

### 代码风格

| 层面 | 规范 |
|------|------|
| **API** | RESTful, 名词复数, kebab-case URL, camelCase JSON |
| **数据库** | snake_case 表/列, `{table}_id` 外键, `_at` 时间戳, `is_` 布尔 |
| **Python** | PEP8, snake_case 变量/函数, PascalCase 类, 必须类型标注 |
| **TypeScript** | camelCase, PascalCase 组件, kebab-case 文件名 |
| **日志** | JSON 格式, 含 trace_id + agent 标识符 |

### 核心本体论 (6大本体)

1. **投资本体** — Market States, Money Flow, Sector Rotation, Value vs Growth, Risk, Opportunity, Bubble, Trend, Quality, Margin of Safety
2. **决策本体** — Recommendation Object schema (含证据维度、风险树、替代方案)
3. **风险本体** — 9类风险树：Market, Liquidity, Company, Policy, Valuation, Execution, Model, Data, AI
4. **特征本体** — 7类特征：Technical, Fundamental, MoneyFlow, Policy, Macro, Alternative, LLM
5. **策略本体** — 8大策略家族：Trend Following, Mean Reversion, Momentum, Value, Event Driven, Factor Based, Allocation, ML/AI
6. **Agent/能力分类** — Analyzer, Planner, Evaluator, Researcher, Executor, Reviewer, Learner / 10个能力家族30+具体能力

---

## 附录：命名规范

### 文件命名
```
Python:    snake_case.py
TypeScript: kebab-case.tsx / camelCase.ts (util files)
文档:      UPPER-CASE-TYPE-NNN-description.md (如 ADR-001-tech-stack-freeze.md)
Prompt:    {agent}_{capability}_v{version}.md
```

### 代码命名
```
Python 变量/函数: snake_case
Python 类:         PascalCase
Python 常量:       UPPER_SNAKE_CASE
TS 变量/函数:      camelCase
TS 组件:           PascalCase
TS 类型/接口:      PascalCase
SQL 表/列:         snake_case
SQL 外键:          {referenced_table}_id
SQL 时间戳:        {action}_at (如 created_at, updated_at)
SQL 布尔:          is_{adjective} (如 is_active)
```

### Git 提交
```
格式: <type>: <description>
类型: feat, fix, docs, refactor, test, chore, style, perf
示例: feat: Epic-005 Portfolio — portfolio management CRUD
```

---

> **文档结束** — 完整项目交接信息
>
> 项目路径：`G:\6、AI尝试\Athena`
> 生成时间：2026-06-25
> Sprint 1 状态：全部实现 ✅ | 测试 136/136 ✅ | 构建通过 ✅
