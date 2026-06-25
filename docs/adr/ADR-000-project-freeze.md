# ADR-000 Project Freeze

## Status

Approved (2026-06-24)

## Decision

### Project Name

**Athena AI Investment Operating System**

简称：Athena。以后所有文档统一使用此名称。

---

## Mission

构建一个持续学习、持续进化、可信、可解释的 AI 投资操作系统，帮助投资者提升**长期决策质量**，而不仅提升短期收益率。

关键词：**长期**、**决策质量**。收益率是结果，不是目标。

---

## Positioning

Athena 不是：

- 股票软件
- 量化交易软件
- 自动交易机器人

Athena 是：**AI Investment Operating System（AI 投资操作系统）**。

### 覆盖完整投资生命周期

```
Observe（观察）
    ↓
Research（研究）
    ↓
Understand（理解）
    ↓
Reason（推演）
    ↓
Decide（决策）
    ↓
Execute（执行）
    ↓
Review（复盘）
    ↓
Learn（学习）
```

---

## 13 Core Principles

### Principle 1: Documentation First
没有文档，不开发。Issue → PRD → Review → Coding。

### Principle 2: Everything Explainable
所有推荐必须解释：为什么推荐/不推荐/今天变化，不能只有 Score。

### Principle 3: Everything Versioned
Prompt、Agent、API、Database、Model、Strategy 全部版本化，可回滚。

### Principle 4: Research Before Trading
研究优先。交易只是研究结果，不是目的。

### Principle 5: Evidence Driven
所有投资建议必须引用：数据、新闻、财报、政策、因子。不能"模型觉得可以买"。

### Principle 6: Human in the Loop
AI 永远只是建议者。只有经过长期模拟验证后才开放自动交易。

### Principle 7: Loose Coupling
所有模块必须可替换。今天 OpenAI → 以后 Qwen，业务零改动。

### Principle 8: Experiment First
所有策略必须经过实验，不能直接上线。

### Principle 9: Knowledge Accumulation
Athena 最大资产不是收益，而是越来越大的知识库。

### Principle 10: Decision Memory
保存所有"为什么"，不是只保存买卖记录。

### Principle 11: Continuous Learning
每天自动学习，每天自动优化。

### Principle 12: Trustworthy AI
宁愿少推荐，不要乱推荐。可信高于聪明。

### Principle 13: Measure Everything（量化一切）

系统不仅分析市场，还分析自己。

| 对象 | 指标示例 |
|------|---------|
| Agent | 决策次数、被采纳率、平均贡献收益、最大错误、平均置信度、校准误差 |
| Strategy | 年化收益、夏普、最大回撤、胜率、盈亏比、换手率、稳定性 |
| Factor | IC、Rank IC、因子衰减、有效周期 |
| Model | AUC、Precision、Recall、Drift |
| Prompt | Token 成本、响应时间、正确率 |

**如果不能测量，就不能持续优化。**

---

## Three-Phase Roadmap

### Phase A: Research OS（研究操作系统）— ~6 months

建立：数据平台、Feature Store、回测平台、因子平台、策略平台、研究中心。

不接券商。

### Phase B: Decision OS（决策操作系统）— ~6 months

增加：Agent、AI、决策引擎、Portfolio Brain、Explainable AI。

仍然人工执行。

### Phase C: Execution OS（执行操作系统）— ~6 months

接券商，支持模拟盘 → 小资金 → 自动执行。

---

## Current Phase

Sprint 1 属于 **Phase A: Research OS** 的 Foundation 阶段。

目标：构建可运行基础平台，完成投资数据闭环（Market → Watchlist → Stock Detail → Portfolio → Recommendation）。

---

## References

- [Constitution](../project-charter/Constitution.md)
- [Vision](../project-charter/Vision.md)
- [AES-001](../aes/AES-001-four-layer-architecture.md)
