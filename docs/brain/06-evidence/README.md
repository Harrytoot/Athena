# 06-evidence — Evidence Repository

## Purpose

Evidence 层存储所有可追溯的原始证据。Evidence 是 Research 和 Knowledge 的事实基础，必须可追溯、可验证、不可篡改。

## Scope

- 市场数据快照与分析
- 学术论文引用与摘要
- 行业报告摘要
- 监管文件引用
- 新闻事件时间线
- 数据源信息与质量评估
- 第三方数据引用记录

## Allowed Document Types

- `EVIDENCE-*` — 单条证据记录

## Required Metadata

```yaml
id: EVIDENCE-###
title: <title>
status: Collected | Verified | Superseded
version: <semver>
type: data | paper | report | regulatory | news | other
source: <完整来源信息，确保可追溯>
source_url: <URL>
collected_by: <collector>
collected_date: <YYYY-MM-DD>
verified_by: <verifier>
verified_date: <YYYY-MM-DD>
expires: <YYYY-MM-DD | Permanent>
related_research: [RESEARCH-###, ...]
```

## Required Content Sections

每条 Evidence 必须包含：

1. **Excerpt** — 关键内容摘要
2. **Full Source** — 完整来源信息（确保可追溯）
3. **Reliability** — 可靠性评估（High | Medium | Low）
4. **Relevance** — 与哪些研究/知识相关
5. **Raw Data Reference** — 原始数据位置（如 MinIO 路径）

## Lifecycle

```
Collected → Verified → Active → Superseded → Archived
```

Evidence 不可删除，只能标记为 Superseded 并指向新证据。

## Naming Convention

```
EVIDENCE-###-short-description.md
```

编号使用三位数字，从 001 开始。

## Relationship

- **下游**: Research（02-research/）— 研究引用证据
- **下游**: Knowledge（01-knowledge/）— 知识引用证据
- **下游**: Decisions（07-decisions/）— 决策引用证据
- **配套**: MinIO — 原始数据文件存储
