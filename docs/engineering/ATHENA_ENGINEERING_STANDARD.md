# Athena Engineering Standard v1.0

## Status

Ratified (2026-06-24)

## Role

本文件是 Athena 项目的**工程规范宪法**。

所有代码、数据库、API、Prompt、Agent、UI、日志、配置必须遵守本标准。不得有例外。

---

# Part 1 — Athena Language (ATHL)

## Principle

Athena 所有层级使用统一英文术语，禁止中英混杂、同义词混用。

## 1.1 Market States

| 术语 | 含义 | 禁止 |
|------|------|------|
| `BULL` | 牛市 | 不用 Bull, Trend, 上涨, Uptrend |
| `BEAR` | 熊市 | 不用 Bear, 下跌, Downtrend |
| `RANGE` | 震荡 | 不用 Sideways, Consolidation, 盘整 |
| `VOLATILE` | 高波动 | 不用 Volatility, 剧烈波动 |

## 1.2 Actions

| 术语 | 含义 | 禁止 |
|------|------|------|
| `BUY` | 买入 | 不用 Long, 做多, 建仓 |
| `SELL` | 卖出 | 不用 Short, 做空, 平仓 |
| `HOLD` | 持有 | 不用 Keep, 持仓不动 |
| `REDUCE` | 减仓 | 不用 Partial Sell |

## 1.3 Core Concepts

| 术语 | 含义 | 禁止 |
|------|------|------|
| `Recommendation` | 建议 | 不用 Signal, Alert, Tip, 信号 |
| `Allocation` | 仓位/配置 | 不用 Position(歧义), Weight(混淆) |
| `Confidence` | 置信度 0-100 | 不用 Score, Probability |
| `Evidence` | 证据 | 不用 Reason(仅是证据的一部分) |
| `Portfolio` | 投资组合 | 不用 Account, Fund |
| `Position` | 持仓(具体股票) | 不用 Holding |
| `Exposure` | 总敞口 % | 不用 TotalWeight |
| `Regime` | 市场状态 | 不用 State, Condition |
| `Capability` | 系统能力 | 不用 Function, Feature |
| `Provider` | 数据源 | 不用 Adapter, Connector, Source |

## 1.4 Direction

| 术语 | 含义 | 禁止 |
|------|------|------|
| `Bullish` | 看多 | 不用 Positive, Up |
| `Bearish` | 看空 | 不用 Negative, Down |
| `Neutral` | 中性 | 不用 Flat, Sideways |

---

# Part 2 — Athena Vocabulary（官方词典）

## 2.1 Portfolio & Trading

| 术语 | 精确定义 |
|------|---------|
| **Portfolio** | 一个投资者的完整资产集合，包含现金、持仓、历史交易 |
| **Position** | 对单一标的的持仓，包含成本、数量、当前市值、浮盈亏 |
| **Allocation** | 对 Portfolio 中某个资产的目标配置比例 |
| **Exposure** | Portfolio 的总市场敞口 (仓位) 百分比 |
| **Cash** | Portfolio 中未投资的现金余额 |
| **PnL** | Profit and Loss — 持仓的浮动盈亏 |
| **Order** | 一笔待执行或已执行的交易指令 |

## 2.2 Market & Analysis

| 术语 | 精确定义 |
|------|---------|
| **Regime** | 市场所处的状态模式 (BULL/BEAR/RANGE/VOLATILE) |
| **Breadth** | 市场宽度 — 上涨/下跌股票的数量比例 |
| **Liquidity** | 流动性 — 市场交易活跃程度 |
| **Sentiment** | 市场情绪 — 投资者的整体乐观/悲观程度 |
| **Turnover** | 成交额 — 某一时段的交易金额 |
| **Northbound** | 北向资金 — 通过沪/深港通流入 A 股的外资 |
| **Sector** | 行业 — 按经济职能分类的公司群组 |
| **Theme** | 主题/概念 — 跨行业的公司群组 |
| **Rotation** | 轮动 — 资金从一类资产流向另一类资产 |

## 2.3 Strategy & Signal

| 术语 | 精确定义 |
|------|---------|
| **Strategy** | 一组系统化的投资规则 |
| **Factor** | 可量化的、与收益相关的特征 |
| **Signal** | 策略产生的具体操作指令 |
| **Rule** | 策略中的单一条件判断 |
| **Score** | 因子/策略对标的的综合评价数值 |
| **Recommendation** | 综合多个 Signal 和 Evidence 后对用户的最终建议 |

