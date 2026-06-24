# 08-glossary — Domain Glossary

## Purpose

Glossary 定义 Athena Brain 中使用的所有领域术语，确保 AI、开发者、分析师使用统一语言。

注意：此 Glossary 专注于 Athena Brain 知识体系内部术语。项目级通用术语参见 [docs/glossary/](../../glossary/)。

## Scope

- Athena Brain 专用术语定义
- 投资领域术语（与 Brain 知识体系相关）
- 方法论术语
- 缩写与简称
- 中英文术语对照

## Allowed Document Types

- `GLOSSARY-*` — 术语集（按领域分组）
- `TERM-*` — 单条术语定义（可选，大量术语时使用）

## Required Metadata

```yaml
id: GLOSSARY-###
title: <title>
version: <semver>
domain: all | market | macro | industry | factor | policy | sentiment | execution | ontology
owner: <steward>
updated: <YYYY-MM-DD>
```

## Required Content Sections

每个 Glossary 条目必须包含：

1. **Term** — 术语
2. **Abbreviation** — 缩写（如有）
3. **Definition** — 定义
4. **Context** — 使用场景
5. **Related Terms** — 相关术语

## Lifecycle

```
Draft → Review → Active → Updated → Archived
```

术语定义随领域知识演进而更新。

## Naming Convention

```
GLOSSARY-###-domain-name.md
TERM-###-term-name.md
```

编号使用三位数字，从 001 开始。

## Relationship

- **配套**: Ontology Knowledge（01-knowledge/ontology/）— 术语定义与实体定义互补
- **参考**: 所有 Brain 层级 — 所有文档写作时应参考 Glossary 确保术语一致
- **补充**: 项目级 Glossary（docs/glossary/）— 项目通用术语
