---
id: INV-ARCH-003
title: Market Regime Engine (MRE)
classification: S
status: Approved
version: 1.0.0
owner: Chief Architect
reviewer: Founder
board: Investment Board
---

# Purpose

Market Regime Engine（MRE）是 Athena 所有投资决策的第一层基础设施。

所有 Signal、Probability、Capital Allocation、Decision 均必须基于当前市场状态进行动态调整。MRE 输出不是建议，而是上下文——是所有下游模块的强制性输入。

---

# Core Principle

不同市场状态下，相同信号具有不同的预测能力。固定权重的信号系统无法适应市场结构性变化。

因此：

```
Signal Weight = f(Market Regime)
```

而不是固定权重。

这一原则贯穿所有下游模块：

| 下游模块 | Regime 影响 |
|---------|------------|
| Signal Engine | 信号权重动态调整 |
| Conflict Resolver | 冲突消解优先级重排 |
| Probability Engine | 先验概率修正 |
| Capital Allocation Engine | 风险预算与仓位上限 |
| Action Engine | 动作选择集合过滤 |

---

# Multi-Dimensional Market Regime

市场状态由多个维度共同描述，而非单一标签。单一维度（如仅看牛/熊）无法捕捉市场的结构化特征。

## Regime Dimensions

### 1. Trend（趋势）

| State | Definition | Quant Criteria (Reference) |
|-------|-----------|---------------------------|
| **Bull** | 趋势向上，市场宽度良好 | 指数 > MA200, Advance/Decline > 1.5 |
| **Bear** | 趋势向下，市场宽度恶化 | 指数 < MA200, Advance/Decline < 0.7 |
| **Range** | 无明确方向，区间震荡 | 波动率收缩，突破失败率高 |
| **Transition** | 趋势正在切换 | 关键均线交叉，动量衰减/加速 |

### 2. Liquidity（流动性）

| State | Definition | Quant Criteria (Reference) |
|-------|-----------|---------------------------|
| **Loose** | 流动性充裕 | 利率下行 + 成交额放大 + 信用利差收窄 |
| **Neutral** | 流动性中性 | 各项指标处于历史中位 |
| **Tight** | 流动性紧张 | 利率上行 + 成交额萎缩 + 信用利差扩大 |

### 3. Volatility（波动率）

| State | Definition | Quant Criteria (Reference) |
|-------|-----------|---------------------------|
| **Low** | 低波环境 | 实现波动率 < 历史 25 分位 |
| **Medium** | 正常波动 | 实现波动率处于历史 25-75 分位 |
| **High** | 高波环境 | 实现波动率 > 历史 75 分位 |

### 4. Risk Appetite（风险偏好）

| State | Definition | Quant Criteria (Reference) |
|-------|-----------|---------------------------|
| **Fear** | 恐慌/避险 | 防御性资产跑赢，信用利差飙升，波动率偏斜极端 |
| **Neutral** | 中性 | 各类资产无明显偏好 |
| **Greed** | 贪婪/追逐风险 | 高风险资产跑赢，杠杆率上升，IPO 活跃 |

### Extensibility

未来可继续增加维度，不破坏现有模型结构：

| 候选维度 | 说明 | 优先级 |
|---------|------|--------|
| Macro | 经济周期位置（复苏/过热/滞胀/衰退） | Sprint 2 |
| Policy | 货币政策/财政政策 stance | Sprint 2 |
| Credit Cycle | 信贷周期阶段 | Sprint 3 |
| Sector Breadth | 行业扩散度 | Sprint 2 |
| Global Correlation | 全球市场联动性 | Sprint 3 |

新增维度通过 Plugin 架构接入，不修改 MRE 核心。

---

# Input Signals

候选输入信号列表。MRE 通过多信号融合进行 Regime 判定，禁止依赖单一指标。

## Signal Categories

| Category | Signals | Update Frequency |
|----------|---------|-----------------|
| **Broad Index Trend** | 沪深300 / 中证500 / 创业板指 均线位置、斜率、交叉 | Daily |
| **Volume** | 两市成交额、成交额 MA、成交额分位 | Daily |
| **Volatility** | 实现波动率(20d/60d)、隐含波动率、振幅 | Daily |
| **Market Breadth** | 涨跌家数比、新高/新低比、>MA20 占比 | Daily |
| **Capital Flow** | 北向资金净流入/出、ETF 资金流、主力资金流向 | Daily |
| **Margin** | 融资余额、融券余额、融资买入占比 | Daily |
| **Macro** | PMI、社融增量、M2 同比、CPI/PPI | Monthly/Weekly |
| **Interest Rate** | DR007、10年期国债收益率、期限利差、信用利差 | Daily |
| **Sector Diffusion** | 行业上涨比例、行业轮动速度 | Daily |
| **Sentiment** | 恐慌指数、换手率、新增投资者数、舆情指数 | Daily/Weekly |

