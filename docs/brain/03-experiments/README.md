# 03-experiments — Layer 3

## Purpose

Experiments 层记录所有可复现的实验。每个实验必须描述完整的环境、步骤、数据和结果，确保任何人在未来都能重现该实验。

## Scope

所有为验证假设而进行的投资相关实验：

- 回测实验
- 统计检验
- 模拟交易
- 数据质量验证
- 模型性能测试
- A/B 测试

## Allowed Document Types

- `EXPERIMENT-*` — 单个实验记录

## Required Metadata

```yaml
id: EXPERIMENT-###
title: <title>
status: Draft | Executing | Completed | Failed
version: <semver>
research: RESEARCH-###  # 关联的研究
owner: <experimenter>
created: <YYYY-MM-DD>
executed: <YYYY-MM-DD>
environment:  # 实验环境
  data_version: <version>
  code_version: <commit-hash>
  parameters: {}
result: Passed | Failed | Inconclusive
reproducibility: High | Medium | Low
```

## Required Content Sections

每个 Experiment 必须包含：

1. **Objective** — 实验目标
2. **Setup** — 环境与数据准备
3. **Method** — 实验方法
4. **Results** — 实验结果（含数据）
5. **Reproducibility** — 可复现性评估
6. **Artifacts** — 产出物清单（代码、数据、图表路径）

## Lifecycle

```
Draft → Executing → Completed → Archived

Draft → Executing → Failed → Archived
```

失败的实验不可删除。

## Naming Convention

```
EXPERIMENT-###-short-description.md
```

编号使用三位数字，从 001 开始。

## Relationship

- **上游**: Research（02-research/）— 实验验证研究假设
- **上游**: Evidence（06-evidence/）— 实验使用的原始数据
- **下游**: Knowledge（01-knowledge/）— 成功实验支撑 Knowledge 生成
- **下游**: Failures（04-failures/）— 失败实验需同步记录到 Failures 层
- **配套**: 代码仓库中的实验脚本应与实验文档关联
