---
id: INV-ARCH-002
title: Investment Hypothesis Framework
classification: S
status: Approved
version: 1.0.0
owner: Chief Architect
reviewer: Founder
board: Investment Board
---

# Purpose

Athena 的核心资产不是指标，也不是策略，而是经过持续验证的 Investment Hypothesis（投资假设）。

所有 Signal、Probability Model、Decision Rule 均应服务于验证、支持或否定某一投资假设。

本框架定义投资假设的完整生命周期，是 INV-ARCH-001（S→P→D Framework）的先导层和知识根源。

---

# Core Principle

> **Long-Term Asset** = Verified Hypotheses (Knowledge)
> **Short-Term Asset** = Strategies (Derived Products)

Athena 不追求"策略库"的规模，而追求"假设库"的深度与验证闭环。

任何未来策略均应能够映射到一个或多个已定义的 Investment Hypothesis。

---

# Investment Intelligence Pipeline

```
Reality
    ↓
Observation（观察）
    ↓
Evidence（证据）
    ↓
Hypothesis（假设）
    ↓
Signal（信号）
    ↓
Probability（概率）
    ↓
Decision（决策）
    ↓
Execution（执行）
    ↓
Feedback（反馈）
    ↓
Learning（学习）
    ↓ (loop back to Hypothesis)
```

每一层向下一层传递结构化信息，不可越层。

Hypothesis 是 Pipeline 的核心节点，上承 Evidence，下启 Signal。

---

# Hypothesis Definition

Investment Hypothesis 是一种关于市场运行规律的可验证假设。

## 定义标准

每个 Hypothesis 必须满足以下四个刚性标准：

### 1. Falsifiable（可证伪）

必须存在明确的观测集合，当这些观测出现时，该假设应被判定为不支持（或不成立）。

> **反例**: "市场会涨" —— 不可证伪，因为无法定义什么算"没涨"。
> **正例**: "M2 同比增速 > 10% 且持续上升 3 个月时，沪深300 在未来 6 个月内跑赢中证500" —— 可界定验证条件。

### 2. Measurable（可量化）

所有核心变量必须可度量，且度量方法有明确定义。

| 变量类型 | 要求 |
|---------|------|
| 自变量 | 必须有明确的数据来源、频率、口径 |
| 因变量 | 必须有明确的计算方式和基准 |
| 条件变量 | 必须定义阈值和判定规则 |

### 3. Backtestable（可回测）

假设必须在历史数据上可复现验证。

- 回测需指定：时间范围、样本空间、基准、统计检验方法
- 回测结果需记录：胜率、夏普比率、最大回撤、信息系数（IC）
- 严禁生存偏差（Survivorship Bias）和前视偏差（Look-Ahead Bias）

### 4. Continuously Verifiable（可持续验证）

假设必须设计为可被系统持续自动验证。

- 定义验证频率（每日 / 每周 / 每月 / 每季度）
- 定义验证触发器（数据到达时 / 时间到达时 / 事件发生时）
- 定义衰减规则（长期未触发时如何处理）

---

# Hypothesis Lifecycle

每个 Investment Hypothesis 经历以下生命周期：

```
Proposed（提出）
    ↓
Validated（验证中）
    ↓
├── Active（活跃 — 当前有效）
│       ↓
│   ├── Strengthened（强化 — 新证据支持）
│   ├── Weakened（弱化 — 新证据部分否定）
│   └── Retired（退役 — 失效/被替代）
│
└── Rejected（否决 — 验证不通过）
```

## 状态转换规则

| 从 | 到 | 条件 |
|----|-----|------|
| Proposed | Validated | 通过初始回测验证（IC > 0 且统计显著） |
| Validated | Active | 通过评审委员会批准 |
| Validated | Rejected | 未通过回测或逻辑审查 |
| Active | Strengthened | 连续 N 期验证通过 |
| Active | Weakened | 连续 M 期验证不通过 |
| Active | Retired | 假设前提不再成立（如政策环境改变） |
| Strengthened | Active | 状态聚合展示 |
| Weakened | Active | 逆转证据出现 |
| Weakened | Retired | 确认失效且无逆转可能 |

---

# Hypothesis Schema