## Signal Ingestion Contract

每个输入信号必须满足：

| 属性 | 要求 |
|------|------|
| 数据来源 | 明确标注，可追溯 |
| 频率 | 明确标注更新频率 |
| 历史长度 | ≥ 5 年（用于回测校准） |
| 缺失处理 | 定义缺失时的填充策略（前值/插值/标记） |
| 标准化 | 统一转换为 Z-Score 或分位值进入模型 |

---

# Methodology

## Regime Detection Approach

MRE 采用**概率化多维度判定**方法，而非硬分类。

核心方法论：

```
For each dimension d:
    P(state_i | signals) = softmax(score_i)

Overall Regime = { d: probability_distribution(d) }
```

### 为什么不用硬分类

| 硬分类 | 概率分布 |
|--------|---------|
| "现在是牛市" | Trend: Bull=0.72, Bear=0.10, Range=0.18 |
| 丢失不确定性信息 | 保留完整信息 |
| 边界处跳变剧烈 | 平滑过渡 |
| 下游无法自行决策 | 下游可按需设定阈值 |

### 初始实现策略

Sprint 1 采用**规则引擎 + 专家打分**的混合方法：

1. 每个维度的每个信号映射到评分函数
2. 评分函数输出 [-1, 1] 连续值
3. 维度内信号加权聚合
4. Softmax 转换为概率分布

Sprint 2+ 可通过 Plugin 接入 ML 模型（LightGBM / XGBoost），替换规则引擎，但必须保持输出 schema 不变。

---

# Output Schema

## Formal Definition

MRE 输出为多维度概率分布，每个维度输出各状态的概率向量：

```json
{
  "timestamp": "2026-06-24T15:00:00+08:00",
  "generated_at": "2026-06-24T15:00:01.123+08:00",
  "version": "1.0.0",
  "regime": {
    "trend": {
      "bull": 0.72,
      "bear": 0.10,
      "range": 0.18,
      "transition": 0.00
    },
    "liquidity": {
      "loose": 0.63,
      "neutral": 0.29,
      "tight": 0.08
    },
    "volatility": {
      "low": 0.15,
      "medium": 0.55,
      "high": 0.30
    },
    "risk_appetite": {
      "fear": 0.12,
      "neutral": 0.45,
      "greed": 0.43
    }
  },
  "confidence": 0.81,
  "regime_change": {
    "detected": false,
    "dimension": null,
    "from": null,
    "to": null,
    "score": 0.0
  },
  "contributors": {
    "trend": [
      {"signal": "index_ma_position", "contribution": 0.35},
      {"signal": "advance_decline_ratio", "contribution": 0.28}
    ],
    "liquidity": [
      {"signal": "northbound_flow", "contribution": 0.30},
      {"signal": "volume_percentile", "contribution": 0.25}
    ]
  },
  "metadata": {
    "model_version": "rule-engine-v1",
    "signals_used": 24,
    "signals_missing": 2,
    "computation_time_ms": 45
  }
}
```

## Output Properties

| Field | Type | Description |
|-------|------|-------------|
| `regime.<dimension>` | object | 每个维度的概率分布，所有状态概率之和 = 1.0 |
| `confidence` | float [0,1] | 整体判定置信度（信号完整性 & 一致性加权） |
| `regime_change` | object | Regime 切换检测结果 |
| `contributors` | object | 各信号对维度判定的贡献度（用于可解释性） |
| `metadata` | object | 模型版本、数据质量、计算元信息 |

## Invariants

1. 所有概率分布之和必须等于 1.0（允许 ±0.001 浮点误差）
2. `confidence` 必须为正值，`regime_change.score` 必须为正值
3. Contributor 贡献度之和归一化后应接近 1.0
4. 下游模块不应直接依赖原始概率值做硬阈值判断，而应将分布整体纳入决策模型

---

# Dependency

以下模块必须消费 MRE 输出。所有依赖 MRE 的模块应在初始化时声明其 Regime 消费契约。

## Downstream Consumers