## 2.4 Risk

| 术语 | 精确定义 |
|------|---------|
| **Drawdown** | 从最高点到当前点的回撤幅度 |
| **VaR** | Value at Risk — 在给定置信度下的最大可能损失 |
| **Exposure** | 风险敞口 |
| **Concentration** | 持仓集中度 |
| **Correlation** | 资产间相关性 |
| **Tail Risk** | 极端事件风险 |

## 2.5 AI & Agent

| 术语 | 精确定义 |
|------|---------|
| **Agent** | 独立 AI 分析单元，负责特定领域的感知/分析/推理 |
| **Capability** | Agent 对外暴露的单一能力接口 |
| **Prompt** | 发送给 LLM 的完整输入模板 |
| **Context** | 注入 Prompt 的运行时上下文数据 |
| **Confidence** | AI 对自身输出的信心程度 (0-100) |
| **Evidence** | 支持或反对某个结论的可量化数据点 |
| **Reason** | 基于 Evidence 的推理链路 |
| **Uncertainty** | 结论中无法确定的部分 |

---

# Part 3 — Style Guide（编码规范）

## 3.1 API Naming

| 规则 | 示例 | 禁止 |
|------|------|------|
| RESTful, 名词复数 | `GET /v1/markets` | `GET /getMarket` |
| 嵌套资源 | `GET /v1/watchlists/{id}/items` | `GET /v1/watchlistItems?watchlist_id=` |
| kebab-case URL | `/market-overview` | `/marketOverview` |
| camelCase JSON | `{ "marketRegime": "BULL" }` | `{ "market_regime": "BULL" }` |
| 查询用 query string | `?q=keyword&limit=20` | URL path params |

## 3.2 Database Naming

| 规则 | 示例 | 禁止 |
|------|------|------|
| snake_case 表名 | `watchlist_items` | `WatchlistItems`, `watchlistItems` |
| snake_case 列名 | `created_at` | `createdAt` |
| 外键: `{table}_id` | `watchlist_id` | `watchlistId`, `wl_id` |
| 时间戳: `_at` | `updated_at` | `update_time` |
| 布尔: `is_` | `is_active` | `active` |

## 3.3 Python Naming

| 规则 | 示例 |
|------|------|
| PEP8 | 100 chars/line |
| snake_case 变量/函数 | `get_market_overview` |
| PascalCase 类名 | `MarketService` |
| UPPER_CASE 常量 | `DEFAULT_USER_ID` |
| 类型提示: 所有公开函数 | `def foo(x: int) -> str:` |

## 3.4 TypeScript Naming

| 规则 | 示例 |
|------|------|
| camelCase 变量/函数 | `getMarketOverview` |
| PascalCase 组件 | `IndexCard` |
| PascalCase 接口 | `MarketOverview` |
| kebab-case 文件 | `index-card.tsx` |

## 3.5 Prompt Naming

| 规则 | 示例 |
|------|------|
| Markdown 格式 | system/user/assistant 分离 |
| 文件名: `{agent}_{capability}_v{version}.md` | `market_analyze_regime_v1.2.md` |
| 变量: `{{variable}}` | `{{market_data}}` |

## 3.6 Agent Naming

| 角色 | 命名格式 | 示例 |
|------|---------|------|
| Analyzer | `{Domain}Analyzer` | `MarketAnalyzer`, `CompanyAnalyzer` |
| Planner | `{Domain}Planner` | `PortfolioPlanner` |
| Evaluator | `{Domain}Evaluator` | `RiskEvaluator` |
| Researcher | `{Domain}Researcher` | `IndustryResearcher` |
| Executor | `{Domain}Executor` | `TradeExecutor` |
| Reviewer | `{Domain}Reviewer` | `DecisionReviewer` |
| Learner | `{Domain}Learner` | `StrategyLearner` |

## 3.7 Event Naming

| 规则 | 示例 |
|------|------|
| `{Subject}{Verb}Event` (Past Tense) | `MarketRegimeChangedEvent` |
| 包含时间戳 | `occurred_at: ISO 8601` |
| 包含来源 | `source: AgentName` |

## 3.8 Logging

| 规则 | 示例 |
|------|------|
| 统一 JSON 格式 | `{"level":"INFO","agent":"MarketAnalyzer",...}` |
| 包含 trace_id | 全链路追踪 |
| 包含 agent | 标识来源 Agent |

---

