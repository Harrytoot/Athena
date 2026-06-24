# RFC-002 Multi-Repository Architecture

## Status

Approved (2026-06-24)

## Context

当前所有代码和文档混在一个仓库，不利于职责分离和版本演进。

## Decision

Athena 拆分为 12 个独立 Git 仓库。

| # | 仓库 | 作用 | 内容 |
|---|------|------|------|
| 1 | **athena-charter** | 章程 & 架构决策 | Constitution, ADR, Vision, Mission |
| 2 | **athena-docs** | 产品 & 技术文档 | PRD, Architecture, API, Database, Glossary |
| 3 | **athena-core** | 核心业务逻辑 | Domain, Application Service, DDD |
| 4 | **athena-agents** | AI Agent | Agent 定义, Capability Registry |
| 5 | **athena-frontend** | Web 前端 | Next.js, Components, Dashboard |
| 6 | **athena-data** | 数据平台 | ETL, Feature Store, Data Connectors |
| 7 | **athena-research** | 研究 & 实验 | Backtest, Notebook, Factor Research |
| 8 | **athena-prompts** | Prompt 管理 | Prompt 版本, Agent 配置, 评测 |
| 9 | **athena-infra** | 基础设施 | Docker, Kubernetes, CI/CD |
| 10 | **athena-tests** | 测试 | Unit, Integration, Performance, Regression |
| 11 | **athena-sdk** | 对外 SDK | Python SDK, REST Client |
| 12 | **athena-ops** | 运维 | 监控, 日志, Alert |

## Rationale

| 原则 | 说明 |
|------|------|
| **研究不污染代码** | `athena-research` 独立，可随意实验 |
| **Prompt 即代码** | `athena-prompts` 独立版本管理，不与代码混 |
| **Agent 可独立部署** | `athena-agents` 独立构建和部署 |
| **文档独立发布** | `athena-charter` + `athena-docs` 可公开 |
| **基础设施可复用** | `athena-infra` 跨项目使用 |

## Migration Strategy

Sprint 1 结束后执行，避免中断当前开发。

1. 创建 12 个空仓库
2. 按目录迁移文件
3. 保留提交历史（git subtree split）
4. 更新 CI/CD 配置
5. 更新 AGENTS.md 中的工作目录指向 `athena-core`

## OpenCode Workspace

```
athena-core/      ← 主工作目录
athena-frontend/  ← 前端工作目录
athena-tests/     ← 测试工作目录
```

## Cross-Repo References

文档间引用使用 GitHub 相对路径：
```
[Constitution](../athena-charter/Constitution.md)
[AMS](../athena-docs/ams/AMS-001.md)
```

## References

- [ADR-005 Enterprise R&D Process](../adr/ADR-005-enterprise-rd-process.md)
- [AES-002 AI Architecture](../aes/AES-002-ai-architecture.md)
