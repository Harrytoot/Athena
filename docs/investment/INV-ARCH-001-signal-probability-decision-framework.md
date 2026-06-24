---
id: INV-ARCH-001
title: Signal → Probability → Decision Framework
classification: S
status: Approved
version: 1.0.0
owner: Chief Architect
reviewer: Founder
board: Investment Board
---

# Purpose

定义 Athena 投资智能系统的核心决策架构。

Athena 不直接基于指标进行交易，而是通过"信号 → 概率 → 决策"的统一流程完成投资决策。

---

# Core Pipeline

Data
↓
Information
↓
Signal
↓
Probability
↓
Decision
↓
Execution
↓
Review
↓
Knowledge

---

# Signal Categories

所有信号必须归属于以下类别之一：

- Macro Signal
- Market Signal
- Liquidity Signal
- Capital Flow Signal
- Fundamental Signal
- Valuation Signal
- Technical Signal
- Sentiment Signal
- Policy Signal
- Event Signal

禁止直接使用孤立指标作为交易依据。

---

# Signal Model

每个 Signal 必须包含以下标准属性：

- Direction（方向）
- Strength（强度）
- Confidence（可信度）
- Decay（有效期）
- Source（数据来源）
- Update Frequency（更新频率）

---

# Probability Engine

Probability Engine 综合多个 Signal 计算：

- Market Probability
- Industry Probability
- Stock Probability
- Risk Probability

输出统一为标准化概率评分。

---

# Decision Engine

Decision Engine 不处理原始数据。

Decision Engine 仅消费 Probability Engine 输出。

Decision Engine 负责：

- Risk Budget
- Capital Allocation
- Sector Rotation
- Stock Selection
- Position Sizing

---

# Explainability

任何投资建议必须能够追溯：

Signal
↓
Probability
↓
Decision
↓
Execution

形成完整解释链。

---

# Success Criteria

Athena 的投资建议来源于多信号融合与概率推断，而不是单一指标或固定规则。

所有未来算法必须兼容本框架。
