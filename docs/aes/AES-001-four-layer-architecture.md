# AES-001 Architecture Evolution Strategy

## Status

Approved (2026-06-24)

## Vision

Athena 定义为 **AI Investment Operating System**，非传统 AI Quant System。

## Target Architecture: Four Layers

```
┌────────────────────────────────────────┐
│       Application Layer                │
│  Dashboard │ API │ Mobile │ Report     │
├────────────────────────────────────────┤
│          AI Layer                      │
│  LLM │ Agents │ Learning │ Prediction  │
├────────────────────────────────────────┤
│        Domain Layer                    │
│  Market │ Portfolio │ Strategy         │
│  Risk │ Research                       │
├────────────────────────────────────────┤
│         Data Layer                     │
│  Connectors │ Data Lake │ Feature Store│
└────────────────────────────────────────┘
```

### Data Layer

**Data Connector Marketplace**: 所有数据源为插件。

```
Connector/
├── AKShare
├── Wind
├── 同花顺
├── 东方财富
├── 雪球
├── 聚宽
├── RiceQuant
├── CSV
├── Excel
└── REST API
```

新增数据源：零系统改动。

**Data Lake**: 分层存储。

```
Raw Data → Bronze → Silver → Gold
```

- **Raw**: AKShare 原始数据
- **Silver**: 统一字段、清洗后数据
- **Gold**: AI 直接使用、特征数据

**Feature Store**: 统一特征计算，所有策略/Agent/模型共享。

### Domain Layer

五大业务中心：

| 中心 | 职责 |
|------|------|
| **Research Center** | 宏观/行业/企业研究、估值、财报、知识管理 |
| **Market Center** | 每日市场分析、状态判断 |
| **Decision Center** | AI CIO，综合多维度输出建议 |
| **Execution Center** | 交易计划生成、执行 |
| **Learning Center** | 每日复盘、模型更新、持续进化 |

### AI Layer

**Agent 架构**:

```
MarketAgent, MacroAgent, PolicyAgent, IndustryAgent,
MoneyFlowAgent, SentimentAgent, FactorAgent,
StrategyAgent, PortfolioAgent, RiskAgent,
ExecutionAgent, LearningAgent, ReportAgent, ResearchAgent
```

**通信**: Event Bus only。

```
MarketAgent → MarketChanged Event → Event Bus → StrategyAgent
```

**Meta Agent**: 元调度器，动态调整各 Agent 权重。

**Three-Tier Intelligence**:

| 层级 | 引擎 | 职责 |
|------|------|------|
| L1 | Rule Engine | 止损、风控 |
| L2 | ML Engine | 预测、因子 |
| L3 | LLM Engine | 推理、解释 |

**Knowledge Graph**: 产业链 + 实体关系。

```
机器人 → 减速器 → 绿的谐波 → 供应商 → 客户 → 政策 → 基金持仓 → 产业链
```

### Application Layer

Dashboard / API / Mobile / Report — 面向用户的产品形态。

---

## Evolution Path

| Sprint | Layer | Focus |
|--------|-------|-------|
| Sprint 1 | Data + Application | Foundation: Market, Watchlist, Portfolio |
| Sprint 2 | Domain + AI | Agents, Event Bus, Research Center |
| Sprint 3 | Data | Feature Store, Knowledge Graph |
| Sprint 4+ | Full Stack | Continuous Backtesting, Investment Memory |

---

## Key Decisions

1. **Knowledge Graph** — 产业链推导能力，Sprint 3 启动
2. **Investment Memory** — 保存"为什么交易"，Sprint 4+ 启动
3. **Strategy Marketplace** — Sprint 2 启动，策略即插件
4. **Continuous Backtesting** — 每日凌晨自动回测，生成报告

---

## References

- [ADR-001](../adr/ADR-001-sprint-1-tech-stack-freeze.md)
- [ADR-003 Core Principles](../adr/ADR-003-core-principles.md)
