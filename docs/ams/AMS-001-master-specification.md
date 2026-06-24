# Athena Master Specification (AMS) v1.0

## Status

Ratified (2026-06-24)

## Role

本文件是 Athena 项目的**唯一真相来源（Single Source of Truth）**。

任何 PRD、RFC、代码、Prompt、数据库设计，必须引用 AMS，不得各自定义概念。

---

# Chapter 1 — Project Charter

## 1.1 Project Name

**Athena（AI Investment Operating System）**

简称：Athena | 代号：ATH

## 1.2 Vision

构建一个可信、可解释、持续学习的 AI 投资操作系统，帮助投资者形成高质量投资决策，而不是替代投资者进行不可控的交易。

**关键词：**

| 关键词 | 含义 |
|--------|------|
| Trustworthy | 可信 — 每一条建议可追溯 |
| Explainable | 可解释 — 每一条建议有理由链 |
| Evolvable | 可持续演进 — 模块可替换，能力可叠加 |
| Evidence-driven | 证据驱动 — 信号基于多维证据 |
| Human-centered | 以人为中心 — AI 辅助，人决策 |

## 1.3 Mission

Athena 将投资流程拆解为：

```
Data → Information → Knowledge → Insight → Decision → Execution → Review → Learning
```

目标不是自动买股票。目标是不断提高整个投资流程的质量。

---

# Chapter 2 — Persona

## V1 唯一 Persona

**Professional Individual Investor（专业个人投资者）**

- 有长期投资目标
- 能接受 AI 建议
- 希望掌握决策过程
- 重视风险控制
- 愿意持续迭代策略

---

# Chapter 3 — Value Proposition

Athena 与现有软件最大的区别：不是功能更多，而是思维方式不同。

| 传统软件 | Athena |
|----------|--------|
| 行情 → 指标 → 交易 | 市场 → 理解 → 证据 → 推理 → 建议 → 学习 |

---

# Chapter 4 — System Boundary

以后所有需求必须属于边界内，否则拒绝开发。

## Included

- ✅ Data（数据采集、存储、处理）
- ✅ AI（推理、建议、解释）
- ✅ Backtest（回测、模拟）
- ✅ Research（研究、因子、假设）
- ✅ Risk（风险评估、控制）
- ✅ Portfolio（持仓管理、仓位计算）
- ✅ Agent（多 Agent 协作）
- ✅ Dashboard（可视化、交互）

## Excluded

- ❌ Broker account management（券商账户管理）
- ❌ Banking system（银行系统）
- ❌ Payment（支付）
- ❌ Social（社交）
- ❌ Chat（聊天 — 非投资相关对话）
- ❌ News portal（新闻门户 — 仅消费新闻数据，不建门户）

---

# Chapter 5 — Core Domains

基于 DDD（领域驱动设计），Athena 只有 **6 个 Domain**，所有功能只能属于其中之一。

| Domain | 职责 |
|--------|------|
| **Research** | 宏观/行业/企业分析、因子研究、假设验证、回测 |
| **Market** | 市场状态识别、指数监控、资金流向、热度分析 |
| **Decision** | 证据收集、推理、建议生成、置信度计算 |
| **Portfolio** | 持仓管理、仓位计算、盈亏分析、风险评估 |
| **Execution** | 交易计划生成、订单管理、执行记录 |
| **Learning** | 复盘、模型更新、知识积累、经验沉淀 |

---

# Chapter 6 — Unified Object Model

所有 API、Database、Agent 围绕以下对象。

```
Market
├── Index          # 指数
├── Sector         # 行业
├── Theme          # 概念/主题
├── Liquidity      # 流动性
├── Breadth        # 市场宽度
├── Volatility     # 波动率
└── Policy         # 政策事件

Company
├── Basic          # 基本信息
├── Industry       # 行业归属
├── Financial      # 财务数据
├── Valuation      # 估值数据
├── Shareholder    # 股东结构
├── SupplyChain    # 产业链
└── Events         # 重大事件

Strategy
├── Factor         # 因子
├── Signal         # 信号
├── Rule           # 规则
├── Weight         # 权重
└── Score          # 评分

Decision
├── Evidence       # 证据条目
├── Reason         # 推理链路
├── Confidence     # 置信度
├── Risk           # 风险评估
└── Recommendation # 最终建议

Portfolio
├── Cash           # 现金
├── Position       # 持仓
├── Order          # 订单
├── PnL            # 盈亏
└── Risk           # 组合风险

Learning
├── Experiment     # 实验记录
├── Review         # 复盘记录
├── Knowledge      # 知识条目
└── Experience     # 经验沉淀
```

