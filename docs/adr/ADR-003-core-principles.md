# ADR-003 Core Engineering & Investment Principles

## Status

Approved (2026-06-24)

## Decision

Athena 项目采用以下核心原则，覆盖工程、架构、投资三个维度。

---

## Engineering Principles

### 1. Documentation First

任何功能开发流程：

`Idea → Issue → PRD → Architecture → Review → Implementation → Test → Merge`

无 PRD，不开发。

### 2. Everything Has Version

- PRD: v1.0, v1.1, v2.0
- Prompt: v1, v2, v3
- Agent: MarketAgent v1, MarketAgent v2
- Database Schema: v1, v2
- API: v1, v2

**原因**: 几年后仍可追溯每一次变更。

### 3. Event-Driven Agent Communication

所有 Agent 禁止直接调用其他 Agent。必须通过 Event Bus。

```
MarketChanged Event → StrategyAgent → SignalGenerated Event → PortfolioAgent → ...
```

新增 Agent 不修改任何旧代码。

### 4. AI Safety — Human In The Loop

AI 永远不能直接控制交易。

```
AI → Recommendation → Risk Engine → Execution Rule → Manual Approval → Broker
```

### 5. Explainable AI

任何建议必须可解释。

❌ 推荐: 贵州茅台, Score: 91
✅ 推荐: 贵州茅台  
    ✔ 行业资金连续流入  
    ✔ ROE连续增长  
    ✔ 北向资金连续净买  
    ✔ 市场趋势: Bull  
    ✔ 风险: 低  
    信心: 91%

---

## Architecture Principles

### 6. Fully Replaceable Modules

任一模块必须可替换而不影响系统。

| 今天 | 以后 | 业务代码改动 |
|------|------|-------------|
| AKShare | Wind | 0 |
| OpenAI | Qwen | 0 |
| Mock Provider | Real Provider | 0 |

策略、模型、数据源、LLM、券商接口均遵循统一接口 + 低耦合 + 高内聚。

### 7. Four-Layer Architecture

见 [AES-001 Four-Layer Architecture](../aes/AES-001-four-layer-architecture.md)。

- **Data Layer** — 数据接入 + Data Lake + Feature Store
- **Domain Layer** — Market / Portfolio / Strategy / Risk / Research
- **AI Layer** — LLM / Agents / Learning / Prediction
- **Application Layer** — Dashboard / API / Mobile / Report

### 8. Three-Tier Intelligence

- **Rule Engine** — 止损、风控等确定性规则
- **ML Engine** — 预测、分类、因子模型
- **LLM Engine** — 推理、解释、研究

三层共同决策，非单一依赖 AI。

---

## Investment Principles

### 9. Decision Quality > Alpha

Athena 的核心 KPI 不是跑赢指数，而是**持续提升决策质量**。

| 指标 | 说明 |
|------|------|
| 决策命中率 | 建议的正确率 |
| 风险控制能力 | 最大回撤控制 |
| 回撤控制 | 下行风险限制 |
| 决策一致性 | 风格不漂移 |
| 模型稳定性 | 时间鲁棒性 |
| 学习效率 | 错误修正速度 |

### 10. Feature Gate

任何新增功能必须回答三个问题：

1. 它解决什么投资问题？
2. 它如何提升长期收益或降低风险？
3. 它如何与现有模块协作，而不是重复功能？

回答不了，暂不开发。

---

## Consequences

- 所有 Feature 必须有 PRD
- Agent 间通信必须通过 Event Bus（实现后）
- AI 推荐必须带解释字段
- 模块接口必须定义 Provider/Interface 抽象

## References

- [ADR-001](ADR-001-sprint-1-tech-stack-freeze.md)
- [ADR-002](ADR-002-development-principles.md)
- [AES-001 Architecture Evolution Strategy](../aes/AES-001-four-layer-architecture.md)
