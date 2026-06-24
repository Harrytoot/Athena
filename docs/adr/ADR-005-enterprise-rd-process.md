# ADR-005 Enterprise R&D Process & Team Structure

## Status

Approved (2026-06-24)

## Decision

### 1. Team Roles

Athena 正式设立四个角色：

| 角色 | 承担者 | 职责 |
|------|--------|------|
| **Founder** | 你 | 产品愿景、最终决策 |
| **Chief Architect** | ChatGPT | 架构设计、ADR/RFC/PRD |
| **Software Engineer** | OpenCode | 代码实现、测试 |
| **QA Architect** | OpenCode | 测试先于代码 |
| **Data Architect** | OpenCode | 数据标准统一 |
| **AI Governance** | ChatGPT + OpenCode | Prompt/Agent/Model 版本管理 |

### 2. TDD Flow（测试驱动开发）

任何需求必须：

```
PRD → Test Case → Code → CI → Merge
```

OpenCode 没有测试不能提交。

### 3. Architecture Governance

任何修改必须经过 RFC gate：

```
Idea → RFC → Review → ADR → PRD → Task → Code
```

几年后仍可追溯每一次架构决策。

### 4. Directory Structure — DDD Monorepo

Athena 采用 DDD + Clean Architecture + Event Driven，不采用 MVC。

```
athena/
├── apps/
│   ├── api/            # FastAPI 应用
│   ├── dashboard/      # Next.js 前端
│   └── worker/         # 后台任务
├── domains/
│   ├── market/         # Market Domain
│   ├── portfolio/      # Portfolio Domain
│   ├── research/       # Research Domain
│   ├── strategy/       # Strategy Domain
│   └── learning/       # Learning Domain
├── shared/
│   ├── kernel/         # 共享内核（Value Objects, Base Entities）
│   ├── events/         # Event Bus + Event Definitions
│   └── infra/          # 基础设施
│       ├── postgres/
│       ├── redis/
│       ├── llm/
│       └── broker/
├── providers/          # 外部系统 Provider
├── tests/
└── docs/
```

所有代码按 Domain 组织，不按 Controller。

### 5. Provider Pattern（强化）

所有外部系统全部通过 Provider：

```
MarketDataProvider
├── AKShareProvider
├── TushareProvider
├── WindProvider
└── JoinQuantProvider

LLMProvider
├── OpenAIProvider
├── QwenProvider
└── DeepSeekProvider

BrokerProvider
├── SimulatedBrokerProvider
├── 华泰Provider
└── 东方财富Provider
```

切换：一行配置，零代码改动。

### 6. Data Standards

| 规范 | 示例 | 禁止 |
|------|------|------|
| 股票代码 | `600519.SH`, `000001.SZ` | `SZ000001` |
| 日期格式 | ISO 8601 `2026-06-24T15:00:00+08:00` | 本地格式 |
| 金额单位 | 元（float） | 万元混杂 |
| 数值精度 | Decimal(18,4) | Float 直接比较 |

## Consequences

- 所有 PRD 必须附带 Test Case
- 所有代码变更走 RFC gate（架构层面）
- 目录结构按 Sprint 1 结束后迁移
- 数据标准立即生效

## References

- [AMS-001](../ams/AMS-001-master-specification.md)
- [Constitution v2.0.0](../project_charter/Constitution.md)