每个 Hypothesis 的标准字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 唯一标识，格式: `HYP-{domain}-{seq}` |
| `name` | string | 简洁的假设名称 |
| `statement` | string | 假设陈述（一句话） |
| `category` | enum | 宏观 / 行业 / 策略 / 行为 / 结构 |
| `domain` | enum | 对应 DDD Bounded Context |
| `variables` | list | 自变量/因变量/条件变量定义 |
| `evidence_requirements` | list | 验证该假设所需的证据类型 |
| `falsification_criteria` | string | 证伪条件 |
| `backtest_config` | object | 回测配置 |
| `verification_schedule` | string | 持续验证计划 |
| `status` | enum | 生命周期状态 |
| `confidence` | float | 当前置信度 [0, 1] |
| `parent_hypotheses` | list | 父假设（知识图谱关系） |
| `child_hypotheses` | list | 子假设 |
| `related_signals` | list | 关联信号 |
| `related_strategies` | list | 衍生策略 |
| `audit_trail` | list | 状态变更历史 |

---

# Relationship to INV-ARCH-001

Hypothesis Framework 是 Signal → Probability → Decision Framework 的先导层。

```
Hypothesis（本框架）
    ↓
Evidence（证据转化）
    ↓
Signal（INV-ARCH-001 §Signal Model）
    ↓
Probability（INV-ARCH-001 §Probability Engine）
    ↓
Decision（INV-ARCH-001 §Decision Engine）
    ↓
Execution
    ↓
Review → Feedback → Hypothesis（闭环）
```

## 职责分离

| 层 | 职责 | 所属框架 |
|----|------|---------|
| Hypothesis | 定义"为什么这么认为" | INV-ARCH-002 |
| Evidence | 收集"有什么依据" | INV-ARCH-002 |
| Signal | 计算"现在是什么状态" | INV-ARCH-001 |
| Probability | 推断"未来大概率怎样" | INV-ARCH-001 |
| Decision | 决定"现在做什么" | INV-ARCH-001 |

禁止 Signal 层定义假设。禁止 Decision 层自行解释信号。

---

# Hypothesis Categories

所有 Hypothesis 必须归属以下类别之一：

| 类别 | 说明 | 示例 |
|------|------|------|
| Macro Hypothesis | 关于宏观经济与市场整体运行规律的假设 | 流动性 → 风格切换 |
| Industry Hypothesis | 关于行业/板块相对强弱规律的假设 | 行业轮动与经济周期 |
| Strategy Hypothesis | 关于特定策略逻辑的假设 | 因子有效性 |
| Behavioral Hypothesis | 关于市场参与者行为规律的假设 | 情绪 → 反转 |
| Structural Hypothesis | 关于市场制度/结构影响的假设 | 注册制 → 定价效率 |

---

# Evidence Model

Evidence 是连接 Reality 与 Hypothesis 的桥梁。

## Evidence 类型

| 类型 | 示例 | 数据源 |
|------|------|--------|
| Macro Data | GDP, CPI, PMI, M2, 社融 | 国家统计局 / Wind |
| Market Data | 指数、成交量、涨跌比 | 交易所 / 数据商 |
| Flow Data | 北向资金、主力资金、融资融券 | 交易所 / Wind |
| Sentiment Data | 舆情指数、搜索热度、VIX | 新闻 / 社交 / 衍生品 |
| Fundamental Data | ROE、营收增速、估值分位 | 财报 / 数据商 |
| Policy Data | 央行报告、产业政策、监管文件 | 政府网站 / 研报 |
| Event Data | 财报公告、分红、增减持 | 交易所公告 |
| Microstructure Data | 订单簿、tick 数据、高频因子 | 交易所 Level-2 |

## Evidence → Signal 转化规则

- 每条 Evidence 需定义置信度权重
- 多条 Evidence 融合时需记录融合方法（加权/贝叶斯/投票）
- Evidence 失效时需触发 Signal 更新

---

# Knowledge Evolution

Hypothesis 是 Athena 的长期知识资产。

## 知识资产积累路径

```
单个 Hypothesis 验证
        ↓
多个相关 Hypothesis 形成 Hypothesis Network（假设网络）
        ↓
Hypothesis Network → Domain Theory（领域理论）
        ↓
Domain Theory → Investment Knowledge Graph（投资知识图谱）
```

## 知识演化规则

| 阶段 | 触发条件 | 产出 |
|------|---------|------|
| Hypothesis 验证 | 单个假设通过 N 期验证 | 假设状态更新 |
| Hypothesis Network | 多个假设存在因果关系 | 知识图谱边 |
| Domain Theory | 假设网络稳定且自洽 | 理论文档 |
| Knowledge Graph | 多个理论关联 | 可查询知识库 |

---

# Examples

## Example 1: Macro Liquidity Hypothesis

**Hypothesis**:
"流动性持续改善将提升成长风格相对收益。"

**Evidence**:
- M2 同比增速
- 社会融资规模增量
- 市场利率（DR007, 10年期国债收益率）
- 北向资金净流入