| Module | Dependency | Consumed Fields |
|--------|-----------|----------------|
| **Signal Engine** | 强制 | `regime.trend`, `regime.volatility` |
| **Conflict Resolver** | 强制 | `regime.trend`, `confidence` |
| **Probability Engine** | 强制 | 全部 `regime` 维度 |
| **Capital Allocation Engine** | 强制 | `regime.liquidity`, `regime.volatility`, `regime.risk_appetite` |
| **Action Engine** | 强制 | 全部 `regime` 维度 + `regime_change` |
| **Review Module** | 强制 | 全部输出（用于学习与评估） |
| **UI Dashboard** | 可选 | `regime` 摘要（展示用途） |

## Consumption Contract

所有消费者必须遵循：

1. **Read-Only**: 不得修改 MRE 输出
2. **Temporal Coupling**: 使用与当前时间戳匹配的 MRE 输出
3. **Graceful Degradation**: MRE 不可用时（如数据缺失导致 confidence < 0.3），下游应降级至保守模式
4. **Regime Change Response**: `regime_change.detected == true` 时，下游必须重新评估所有开仓信号

---

# Interface

## Internal API

```
MRE.generate(input_signals: List[Signal]) -> RegimeOutput
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `input_signals` | `List[Signal]` | 标准化后的输入信号列表 |
| Returns | `RegimeOutput` | 符合 Output Schema 的 Regime 判定结果 |

## Event

MRE 在完成 Regime 判定后发布 Domain Event：

```
Event: MarketRegimeUpdated
Payload: { regime_output_id, previous_regime_id, regime_change_detected, timestamp }
```

下游模块通过 Event Bus 订阅 `MarketRegimeUpdated` 事件，触发相应的重新计算流程。

## Scheduling

| Trigger | Frequency | Description |
|---------|-----------|-------------|
| Market Close | Daily (T+0 15:30) | 日频全量 Regime 计算 |
| Intraday Update | Intraday (可选) | 盘中关键信号变化时增量更新 |
| On-Demand | Manual/API | 回测/研究场景按需计算 |
| Data Arrival | Event-driven | 月度宏观数据到达时触发更新 |

---

# Learning

Market Regime Engine 必须具备持续学习能力——不是一次性模型，而是持续进化的系统。

## Learning Loop

```
MRE Output
    ↓
Downstream Decisions
    ↓
Outcome Observation
    ↓
Review Module
    ↓
Regime Quality Assessment
    ↓
Parameter Tuning / Model Upgrade
    ↓ (loop back to MRE)
```

## Review Metrics

Review 模块持续评估以下指标：

| Metric | Definition | Target |
|--------|-----------|--------|
| **Regime Accuracy** | 事后确认的 Regime 与 MRE 判定的匹配率 | ≥ 70% |
| **Regime Lag** | Regime 切换信号与实际切换点的时差（交易日） | ≤ 3 days |
| **Signal Contribution** | 各输入信号对判定的边际贡献（SHAP / Permutation） | 持续追踪 |
| **Feature Importance Drift** | 信号重要性随时间的变化率 | 异常检测 |
| **Confidence Calibration** | confidence 与实际准确率的校准曲线 | ECE < 0.1 |
| **Downstream Impact** | Regime 判定对下游决策质量的边际影响 | 持续追踪 |

## Model Evolution Path

| Phase | Approach | Trigger |
|-------|----------|---------|
| Phase 1 | 规则引擎 + 专家权重 | Sprint 1 默认 |
| Phase 2 | ML 模型（LightGBM）替代规则引擎 | Regime Accuracy < 65% 持续 20 交易日 |
| Phase 3 | 集成模型（多模型投票） | 单一模型在特定 Regime 下失效 |
| Phase 4 | 自适应在线学习 | 市场结构突变检测触发 |

每次模型升级必须通过 AB 测试验证（新模型 vs 旧模型并行运行 ≥ 60 交易日），由 Chief Architect 审批。

---

# Relationship to Other Frameworks

## Position in Athena Architecture

```
ONT-001 (Investment Ontology)
    ↓ (概念定义)
INV-ARCH-002 (Investment Hypothesis Framework)
    ↓ (假设 → 证据)
INV-ARCH-003 (Market Regime Engine) ← 本文档
    ↓ (Regime 上下文)
INV-ARCH-001 (Signal → Probability → Decision Framework)
    ↓