# Part 4 — Investment Ontology（投资本体）

## 4.1 Capital Flow（资金分类）

```
CapitalFlow
├── Retail           # 散户资金
├── Institution      # 机构资金
├── Northbound       # 北向（外资→A股）
├── Southbound       # 南向（内地→港股）
├── ETF              # ETF 资金流
├── Quant            # 量化资金
└── Margin           # 融资融券
```

## 4.2 Industry（行业分类）

```
Industry
├── Level1 (Sector)  # 一级行业: 金融/科技/消费/医药/制造/能源/材料/公用
├── Level2 (Industry)# 二级行业: 银行/半导体/白酒/创新药
├── Theme            # 主题: 新能源/AI/机器人/低空经济
└── Concept          # 概念: 光刻机/液冷/CPO
```

## 4.3 Market Indicators（市场指标）

```
MarketIndicator
├── Breadth          # 宽度: advance/decline ratio
├── Temperature      # 温度: 0-100 综合评分
├── Liquidity        # 流动性: 成交量/换手率
├── Volatility       # 波动率: 历史/隐含
├── Sentiment        # 情绪: 综合情绪指标
└── Concentration    # 集中度: 前N只股票成交占比
```

---

# Part 5 — Decision Ontology（决策本体）

## Recommendation Object

```json
{
  "action": "BUY",
  "symbol": "600519.SH",
  "confidence": 82,
  "evidence": {
    "technical": { "score": 4.2, "signals": ["MA多头排列", "RSI超卖反弹"] },
    "fundamental": { "score": 3.8, "signals": ["ROE>20%", "现金流充裕"] },
    "money_flow": { "score": 4.5, "signals": ["北向连续流入", "主力净买入"] },
    "policy": { "score": 3.0, "signals": ["消费刺激预期"] },
    "sentiment": { "score": 3.5, "signals": ["分析师上调"] }
  },
  "risk": {
    "market_risk": "LOW",
    "liquidity_risk": "LOW",
    "company_risk": "LOW",
    "policy_risk": "MEDIUM",
    "valuation_risk": "MEDIUM",
    "overall": "MEDIUM"
  },
  "reason": [
    "北向资金连续5日净买入",
    "ROE连续3年>20%",
    "PE处于历史30分位，估值合理"
  ],
  "alternative": "HOLD if market regime becomes RANGE",
  "expire_at": "2026-06-25T15:00:00+08:00"
}
```

---

# Part 6 — Risk Ontology（风险树）

```
Risk
├── MarketRisk           # 市场风险
│   ├── SystemicRisk     #   系统性
│   ├── RegimeRisk       #   状态切换
│   └── EventRisk        #   黑天鹅
├── LiquidityRisk        # 流动性风险
│   ├── BidAskSpread     #   买卖价差
│   └── MarketDepth      #   市场深度
├── CompanyRisk          # 公司风险
│   ├── FinancialRisk    #   财务风险
│   ├── ManagementRisk   #   管理风险
│   └── CompetitiveRisk  #   竞争风险
├── PolicyRisk           # 政策风险
│   ├── RegulatoryRisk   #   监管风险
│   └── FiscalRisk       #   财政/货币风险
├── ValuationRisk        # 估值风险
│   ├── ExpensiveRisk    #   高估风险
│   └── BubbleRisk       #   泡沫风险
├── ExecutionRisk        # 执行风险
│   ├── SlippageRisk     #   滑点
│   └── TimingRisk       #   时机
├── ModelRisk            # 模型风险
│   ├── Overfitting      #   过拟合
│   └── DriftRisk        #   漂移
├── DataRisk             # 数据风险
│   ├── QualityRisk      #   数据质量
│   └── LatencyRisk      #   延迟
└── AIRisk               # AI 风险
    ├── Hallucination    #   幻觉
    └── CalibrationError #   校准误差
```

---

# Part 7 — Feature Ontology（特征本体）

