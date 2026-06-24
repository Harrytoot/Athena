# RFC-002 Three-Repository Architecture

## Status

Proposed (2026-06-24)

## Context

当前所有代码和文档混在一个仓库，不利于职责分离和版本演进。

## Proposal

将 Athena 拆分为三个独立 Git 仓库：

### athena-docs

```
athena-docs/
├── PRD/
├── Architecture/
│   ├── SystemArchitecture.md
│   ├── DataArchitecture.md
│   └── AgentArchitecture.md
├── API/
├── Database/
├── UI/
├── Roadmap/
├── ADR/
├── AES/
├── Prompt/
│   ├── MarketAgent/
│   │   ├── v1.0.md
│   │   └── v1.1.md
│   └── StrategyAgent/
│       └── v1.0.md
└── ProjectCharter.md
```

**职责**: 所有非代码资产 — 需求、架构、设计、Prompt 版本管理。

### athena-core

```
athena-core/
├── backend/
├── frontend/
├── docker/
├── tests/
└── AGENTS.md
```

**职责**: 所有代码。OpenCode 只写这里。

### athena-research

```
athena-research/
├── backtests/
├── notebooks/
├── factors/
├── experiments/
├── data_analysis/
└── papers/
```

**职责**: 回测、Notebook、因子研究、AI 实验、数据分析。

## Rationale

- 研究不会污染代码
- 代码不会污染文档
- 文档可独立版本发布
- 研究可 Fork 克隆而不带代码

## Migration Strategy

**Sprint 1 结束时执行**，避免中断当前开发。

1. 创建三个空仓库
2. 按目录迁移文件
3. 保留提交历史（`git filter-branch` 或 `git subtree split`）
4. 更新 CI/CD
5. 更新 AGENTS.md 引用

## Impact

- 当前 Sprint 1 不受影响
- 跨仓库引用需约定（文档中交叉引用使用相对路径转为固定 URL）
- OpenCode 工作目录需切换为 `athena-core`

## Alternatives Considered

- **Monorepo + Git Submodules**: 增加复杂度，权限控制较差
- **保持单仓库**: 职责混乱，长期维护成本高

## Decision

Pending review.

## References

- [ADR-003](../adr/ADR-003-core-principles.md)
- [AES-001](../aes/AES-001-four-layer-architecture.md)
