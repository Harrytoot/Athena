# Execution Knowledge

## Purpose

存储关于交易执行、订单管理、交易成本分析、算法交易等方面的已验证知识。

## Scope

- 订单类型与执行策略
- 交易成本分析（佣金、滑点、冲击成本）
- 算法交易（TWAP、VWAP、POV 等）
- 最优执行框架
- 流动性管理
- 交易前/后分析
- 经纪商选择与评估

## Allowed Document Types

- `KNOWLEDGE-*` — 单条已验证知识

## Required Metadata

遵循父目录 [01-knowledge/README.md](../README.md) 的元数据规范。

额外要求 `domain: execution`。

## Lifecycle

遵循父目录生命周期。

## Naming Convention

遵循父目录命名规范。

## Relationship

- **上游**: Research、Evidence
- **下游**: Playbooks（通过父级 Knowledge 层）
- **同级**: 与 market（流动性）、factor（交易成本因子）等其他 Knowledge 子域协作
