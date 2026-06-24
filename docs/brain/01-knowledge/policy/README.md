# Policy Knowledge

## Purpose

存储关于监管政策、法律法规、合规要求、交易所规则等方面的已验证知识。

## Scope

- 证券法规与监管框架
- 交易所上市与交易规则
- 信息披露要求
- 投资者保护制度
- 税收政策
- 跨境投资政策
- 合规审查标准

## Allowed Document Types

- `KNOWLEDGE-*` — 单条已验证知识

## Required Metadata

遵循父目录 [01-knowledge/README.md](../README.md) 的元数据规范。

额外要求 `domain: policy`。

## Lifecycle

遵循父目录生命周期。

## Naming Convention

遵循父目录命名规范。

## Relationship

- **上游**: Research、Evidence
- **下游**: Playbooks（通过父级 Knowledge 层）
- **同级**: 与 macro、market 等其他 Knowledge 子域协作，特别是与宏观政策联动
