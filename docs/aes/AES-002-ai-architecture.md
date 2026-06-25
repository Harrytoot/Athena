# AES-002 AI Architecture — MCP, Capability-First, Knowledge Graph, Simulation, Prompt, DSL

## Status

Approved (2026-06-24)

## Scope

Sprint 2+ (当前 Sprint 1 不实现，仅设计冻结)

---

## 1. MCP（Model Context Protocol）

### 原则

Athena 所有 AI 模块采用 MCP 思想：

- **上下文管理** — 统一管理 Agent 的上下文窗口
- **知识调用** — 通过 Knowledge Graph 检索相关实体
- **工具调用** — Capability 作为 Tool 注册

### 架构

```
Agent
  ├── MCP Context Manager → 管理对话/检索上下文
  ├── MCP Knowledge → Knowledge Graph 检索
  └── MCP Tools → Capability Registry
```

---

## 2. Capability First（能力优先）

### 原则

Athena 不以 Agent 为中心，以 **Capability（能力）** 为中心。

❌ Agent First:
```
MarketAgent → 所有市场相关功能写死在 Agent 里
```

✅ Capability First:
```
Capability:
  GetMarketBreadth
  GetIndustryRotation
  GetPolicyTrend
  GetNorthboundFlow
  GeneratePortfolio
  EvaluateStrategy

Agent → 调用 Capability
```

**Agent 换 → Capability 不动 → 企业级设计。**

### Capability Registry

```
CapabilityRegistry
├── market/
│   ├── get_breadth
│   ├── get_rotation
│   ├── get_temperature
│   └── get_money_flow
├── portfolio/
│   ├── generate_allocation
│   ├── evaluate_risk
│   └── calculate_pnl
├── research/
│   ├── analyze_industry
│   ├── evaluate_company
│   └── compare_peers
└── decision/
    ├── collect_evidence
    ├── compute_confidence
    └── generate_recommendation
```

---

## 3. Investment Knowledge Graph（投资知识图谱）

### 原则

不是数据库，是真正的知识图谱。

### 实体关系模型

```
Industry（行业）
├── belongs_to → Sector（板块）
├── contains → SubIndustry（子行业）

Company（公司）
├── belongs_to → Industry
├── supplier_of → Company
├── customer_of → Company
├── competitor_of → Company
├── held_by → Fund
├── recommended_by → Analyst

Policy（政策）
├── affects → Industry
├── affects → Company
├── issued_by → Government

Product（产品）
├── produced_by → Company
├── uses_technology → Technology
├── belongs_to → SupplyChain

Fund（基金）
├── holds → Company
├── managed_by → Manager
├── belongs_to → Strategy
```

### 推理能力

```
政策发布 "机器人+" 
→ 推理: 利好机器人行业
→ 推理: 减速器是机器人核心零部件
→ 推理: 绿的谐波是减速器龙头
→ 推理: 绿的谐波的客户包括埃斯顿
→ 推理: 机器人ETF可能受益
→ 推荐: 关注绿的谐波、埃斯顿、机器人ETF
```

---

## 4. Simulation Layer（模拟层）

### 原则

所有策略/AI/Agent 不能直接影响真实世界。

```
AI Suggestion
    ↓
Simulation（模拟1年历史）
    ↓
通过？
    ↓
Paper Trading（模拟盘运行）
    ↓
通过？
    ↓
Small Capital（小资金验证）
    ↓
通过？
    ↓
Production（正式上线）
```

### Simulation Metrics

| 阶段 | 验证内容 | 周期 |
|------|---------|------|
| Simulation | 历史数据回溯 | 1年 |
| Paper Trading | 实时数据模拟盘 | 1-3个月 |
| Small Capital | 真实资金小规模 | 3-6个月 |
| Production | 正式上线 | — |

---

## 5. Prompt Engineering — Prompt as Code

### 原则

Prompt 不是字符串，是对象。

### Prompt 对象格式

```yaml
prompt:
  id: "market_regime_analyzer"
  version: "1.2"
  author: "Chief Architect"
  reviewer: "QA"
  created: "2026-06-24"
  model: "deepseek-v3"
  temperature: 0.3
  max_tokens: 2000
  system_prompt: |
    You are a market regime analyst...
  expected_output:
    format: "json"
    schema: "MarketRegimeOutput"
  evaluation:
    accuracy_threshold: 0.85
    test_cases: 50
  cost:
    avg_tokens: 1500
    avg_cost_usd: 0.002
  version_history:
    - version: "1.0" changelog: "Initial version"
    - version: "1.1" changelog: "Added volatility dimension"
    - version: "1.2" changelog: "Tuned temperature"
```

### Prompt 版本管理

```
prompts/
├── market_regime_analyzer/
│   ├── v1.0.yaml
│   ├── v1.1.yaml
│   └── v1.2.yaml
├── stock_evaluator/
├── risk_assessor/
└── report_generator/
```

Prompt 纳入 Git，有 changelog，有测试用例，有成本监控。

---

## 6. Athena DSL（领域特定语言）

### 愿景

让投资策略的编写从 Python 代码升级为 Domain Language。

### 语法示例

```
WHEN Market.Regime == BULL
  AND MoneyFlow("机器人") > 80
  AND Sector("机器人").Rank <= 3
  AND Sentiment.Score > 0.75
THEN
  ALLOCATE 15% TO Sector("机器人")
  CONFIDENCE > 0.8

WHEN Stock("600519.SH").PE < HistoricalPE(0.3)
  AND Stock("600519.SH").NorthboundFlow > 100
  AND Market.Volatility < 30
THEN
  BUY Stock("600519.SH") Weight=10%
  STOP_LOSS = -8%
```

### DSL 编译

```
Athena DSL → Compiler → Python + Capability Calls → Execution
```

### 目标

- 策略可读、可审计、可版本比较
- 非程序员可以理解投资逻辑
- AI 可以生成和优化 DSL 策略

---

## References

- [AMS-001](../ams/AMS-001-master-specification.md)
- [Constitution v2.0.0](../project-charter/Constitution.md)
- [ADR-003 Core Principles](../adr/ADR-003-core-principles.md)
- [ADR-005 Enterprise R&D Process](../adr/ADR-005-enterprise-rd-process.md)
