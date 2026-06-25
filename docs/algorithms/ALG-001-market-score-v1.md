---
id: ALG-001
title: Market Score V1 — 每日综合市场评分算法
status: Approved
version: 1.0.0
depends: []
---

# ALG-001 Market Score V1

## Objective

输出每日 Market Score（0~100），作为整个 Athena 系统的**唯一市场综合评分**。

Market Score 不直接作出投资决策，而是为所有下游模块提供统一的市场热力上下文：

- Dashboard 的市场温度展示
- Signal Engine 的信号过滤阈值
- Capital Allocation Engine 的仓位上限参考
- Review Module 的逐日绩效归因 baseline

---

## Formula

```
Market Score =
    Trend      × 30% +
    Liquidity  × 25% +
    Breadth    × 20% +
    Volatility × 15% +
    Sentiment  × 10%
```

所有权重固定。V1 禁止自动学习、禁止 AI 调整。所有优化必须基于回测进入 V2。

---

## Sub-Scores

### Trend Score（趋势评分）

**Inputs**

| Signal | Source | Description |
|--------|--------|-------------|
| `CSI300 close` | 指数行情 | 沪深 300 当日收盘价 |
| `CSI300 MA20` | 指数行情 | 20 日均线 |
| `CSI300 MA60` | 指数行情 | 60 日均线 |
| `CSI300 MA120` | 指数行情 | 120 日均线 |
| `MACD.DIF` | 技术指标 | MACD 快线 |
| `MACD.DEA` | 技术指标 | MACD 慢线 |
| `MACD.HIST` | 技术指标 | MACD 柱（DIF - DEA） |

**Scoring Logic**（0~100 分段累加）

| Sub-Components | Condition | Points | Description |
|----------------|-----------|--------|-------------|
| **MA Position** | | **60** | 价格相对均线位置 |
| | Close > MA20 | 20 | |
| | Close > MA60 | 20 | |
| | Close > MA120 | 20 | |
| **MA Alignment** | | **20** | 均线多头排列 |
| | MA20 > MA60 | 7 | |
| | MA20 > MA120 | 7 | 完全多头排列可得满 20 分 |
| | MA60 > MA120 | 6 | |
| **MACD Momentum** | | **20** | 趋势动量确认 |
| | DIF > 0 | 6 | |
| | DIF > DEA | 7 | |
| | HIST > 0 | 4 | |
| | HIST > 前一日 HIST | 3 | 柱线扩张加分 |

**Edge Cases**
- 均线数据不足时（上市 < 120 日），缺失均线对应项计 0 分，其余照常计算。
- MACD 计算失败时，MACD Momentum 整项计 0 分。

---

### Liquidity Score（流动性评分）

**Inputs**

| Signal | Source | Description |
|--------|--------|-------------|
| `market_turnover` | 沪深交易所 | 两市当日成交额（亿元） |
| `turnover_ma20` | 衍生 | 两市成交额 20 日均值 |
| `turnover_percentile_1y` | 衍生 | 成交额在近 1 年中的分位数 |
| `northbound_net` | 沪深港通 | 北向资金当日净流入（亿元） |
| `northbound_ma20` | 衍生 | 北向资金 20 日均值 |
| `margin_balance` | 融资融券 | 融资余额（第二阶段接入） |

**Scoring Logic**（0~100）

| Sub-Components | Condition | Points | Weight |
|----------------|-----------|--------|--------|
| **Turnover** | | | **50%** |
| | `turnover_percentile_1y ≥ 80%` | 50 | |
| | `turnover_percentile_1y ≥ 60%` | 35 | |
| | `turnover_percentile_1y ≥ 40%` | 25 | |
| | `turnover_percentile_1y ≥ 20%` | 15 | |
| | `turnover_percentile_1y < 20%` | 5 | |
| **Northbound** | | | **50%** |
| | `northbound_net > 2 × northbound_ma20` | 50 | |
| | `northbound_net > 1 × northbound_ma20` | 35 | |
| | `northbound_net > 0` | 20 | |
| | `northbound_net ≤ 0` | 5 | |

**Phase 2 扩展**

| Sub-Components | Condition | Points | Weight Redistribution |
|----------------|-----------|--------|----------------------|
| **Margin** | 融资余额周环比 > 2% | 30 | Turnover 40% + Northbound 30% + Margin 30% |

