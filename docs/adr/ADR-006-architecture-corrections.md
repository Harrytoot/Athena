# ADR-006 Architecture Corrections — DDD, Event Sourcing, CQRS, Plugin, AI Positioning

## Status

Approved (2026-06-24)

## Decision 1 — No "Universal AI"（不做万能 AI）

Athena 定位必须保持纯粹：**Investment Decision Operating System**。

所有功能必须直接服务于提高投资决策质量，否则拒绝。

| 拒绝 | 原因 |
|------|------|
| ChatGPT 聊天 | 非投资决策 |
| 新闻门户 | 消费新闻数据即可，不建门户 |
| 股票论坛/社交 | 非核心 |
| OA/IM/Office | 非投资功能 |

## Decision 2 — DDD Enforcement（领域驱动设计）

整个系统按 Domain 组织，不按 Controller/Service/DAO。

每个 Domain 统一结构：

```
Domain/
├── Entity/          # 实体
├── ValueObject/     # 值对象
├── Aggregate/       # 聚合根
├── Repository/      # 仓储接口
├── Service/         # 领域服务
├── Event/           # 领域事件
└── Policy/          # 领域策略（规则）
```

6 个 Domain：Market, Research, Decision, Portfolio, Execution, Learning。

## Decision 3 — Event Sourcing（事件溯源）

不保存当前状态，保存整个过程。

❌ 数据库只存：Cash = 80万
✅ 保存事件流：

```
CashReduced(amount=20万, reason="Buy 600519.SH", time="...", operator="...")
```

任何时候可重建任意时刻的完整状态。所有变更可审计。

## Decision 4 — CQRS（命令查询分离）

| 类型 | 职责 | 路径 |
|------|------|------|
| Command | 写操作（状态变更） | `/command/...` |
| Query | 读操作（数据查询） | `/query/...` |

Agent 也分离：Command Agent vs Query Agent。

## Decision 5 — Plugin System（插件架构）

整个系统只有 Kernel 稳定，其他全部 Plugin：

```
Kernel（不可变）
├── Plugin: Provider（数据源）
├── Plugin: Strategy（策略）
├── Plugin: Feature（特征）
├── Plugin: Agent（分析单元）
├── Plugin: Indicator（指标）
├── Plugin: Broker（券商）
└── Plugin: Report（报告）
```

新增能力 = 新增 Plugin，Kernel 无改动。

## Decision 6 — AI Is Not the Center

Athena 的真正中心：

```
Knowledge → Reasoning → Decision → Execution
                  ↑
                LLM
            (仅 Reasoning)
```

LLM 只是 Reasoning 层的一个实现。换模型不改系统。

## Decision 7 — Prompt as Template（不允许直接写 Prompt）

```
MarketPrompt
    ↓
Template（模板）
    ↓
Variables（变量注入）
    ↓
Context（上下文字段）
    ↓
LLM（调用）
```

所有 Prompt 配置化，版本化，不可硬编码。

## Decision 8 — Capability Registry（能力注册）

系统注册能力，不注册 Agent。

```
Capability: MarketAnalysis
  Provider: MarketAgent v2.0
  Input: MarketSnapshot
  Output: MarketRegime + Confidence

Capability: RiskAssessment
  Provider: RiskAgent v1.5
  Input: Portfolio + MarketState
  Output: RiskScore + Breakdown
```

Agent 可替换，Capability 永远在。

## Consequences

- 所有新功能必须先过 Architecture Budget 检查
- DDD 结构立即生效（Sprint 1 目录对齐）
- Event Sourcing / CQRS → Sprint 2 实施
- DSL / Capability Registry → Sprint 2 实施

## References

- [AMS-001](../ams/AMS-001-master-specification.md)
- [Constitution v2.0.0](../project-charter/Constitution.md)
