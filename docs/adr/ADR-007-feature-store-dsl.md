# ADR-007 Feature Store & Investment DSL

## Status

Approved (2026-06-24)

## Decision 1 — Feature Store（特征仓升级）

### 以前
指标（Indicator）：MA5, RSI, MACD — 分散在各处

### 现在
Feature（特征）：统一管理，所有策略/Agent/模型共享

```
feature_store/
├── technical/
│   ├── trend_slope_20       # 20日趋势斜率
│   ├── volatility_20        # 20日波动率
│   └── volume_ratio         # 量比
├── fundamental/
│   ├── roe_ttm              # 净资产收益率
│   ├── pe_percentile        # PE 历史分位
│   └── earnings_surprise    # 盈利超预期
├── money_flow/
│   ├── northbound_rank      # 北向资金排名
│   ├── main_force_direction # 主力方向
│   └── sector_rotation      # 行业轮动信号
├── policy/
│   ├── policy_score         # 政策支持评分
│   └── policy_momentum      # 政策动量
├── sentiment/
│   ├── sentiment_score      # 情绪评分
│   └── news_impact          # 新闻影响
└── market/
    ├── breadth_ratio        # 市场宽度
    ├── temperature          # 市场温度
    └── regime_probability   # 市场状态概率
```

### 原则

- 一个 Feature = 一个计算函数 + 元数据
- 所有 Feature 有版本，可追溯
- 所有 Feature 有 IC 评估
- Feature 之间不重复

## Decision 2 — Investment DSL（投资领域语言）

### 语法

```
WHEN Market.Regime == BULL
  AND Feature("policy_score") > 80
  AND Feature("sector_rotation", sector="机器人") > 70
THEN
  ALLOCATE 8% TO Stock("300124.SZ")
  STOP_LOSS = 6%

WHEN Market.Regime == BEAR
  AND Feature("sentiment_score") < 30
THEN
  REDUCE Exposure TO 30%
```

### 编译链

```
Athena DSL → Compiler → Feature Calls + Capability Calls → Execution Plan
```

### 使用场景

| 场景 | 方式 |
|------|------|
| 人写策略 | 直接写 DSL |
| AI 生成策略 | AI 输出 DSL |
| 策略回测 | DSL → Backtest Engine |
| 策略比较 | DSL diff |
| 策略版本 | Git 管理 DSL 文件 |

## Implementation

Sprint 2+ 实现。Sprint 1 仅设计冻结。

## References

- [ADR-006 Architecture Corrections](ADR-006-architecture-corrections.md)
- [AES-002 AI Architecture](../aes/AES-002-ai-architecture.md)