**Edge Cases**
- 北向资金通道关闭日（如假期），Northbound 项按 Turnover 单项归一化（Turnover 权重 100%）。
- 第二阶段融资余额接入后，同样遵循缺失降级原则。

---

### Breadth Score（市场宽度评分）

**Inputs**

| Signal | Source | Description |
|--------|--------|-------------|
| `advance_count` | 沪深交易所 | 上涨家数 |
| `decline_count` | 沪深交易所 | 下跌家数 |
| `advance_ratio` | 衍生 | 上涨家数 / （上涨 + 下跌） |
| `new_high_count` | 行情数据 | 创 60 日新高个股数 |
| `new_high_percentile_1y` | 衍生 | 创新高数在近 1 年中的分位数 |
| `limit_down_count` | 行情数据 | 跌停数量 |

**Scoring Logic**（0~100）

| Sub-Components | Condition | Points | Weight |
|----------------|-----------|--------|--------|
| **Advance Ratio** | | | **40%** |
| | `advance_ratio ≥ 0.60` | 40 | |
| | `advance_ratio ≥ 0.50` | 30 | |
| | `advance_ratio ≥ 0.40` | 20 | |
| | `advance_ratio ≥ 0.30` | 10 | |
| | `advance_ratio < 0.30` | 0 | |
| **New Highs** | | | **30%** |
| | `new_high_percentile_1y ≥ 80%` | 30 | |
| | `new_high_percentile_1y ≥ 60%` | 22 | |
| | `new_high_percentile_1y ≥ 40%` | 15 | |
| | `new_high_percentile_1y ≥ 20%` | 8 | |
| | `new_high_percentile_1y < 20%` | 0 | |
| **Limit Downs** | | | **30%** |
| | `limit_down_count < 10` | 30 | 跌停越少越好 |
| | `limit_down_count < 30` | 20 | |
| | `limit_down_count < 50` | 10 | |
| | `limit_down_count ≥ 50` | 0 | |

**Edge Cases**
- 上涨 + 下跌家数均为 0（交易所停市），Advance Ratio 项计 0 分。
- 历史数据不足 1 年时，创新高分位数用可用历史窗口替代。

---

### Volatility Score（波动率评分）

**核心原则：波动越高，分数越低。**

**Inputs**

| Signal | Source | Description |
|--------|--------|-------------|
| `atr_14` | 技术指标 | 沪深 300 的 14 日 ATR |
| `atr_percentile_1y` | 衍生 | ATR 在近 1 年中的分位数 |
| `daily_amplitude` | 衍生 | 当日振幅（High - Low）/ Prev Close |
| `amplitude_percentile_1y` | 衍生 | 日振幅在近 1 年中的分位数 |
| `volatility_20` | 衍生 | 20 日实现波动率（年化） |
| `volatility_percentile_1y` | 衍生 | 波动率在近 1 年中的分位数 |

**Scoring Logic**（0~100，反向计分）

| Sub-Components | Condition | Points | Weight |
|----------------|-----------|--------|--------|
| **ATR** | | | **40%** |
| | `atr_percentile_1y < 20%` | 40 | 低 ATR → 高分 |
| | `atr_percentile_1y < 40%` | 30 | |
| | `atr_percentile_1y < 60%` | 20 | |
| | `atr_percentile_1y < 80%` | 10 | |
| | `atr_percentile_1y ≥ 80%` | 0 | 高 ATR → 低分 |
| **Amplitude** | | | **30%** |
| | `amplitude_percentile_1y < 20%` | 30 | |
| | `amplitude_percentile_1y < 40%` | 22 | |
| | `amplitude_percentile_1y < 60%` | 15 | |
| | `amplitude_percentile_1y < 80%` | 8 | |
| | `amplitude_percentile_1y ≥ 80%` | 0 | |
| **Volatility** | | | **30%** |
| | `volatility_percentile_1y < 20%` | 30 | |
| | `volatility_percentile_1y < 40%` | 22 | |
| | `volatility_percentile_1y < 60%` | 15 | |
| | `volatility_percentile_1y < 80%` | 8 | |
| | `volatility_percentile_1y ≥ 80%` | 0 | |