---

# Chapter 7 — Daily Lifecycle

Athena 每天重复同一生命周期，所有 Agent 必须遵守。

```
Collect   → 采集数据（市场、新闻、财报、政策）
Clean     → 清洗、标准化
Analyze   → 分析（各 Agent 并行工作）
Reason    → 推理（综合多维度证据）
Recommend → 生成建议（附证据、置信度）
Execute   → 生成交易计划（人工确认）
Evaluate  → 评估结果（对比预测 vs 实际）
Learn     → 学习（更新模型、积累经验）
Improve   → 优化（调整参数、更新知识）
```

---

# Chapter 8 — AI Philosophy

此章永不修改。

AI 不是预测机器，而是推理机器。

| 优先级 | 职责 | 说明 |
|--------|------|------|
| 1st | Understand | 理解市场发生了什么 |
| 2nd | Explain | 解释为什么会发生 |
| 3rd | Recommend | 基于理解给出建议 |
| Last | Predict | 如果需要，预测概率（非价格） |

---

# Chapter 9 — 3-Year Roadmap

## Year 1: Research Platform

- 数据平台（AKShare → Multi-source）
- Feature Store
- 回测平台
- Dashboard（完整闭环）
- Strategy Library（插件化）
- 基础 6 Domain 闭环

## Year 2: AI CIO

- 多 Agent 系统（14+ Agents）
- Event Bus 通信
- Decision Engine（证据驱动）
- Explainable AI（完整输出）
- Learning Engine（持续进化）
- Knowledge Graph

## Year 3: Autonomous Investment Assistant

- 模拟盘运行
- 自动执行（可配置风控）
- Portfolio Brain（AI 仓位管理）
- AI Researcher（自主研究）
- AI Strategy Generator（策略生成）
- Investment Memory（完整决策记忆）

## Current: Sprint 1 (Year 1 Foundation)

参见 [RFC-001](../rfc/RFC-001-sprint-1-foundation-development-plan.md)

---

# Chapter 10 — Success Metrics (KPI)

## Investment Metrics

| 指标 | 说明 |
|------|------|
| 年化收益率 | Annualized Return |
| 夏普比率 | Sharpe Ratio |
| 最大回撤 | Max Drawdown |
| Calmar 比率 | Calmar Ratio |
| Sortino 比率 | Sortino Ratio |
| 信息比率 | Information Ratio |
| Alpha / Beta | 超额 / 市场敏感度 |
| 胜率 | Win Rate |
| 盈亏比 | Profit-Loss Ratio |
| 换手率 | Turnover Rate |

## AI Metrics

| 指标 | 说明 |
|------|------|
| 决策命中率 | 建议方向正确率 |
| 置信度校准误差 | 预测概率 vs 实际频率的差距 |
| 解释质量 | 人工评估 |
| 建议采纳率 | 用户采纳比例 |
| 学习速度 | 错误修正所需时间 |
| 模型漂移 | Model Drift |

## Engineering Metrics

| 指标 | 说明 |
|------|------|
| API 延迟 | p50/p95/p99 |
| Agent 成功率 | 无异常完成比例 |
| 数据延迟 | 采集到可用时间 |
| Prompt 成本 | Token 消耗 |
| 回测耗时 | 全量回测时间 |
| 系统稳定性 | Uptime |

---

## References

- [Constitution v2.0.0](../project_charter/Constitution.md)
- [ADR-000 Project Freeze](../adr/ADR-000-project-freeze.md)
- [ADR-004 Evidence-Driven AI](../adr/ADR-004-evidence-driven-ai.md)
- [AES-001 Four-Layer Architecture](../aes/AES-001-four-layer-architecture.md)
- [Investment Ontology](../ontology/ONT-001-investment-ontology.md)
- [Glossary](../glossary/GLOSSARY.md)