Execution → Review → Learning (闭环)
```

MRE 位于 Hypothesis Framework 与 S→P→D Framework 之间，为 Signal Engine 提供动态上下文。

## 职责分离

| 层 | 职责 | 所属框架 |
|----|------|---------|
| Hypothesis | 定义"为什么这样判断市场" | INV-ARCH-002 |
| Market Regime | 判定"当前市场处于什么状态" | **INV-ARCH-003（本文档）** |
| Signal | 计算"现在是什么信号" | INV-ARCH-001 |
| Probability | 推断"未来大概率怎样" | INV-ARCH-001 |
| Decision | 决定"现在做什么" | INV-ARCH-001 |

---

# Success Criteria

Athena 能够动态识别市场状态，并根据不同 Regime 自动调整全部投资行为。

## 量化标准

| 指标 | 目标 | 说明 |
|------|------|------|
| Regime 维度覆盖率 | Sprint 1: 4 维度全部可用 | 基础维度完备 |
| 信号覆盖率 | ≥ 80% 候选信号已接入 | 数据完备度 |
| 日频更新可靠性 | ≥ 95% 交易日成功生成 | 运维可靠性 |
| 下游集成率 | 5/5 强制消费模块已集成 | 架构合规 |
| Regime Accuracy | ≥ 70% (事后验证) | 判定质量 |
| Regime Lag | ≤ 3 交易日 | 响应速度 |
| 可解释性 | 每次输出包含 top-N contributors | 透明性 |
| 降级可用性 | MRE 不可用时下游仍可运行（保守模式） | 系统韧性 |

---

# Governance

## 变更管理

| 变更类型 | 审批权限 | 流程 |
|---------|---------|------|
| 新增 Regime 维度 | Chief Architect + Founder | RFC |
| 修改判定方法 | Chief Architect + Founder | RFC + AB 测试 |
| 修改输入信号集 | Chief Architect | ADR |
| 修改输出 Schema | Chief Architect + 下游模块 Owner | RFC（Breaking Change） |
| 参数调整 | Investment Board | PR Review |
| 模型升级 | Chief Architect | AB 测试 + ADR |

## 版本管理

MRE 输出携带 `metadata.model_version`，所有下游模块应记录消费的 MRE 版本，用于回测复现和审计追溯。

## 冻结条款

以下事项在 Sprint 1 不做：
1. ML 模型替代规则引擎（保留至 Sprint 2+）
2. 实时 Tick 级别 Regime 判定（保留至 Sprint 3+）
3. 全球多市场 Regime 联动（保留至 Sprint 3+）

---

# References

| 文档 | 关系 |
|------|------|
| [INV-ARCH-001](./INV-ARCH-001-signal-probability-decision-framework.md) | 下游框架：Signal → Probability → Decision |
| [INV-ARCH-002](./INV-ARCH-002-investment-hypothesis-framework.md) | 上游框架：Investment Hypothesis |
| [ONT-001](../ontology/ONT-001-investment-ontology.md) | 概念定义：Market States (Bull/Bear/Range) |
| [AMS-001](../ams/AMS-001-master-specification.md) | 主规格说明书 |
| [ADR-004](../adr/ADR-004-evidence-driven-ai.md) | Evidence-Driven AI 原则 |
| [ADR-007](../adr/ADR-007-feature-store-dsl.md) | Feature Store：输入信号数据管理 |

---

# Open Questions

以下问题保留，不在 Sprint 1 解决：

1. 多维度 Regime 之间是否存在相关性，是否需要联合概率建模？
2. Regime 切换的提前预警机制（Early Warning Signal）如何设计？
3. 极端事件（黑天鹅）下的 Regime 判定如何处理？（模型失效 + 人工 override）
4. Regime 判定的置信区间（而非点估计）是否需要输出？
5. 不同资产类别（股票/债券/商品）是否需要独立的 Regime 判定？
6. MRE 是否需要引入宏观经济 Nowcasting 模型？
7. 盘中 Regime 更新的频率与触发机制？

---

# Glossary

| 术语 | 定义 |
|------|------|
| Market Regime | 市场状态的综合描述，由多维度概率分布表征 |
| Regime Dimension | 描述市场状态的独立维度（Trend / Liquidity / Volatility / Risk Appetite） |
| Regime Change | 某一维度的主导状态发生切换的事件 |
| Softmax | 将评分向量转换为概率分布的数学函数 |
| Confidence | MRE 对自身判定可靠性的整体评估 |
| Signal Contribution | 单个输入信号对 Regime 判定的边际贡献 |
| Regime Lag | 实际 Regime 切换点与 MRE 检测到切换之间的延迟 |
| Graceful Degradation | MRE 不可用时下游模块的保守降级运行模式 |
| AB Test | 新旧模型并行运行对比验证的流程 |