**Edge Cases**
- 次新股或历史数据不足时，使用可用窗口按比例缩放到 0~100。

---

### Sentiment Score（情绪评分）

**Inputs**

| Signal | Source | Description |
|--------|--------|-------------|
| `limit_up_count` | 行情数据 | 涨停数量 |
| `break_board_count` | 行情数据 | 炸板数量（触及涨停后开板） |
| `hit_board_count` | 衍生 | 触及涨停总数 = 涨停 + 炸板 |
| `break_board_rate` | 衍生 | 炸板率 = 炸板数 / 触及涨停总数 |
| `max_consecutive_board` | 行情数据 | 当日最高连板高度 |

**Scoring Logic**（0~100）

| Sub-Components | Condition | Points | Weight |
|----------------|-----------|--------|--------|
| **Limit Ups** | | | **40%** |
| | `limit_up_count ≥ 100` | 40 | |
| | `limit_up_count ≥ 70` | 30 | |
| | `limit_up_count ≥ 40` | 20 | |
| | `limit_up_count ≥ 20` | 10 | |
| | `limit_up_count < 20` | 0 | |
| **Break Board Rate** | | | **30%** |
| | `break_board_rate < 15%` | 30 | 低炸板率 = 高情绪 |
| | `break_board_rate < 25%` | 22 | |
| | `break_board_rate < 35%` | 15 | |
| | `break_board_rate < 50%` | 8 | |
| | `break_board_rate ≥ 50%` | 0 | |
| **Consecutive Board** | | | **30%** |
| | `max_consecutive_board ≥ 7` | 30 | |
| | `max_consecutive_board ≥ 5` | 22 | |
| | `max_consecutive_board ≥ 3` | 15 | |
| | `max_consecutive_board ≥ 1` | 8 | |
| | `max_consecutive_board = 0` | 0 | |

**Edge Cases**
- 涨停数为 0 时，炸板率无法计算，Break Board Rate 项计 0 分。
- `hit_board_count = 0` 时，`break_board_rate` 定义为 0（无板可炸）。

---

## Market State（市场状态分级）

| Score Range | State | Description |
|-------------|-------|-------------|
| 0 ~ 19 | **Extreme Bear** | 极端熊市，全面防御 |
| 20 ~ 39 | **Bear** | 熊市，谨慎为主 |
| 40 ~ 59 | **Neutral** | 中性，无明显方向 |
| 60 ~ 79 | **Bull** | 牛市，积极可为 |
| 80 ~ 100 | **Strong Bull** | 强势牛市，全面进攻 |

---

## API

### GET /api/v1/market/score

**Query Parameters**: 无

**Response**（200）

```json
{
    "date": "2026-06-25",
    "score": 72,
    "trend": 81,
    "liquidity": 69,
    "breadth": 75,
    "volatility": 58,
    "sentiment": 64,
    "state": "Bull",
    "metadata": {
        "version": "1.0.0",
        "generated_at": "2026-06-25T15:30:00+08:00",
        "data_freshness": {
            "market_data": "2026-06-25T15:00:00+08:00",
            "northbound": "2026-06-25T15:00:00+08:00"
        }
    }
}
```

**Response Schema**

| Field | Type | Description |
|-------|------|-------------|
| `date` | string | 评分日期（YYYY-MM-DD） |
| `score` | int | Market Score（0~100） |
| `trend` | int | Trend 子分（0~100） |
| `liquidity` | int | Liquidity 子分（0~100） |
| `breadth` | int | Breadth 子分（0~100） |
| `volatility` | int | Volatility 子分（0~100） |
| `sentiment` | int | Sentiment 子分（0~100） |
| `state` | string | Market State 枚举值 |
| `metadata.version` | string | 算法版本号 |
| `metadata.generated_at` | datetime | 评分生成时间 |
| `metadata.data_freshness` | object | 各项数据的最新时间戳 |

**Error Responses**

| Status | Code | Description |
|--------|------|-------------|
| 503 | `MARKET_DATA_UNAVAILABLE` | 核心数据源不可用，评分无法生成 |

---

## Computed Columns（数据库存储）