**Signals**（映射到 INV-ARCH-001）:
- Liquidity Score
- Northbound Flow Direction
- Credit Expansion Rate
- Growth/Value Spread

**Probability**（映射到 INV-ARCH-001）:
- Growth Outperformance Probability

**Decision**（映射到 INV-ARCH-001）:
- 提升成长板块配置比例

**Falsification Criteria**:
- 流动性指标上升但成长风格连续 2 个月跑输价值风格

---

## Example 2: Sector Rotation Hypothesis

**Hypothesis**:
"经济复苏初期，周期性行业（有色、化工、建材）相对收益优于防御性行业（消费、医药）。"

**Evidence**:
- PMI 新订单指数
- 工业增加值同比
- 行业营收增速差异
- 行业估值分位

**Signals**:
- Economic Cycle Phase
- Sector Momentum Score
- Sector Valuation Spread

**Probability**:
- Cyclical Outperformance Probability

**Decision**:
- 行业超配/低配调整

**Falsification Criteria**:
- PMI > 50 持续 2 个月但周期性行业未产生超额收益

---

## Example 3: Behavioral Hypothesis

**Hypothesis**:
"市场极端恐慌后 20 个交易日内，沪深300 反弹概率 > 70%。"

**Evidence**:
- VIX / 恐慌指数
- 成交量放大倍数
- 跌停家数占比
- 融资余额下降幅度

**Signals**:
- Panic Index
- Volume Surge Ratio
- Margin Call Pressure

**Probability**:
- Mean Reversion Probability

**Decision**:
- 逆向加仓（有严格止损）

**Falsification Criteria**:
- 连续 3 次恐慌信号后无反弹，或反弹幅度小于 2%

---

# Success Criteria

Athena 不以策略作为长期资产。
Athena 以 Investment Hypothesis 作为长期知识资产。

## 量化标准

| 指标 | 目标 | 说明 |
|------|------|------|
| Hypothesis 覆盖率 | 覆盖 5 大类别各 ≥ 2 个假设 | 知识广度 |
| 验证闭环率 | ≥ 80% 假设有持续验证 | 知识健康度 |
| 假设置信度 | Active 假设平均 Confidence ≥ 0.6 | 知识可靠性 |
| 策略映射率 | 100% 策略可追溯到假设 | 架构合规 |
| 证伪执行率 | 100% 假设有明确定义的证伪条件 | 科学标准 |

---

# Governance

## 评审流程

```
提出者 → Investment Board 初审
    ↓
通过 → 数据验证（回测）
    ↓
通过 → 逻辑审查（Chief Architect）
    ↓
通过 → 批准发布（Founder）
    ↓
进入 Hypothesis Registry
```

## 审批权限

| 操作 | 权限 |
|------|------|
| 提出假设 | Researcher / Strategist |
| 批准假设 | Investment Board |
| 修改假设 | 原提出者 + Board 批准 |
| 退役假设 | Board 决议 |
| 否决假设 | Chief Architect / Founder (一票否决) |

---

# References

| 文档 | 关系 |
|------|------|
| [INV-ARCH-001](./INV-ARCH-001-signal-probability-decision-framework.md) | 下游框架：Signal → Probability → Decision |
| [ONT-001](../ontology/ONT-001-investment-ontology.md) | 概念定义：Market States, Money Flow, Sector Rotation |
| [AMS-001](../ams/AMS-001-master-specification.md) | 主规格说明书 |
| [ADR-004](../adr/ADR-004-evidence-driven-ai.md) | Evidence-Driven AI 原则 |
| [ADR-007](../adr/ADR-007-feature-store-dsl.md) | Feature Store：Evidence 数据管理 |
| [GUIDE-001](../GUIDE-001-architecture-decision-rationale.md) | 架构决策依据指南 |

---

# Open Questions

以下问题保留，不做超前设计：

1. Hypothesis 之间是否支持冲突检测和自动消解？
2. 是否引入 Hypothesis Marketplace（假设交易市场）用于内部定价？
3. Confidence 计算是否引入贝叶斯更新机制？
4. 知识图谱的存储技术选型（Neo4j vs PostgreSQL Graph）？
5. Hypothesis 版本管理与策略回滚机制？

---

# Glossary

| 术语 | 定义 |
|------|------|
| Hypothesis | 关于市场运行规律的可验证假设 |
| Evidence | 用于支持或否定假设的可观测数据 |
| Falsification | 证伪：定义什么条件下假设不成立 |
| Hypothesis Network | 多个关联假设形成的因果网络 |
| Domain Theory | 经过充分验证的假设集群 |
| Confidence | 假设当前有效性的概率估计 |
| Decay | 信号/假设随时间推移的效力衰减 |
