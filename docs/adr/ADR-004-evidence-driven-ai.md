# ADR-004 Evidence-Driven AI, Probability & Confidence Standards

## Status

Approved (2026-06-24)

## Decision

### 1. Document System Standardization

所有正式文档采用国际软件工程规范：RFC + ADR + PRD，而非 Word 文档。

文档体系已在 `docs/` 下建立，任何重大设计进入 RFC，确认后沉淀为 ADR。

### 2. Evidence Driven（证据驱动）

Athena 不做规则驱动（如 MACD 金叉 → 买入），而做证据驱动。

每条建议必须附带：

- 各维度证据强度（技术/资金/基本面/情绪/政策/风险）
- 支持证据列表
- 反对证据列表
- 证据冲突分析
- 综合信心度

这形成 **Evidence Graph（证据图谱）**，而非简单指标叠加。

### 3. Predict Probability, Not Price

Athena 不预测价格。预测价格意义极低。

Athena 预测：

- 上涨概率
- 下跌风险
- 未来波动范围
- 适合交易风格
- 不适合的交易风格

### 4. All AI Output Must Have Confidence

所有 Agent 输出统一格式：

```
Action: Buy/Hold/Sell
Confidence: 0-100
Reason: [3-5 条证据]
Uncertainty: [不确定因素]
Need More Data: [缺失数据]
```

### 5. "I Don't Know" Capability

Athena 必须具有"不知道"的能力：

- 数据不足 → 建议等待
- 信号冲突 → 建议空仓
- 没有机会 → 不推荐

禁止硬回答或强行推荐。

## Consequences

- Constitution updated to v2.0.0 (Articles X-XIII)
- All future AI outputs must follow Confidence format
- All future recommendations must include Evidence Graph
- "不知道"是合法输出

## References

- [Constitution v2.0.0](../project-charter/Constitution.md)
- [ADR-000 Project Freeze](ADR-000-project-freeze.md)
- [ADR-003 Core Principles](ADR-003-core-principles.md)
