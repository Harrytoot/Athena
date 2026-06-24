# ADR-001: Sprint 1 技术栈冻结

## Status

Accepted (2026-06-24)

## Context

Athena 项目 Sprint 1 (Foundation) 需要冻结核心技术栈，以确保团队统一技术方向，避免后期分散决策带来的返工成本。

## Decision

### Frontend

| 层级 | 选型 | 版本 |
|------|------|------|
| 框架 | Next.js + React + TypeScript | Latest |
| UI 组件库 | shadcn/ui | Latest |
| 样式方案 | Tailwind CSS | Latest |

### Backend

| 层级 | 选型 | 版本 |
|------|------|------|
| 语言 | Python | 3.12 |
| Web 框架 | FastAPI | Latest |
| ORM | SQLAlchemy | 2.x |
| 校验 | Pydantic | v2 |

### Infrastructure

| 层级 | 选型 | 版本 |
|------|------|------|
| 数据库 | PostgreSQL | 16 |
| 缓存 | Redis | 7 |
| 对象存储 | MinIO | Latest |
| 容器编排 | Docker Compose | Latest |
| 反向代理 | Nginx | Latest |
| AI 网关 | LiteLLM | Latest |

### Architecture

- Domain-Driven Design (DDD)
- Clean Architecture
- Plugin Architecture

## Constraints

- 除非通过新的 ADR 批准，禁止擅自修改上述技术栈
- Sprint 1 仅构建 Foundation 基础设施，不实现 AI Agent、自动交易、知识图谱、DSL 等后续能力

## Consequences

- 所有模块必须基于上述技术栈实现
- 新增技术依赖需先经 RFC 讨论，ADR 批准
- 技术选型与架构原则已在项目初期明确，降低后期重构风险

## References

- Chief Architect (ChatGPT) — 技术栈正式冻结指令 (2026-06-24)
