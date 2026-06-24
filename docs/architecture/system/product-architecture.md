# Athena Product Architecture — Five Products

## Status

Ratified (2026-06-24)

## Products

Athena 拆分为 5 个独立产品，各自独立版本、独立部署、独立团队。

| # | 产品 | 定位 | 核心能力 |
|---|------|------|---------|
| **A** | **Athena Core** | 核心引擎 | DDD Domain, Event Bus, Plugin Kernel, Provider Registry |
| **B** | **Athena Research** | 研究平台 | Feature Store, Backtest, Factor Research, Hypothesis Engine |
| **C** | **Athena Studio** | 策略开发 | DSL Editor, Strategy Builder, Simulation, Optimization |
| **D** | **Athena Terminal** | 投资终端 | Dashboard, Market View, Portfolio, Decision Timeline |
| **E** | **Athena Brain** | AI Agent | Capability Registry, Agents, LLM Reasoning, Knowledge Graph |

## Product Dependencies

```
Athena Core ← 所有产品依赖
    ↑
    ├── Athena Research ──→ Athena Brain ←── Athena Core
    ├── Athena Studio   ──→ Athena Brain ←── Athena Core
    └── Athena Terminal ──→ Athena Brain ←── Athena Core
                            Athena Research
```

## Current Sprint 1 Scope

Sprint 1 构建 Athena Core + Athena Terminal 的 Foundation：

- **Athena Core**: Domain 骨架, Provider Pattern, Event Bus 预留
- **Athena Terminal**: Dashboard, Market, Watchlist, Stock Detail, Portfolio

## References

- [AMS-001](../ams/AMS-001-master-specification.md)
- [AES-001 Four-Layer Architecture](../aes/AES-001-four-layer-architecture.md)
- [ADR-006 Architecture Corrections](../adr/ADR-006-architecture-corrections.md)
