# Ontology Knowledge

## Purpose

存储投资领域的实体定义、分类体系、关系模型、参考数据标准等已验证的领域知识。

## Scope

- 投资领域核心实体定义（证券、组合、策略、订单等）
- 实体关系模型
- 分类体系与编码标准
- 数据字典
- 领域事件定义
- 度量指标定义
- 参考数据治理规则

## Allowed Document Types

- `KNOWLEDGE-*` — 单条已验证知识
- `ONTOLOGY-*` — 本体定义文档（实体关系图、分类树等）

## Required Metadata

遵循父目录 [01-knowledge/README.md](../README.md) 的元数据规范。

额外要求 `domain: ontology`。

对于 `ONTOLOGY-*` 文档，增加字段：
```yaml
version: <semver>
steward: <领域负责人>
```

## Lifecycle

遵循父目录生命周期。

## Naming Convention

遵循父目录命名规范。

## Relationship

- **上游**: Research、Evidence
- **下游**: 所有其他 Knowledge 子域（ontology 是领域模型的根基）
- **配套**: Glossary（08-glossary/）— 术语定义与本体互补
- **与代码的关系**: 代码中的 Domain Model 必须与 ontology 对齐