| Column | Type | Description |
|--------|------|-------------|
| `score` | SMALLINT | Market Score（0~100） |
| `score_trend` | SMALLINT | Trend 子分 |
| `score_liquidity` | SMALLINT | Liquidity 子分 |
| `score_breadth` | SMALLINT | Breadth 子分 |
| `score_volatility` | SMALLINT | Volatility 子分 |
| `score_sentiment` | SMALLINT | Sentiment 子分 |
| `state` | VARCHAR(20) | Market State 枚举 |
| `date` | DATE | 评分日期（PK） |
| `generated_at` | TIMESTAMPTZ | 生成时间 |
| `version` | VARCHAR(16) | 算法版本 |

---

## Constraints

### V1 硬约束

1. **权重固定**：`[30%, 25%, 20%, 15%, 10%]` 不可在运行时调整。
2. **禁止自动学习**：任何基于历史数据自动调参的行为均禁止。
3. **禁止 AI 参与评分计算**：不接受 LLM 输出作为输入信号源。
4. **全部子分必须可解释**：每个子分的原始输入值和中间计算步骤须可追溯。

### 数据质量约束

| Condition | Action |
|-----------|--------|
| 任一子分所需数据缺失 ≥ 50% | 该子分标记为 `null`，总分为剩余子分按权重归一化 |
| Trend 子分数据缺失 | 总分不可计算，返回 503 |
| 北向资金通道关闭（节假日） | Northbound 项降级处理（见 Edge Cases） |

### 变更管理

| 变更类型 | 审批 | 流程 |
|---------|------|------|
| 权重调整 | Chief Architect | 回测验证 + ADR |
| 新增输入信号 | Chief Architect | ADR |
| 修改评分阈值 | Chief Architect | 回测验证 + PR |
| 修改 API Schema | Chief Architect | RFC（Breaking Change 需版本号） |

---

## Evolution Path

| Phase | Scope | Trigger |
|-------|-------|---------|
| **V1**（当前） | 固定权重规则引擎 | Sprint 1 |
| **V2** | 权重回测优化 + 融资余额接入 | 基于 V1 回测结果 |
| **V3** | 动态权重（基于 Regime 切换） | 依赖 MRE 成熟度 |
| **V4** | 引入 ML 评分校准层 | 规则引擎 + ML 混合 |

---

## Testing

### 单元测试

- 每个子分计算函数必须独立可测，覆盖率 ≥ 90%。
- 测试用例覆盖所有边界条件（满分、零分、数据缺失、阈值边界）。

### 回测验证

V1 上线前必须完成：

| 测试项 | 要求 |
|--------|------|
| 历史回测 | ≥ 3 年日频数据 |
| 市场状态分布 | 5 种状态均有样本（允许 Extreme Bear 样本较少） |
| 极端事件覆盖 | 至少覆盖 1 次重大下跌（如 2024-02）和 1 次快速上涨 |
| 与沪深 300 收益相关性 | Spearman ρ ≥ 0.4 |

### 集成测试

- API 响应 schema 符合约定
- 数据源降级场景覆盖
- 日频调度成功生成（模拟过去 1 个月每日触发）

---

## References

| 文档 | 关系 |
|------|------|
| [INV-ARCH-003](../investment/INV-ARCH-003-market-regime-engine.md) | 上游：Market Regime Engine，V3 将消费 Market Score |
| [API-001](../api/API-001-sprint-1-baseline.md) | API 规范遵循 Sprint 1 基线 |
| [DB-001](../database/DB-001-sprint-1-baseline.md) | 数据库设计遵循 Sprint 1 基线 |
| [AMS-001](../ams/AMS-001-master-specification.md) | 主规格说明书 |
| [RFC-001](../rfc/RFC-001-sprint-1-foundation-development-plan.md) | Sprint 1 开发计划 |

---

## Open Questions

1. 是否需要在 V1 中增加"极端单边市"的特别处理逻辑（如熔断、涨跌停限制导致的成交额失真）？
2. 融资余额数据源的接入时间线是否影响 Liquidity 评分 V1 的完整性？
3. Trend Score 中的 MACD 参数（12/26/9）是否固定，还是允许配置？
4. 是否需要引入 CSI1000 或其他宽基指数作为 Breadth 的辅助参考？
5. 分位数计算的滚动窗口（1 年）在牛熊切换期是否有滞后问题，是否需要自适应窗口？
