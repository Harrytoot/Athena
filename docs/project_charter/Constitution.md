# Constitution

Athena 项目的最高法律文件。任何决策不得违反本宪法。

---

## Article I — Identity

Athena 是一个 **Digital Investment Partner（数字投资合伙人）**。

具备五种核心能力：Observe → Understand → Reason → Recommend → Learn。

---

## Article II — Trustworthy AI

Athena 追求"最可信"，而非"最聪明"。

1. **每一个建议都必须有依据** — 不能只有分数，必须有理由链
2. **每一个模型都必须可追溯** — 知道数据来源、训练过程、版本
3. **每一次策略调整都必须有实验记录** — Hypothesis → Experiment → Result
4. **每一个版本都必须可以回滚** — Git versioning for everything
5. **每一次自动化决策都必须经过风险控制** — AI → Rule Check → Risk Check → Human

---

## Article III — Documentation First

1. 任何功能开发必须：PRD → Architecture → Review → Implementation
2. 所有架构决策必须记录为 ADR（Architecture Decision Record）
3. 所有文档纳入版本管理
4. 聊天内容不得作为正式需求

---

## Article IV — Architecture Governance

1. 所有模块必须可替换（Plugin Architecture / Provider Pattern）
2. Agent 之间禁止直接调用，必须通过 Event Bus
3. 外部数据源通过 Provider 抽象（Mock → AKShare → Wind，业务零改动）
4. 策略通过 Strategy Marketplace 注册，系统自动发现
5. 任何架构变更必须先写 ADR，获得批准后才能实现

---

## Article V — AI Safety

1. **AI 永远不能直接控制交易**
2. 所有 AI 建议必须经过 Risk Engine 检查
3. 自动交易需要明确的人工确认
4. AI 交易流：Recommendation → Risk Check → Manual Approval → Execution

---

## Article VI — Measurement

1. 核心 KPI：决策质量，不是收益率
2. 包含：决策命中率、风险控制、回撤控制、一致性、稳定性、学习效率
3. 不以"完成多少代码"衡量进度，以"完成多少用户价值闭环"衡量
4. **Measure Everything**: Agent / Strategy / Factor / Model / Prompt 全部量化

系统不仅分析市场，还分析自己。

| 对象 | 指标示例 |
|------|---------|
| Agent | 决策次数、被采纳率、平均贡献收益、最大错误、校准误差 |
| Strategy | 年化收益、夏普、最大回撤、胜率、盈亏比、换手率 |
| Factor | IC、Rank IC、因子衰减、有效周期 |
| Model | AUC、Precision、Recall、Drift |
| Prompt | Token 成本、响应时间、正确率 |

如果不能测量，就不能持续优化。

---

## Article VII — Feature Gate

任何新增功能必须回答三个问题：

1. 它解决什么投资问题？
2. 它如何提升长期收益或降低风险？
3. 它如何与现有模块协作，而不是重复功能？

---

## Article VIII — Repository is Source of Truth

1. Git Repository 为唯一可信来源
2. 所有正式交付物（ADR、PRD、RFC、API、DB、Prompt）进入 Git
3. 任何重要变更必须提交，附带 conventional commit message

---

## Article IX — Evolution

本宪法自身也可以修正，修正流程：

1. 发起 RFC
2. 记录为 ADR
3. Git 提交
4. 更新 Constitution 版本号

---

Version: 1.1.0
Ratified: 2026-06-24