```
Feature
├── Technical            # 技术面
│   ├── Trend (趋势)     # MA, MACD, Slope
│   ├── Momentum (动量)  # RSI, KDJ, ROC
│   ├── Volatility (波动)# ATR, Bollinger, HV
│   └── Volume (量能)    # OBV, VolumeRatio, MFI
├── Fundamental          # 基本面
│   ├── Profitability    # ROE, ROIC, 利润率
│   ├── Growth           # 收入/利润增长率
│   ├── Value            # PE, PB, PS, EV/EBITDA
│   └── Quality          # 负债率, 现金流, 分红
├── MoneyFlow            # 资金面
│   ├── Direction        # 流向方向
│   ├── Strength         # 流入强度
│   └── Persistence      # 持续性
├── Policy               # 政策面
│   ├── SupportScore     # 支持力度
│   └── ImpactLevel      # 影响级别
├── Macro                # 宏观面
│   ├── EconomicCycle    # 经济周期
│   ├── InterestRate     # 利率环境
│   └── CreditSpread     # 信用利差
├── Alternative          # 另类
│   ├── SupplyChain      # 产业链数据
│   ├── Satellite        # 卫星数据
│   └── SocialMedia      # 社交媒体
└── LLM                  # LLM 特征
    ├── SentimentScore   # 情绪评分
    └── NarrativeStrength# 叙事强度
```

---

# Part 8 — Strategy Ontology（策略分类）

```
Strategy
├── Trend Following      # 趋势跟踪
│   ├── MovingAverage    #   均线系统
│   └── Breakout         #   突破策略
├── Mean Reversion       # 均值回归
│   ├── Statistical      #   统计套利
│   └── PairsTrading     #   配对交易
├── Momentum             # 动量策略
│   ├── PriceMomentum    #   价格动量
│   └── EarningsMomentum #   盈利动量
├── Value                # 价值策略
│   ├── DeepValue        #   深度价值
│   └── GARP             #   合理价格增长
├── Event Driven         # 事件驱动
│   ├── PolicyCatalyst   #   政策催化
│   └── EarningsSurprise #   盈利惊喜
├── Factor Based         # 多因子
│   ├── MultiFactor      #   多因子合成
│   └── RiskParity       #   风险平价
├── Allocation           # 资产配置
│   ├── StrategicAlloc   #   战略配置
│   └── TacticalAlloc    #   战术配置
└── ML/AI                # ML/AI 策略
    ├── PredictionModel   #   预测模型
    └── Reinforcement    #   强化学习
```

---

# Part 9 — Agent Taxonomy（Agent 分类）

| 角色 | 职责 | 输入 | 输出 |
|------|------|------|------|
| **Analyzer** | 分析特定领域数据 | Raw Data | Analysis + Confidence |
| **Planner** | 生成行动方案 | Analysis | Plan + Alternatives |
| **Evaluator** | 评估方案和风险 | Plan | RiskScore + Concerns |
| **Researcher** | 深入研究 | Topic/Query | Research Report |
| **Executor** | 执行已批准方案 | Approved Plan | Execution Record |
| **Reviewer** | 复盘和评估 | Execution Record | Review Report |
| **Learner** | 学习并更新模型 | Review Report | Model Update |

---

# Part 10 — Capability Taxonomy

```
Capability
├── AnalyzeMarket        # 分析市场状态
│   ├── GetRegime        #   判断市场状态
│   ├── GetBreadth       #   计算市场宽度
│   ├── GetTemperature   #   计算市场温度
│   └── GetRotation      #   分析行业轮动
├── AnalyzeCompany       # 分析公司
│   ├── EvaluateQuality  #   评估质量
│   ├── ValuatePrice     #   估值分析
│   └── AnalyzeRisk      #   风险分析
├── GenerateSignal       # 生成信号
│   ├── FactorSignal     #   因子信号
│   └── RuleSignal       #   规则信号
├── AllocatePortfolio    # 组合配置
│   ├── OptimizeWeight   #   权重优化
│   └── Rebalance        #   再平衡
├── RunBacktest          # 运行回测
│   ├── SingleStrategy   #   单策略回测
│   └── MultiStrategy    #   多策略对比
├── GenerateReport       # 生成报告
│   ├── DailyBrief       #   每日简报
│   └── PerformanceReport#   业绩报告
├── EvaluateRisk         # 评估风险
│   ├── PositionRisk     #   持仓风险
│   └── ScenarioRisk     #   情景风险
├── ExecuteTrade         # 执行交易
│   ├── GenerateOrder    #   生成订单
│   └── ConfirmOrder     #   确认订单
├── ResearchIndustry     # 行业研究
│   ├── ValueChain       #   产业链分析
│   └── PeerComparison   #   同行对比
└── ManageKnowledge      # 知识管理
    ├── UpdateGraph      #   更新知识图谱
    └── RecordDecision   #   记录决策
```

---

## Version

1.0.0

## Maintained By

Chief Architect + Documentation Engineer
