# Sentiment Knowledge

## Purpose

存储关于市场情绪、投资者行为、新闻舆情分析、资金流向等方面的已验证知识。

## Scope

- 市场情绪指标体系
- 投资者情绪调研（如 AAII）
- 资金流向与仓位分析
- 新闻舆情量化方法论
- 社交媒体情绪分析
- 恐慌与贪婪指数
- 行为金融学洞见

## Allowed Document Types

- `KNOWLEDGE-*` — 单条已验证知识

## Required Metadata

遵循父目录 [01-knowledge/README.md](../README.md) 的元数据规范。

额外要求 `domain: sentiment`。

## Lifecycle

遵循父目录生命周期。

## Naming Convention

遵循父目录命名规范。

## Relationship

- **上游**: Research、Evidence
- **下游**: Playbooks（通过父级 Knowledge 层）
- **同级**: 与 market、macro 等其他 Knowledge 子域协作，情绪常与市场结构叠加分析
