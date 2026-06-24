---
id: PRD-002
title: Watchlist
status: Approved
version: 1.0.0
owner: Chief Architect
reviewer: Founder
epic: Epic-003
---

# PRD-002 Watchlist

## Background

Watchlist 是 Athena 的第一个用户数据模块。

它不仅用于收藏股票，更是后续 Portfolio、Research、AI Recommendation、Strategy、Backtest 等模块的统一入口。

未来所有分析能力默认围绕 Watchlist 展开。

---

# Product Goals

支持用户维护多个自选股分组，并为每只股票保存标签、备注和排序。

第一阶段采用人工维护。

第二阶段增加 AI 自动维护。

---

# Functional Requirements

## Watchlist Group

支持：

- 新建分组
- 编辑名称
- 删除分组
- 排序
- 设置颜色

默认创建：

- 我的关注
- 长线
- 波段
- 短线
- 观察池

---

## Watchlist Item

每条记录包含：

- 股票代码
- 股票名称
- 标签
- 备注
- 添加时间
- 排序

---

## Search

支持：

- 股票代码搜索
- 股票名称搜索

第一阶段：

Mock Provider。

第二阶段：

AKShare。

---

## Quick Actions

支持：

- 添加
- 删除
- 批量删除
- 移动到其他分组

---

## Future Extension

预留：

- AI 推荐加入 Watchlist
- 导入 Excel
- 导出 Excel
- 导入同花顺
- 导入东方财富
- 标签智能分类

---

# Domain

Watchlist

WatchlistItem

---

# UI

左侧：

Watchlist Group

右侧：

Stock Table

顶部：

Search

New Group

Add Stock

---

# Acceptance Criteria

- 支持多个分组
- 支持 CRUD
- 支持排序
- 支持备注
- 支持标签
- Provider 可替换
- API 与 Domain 分离
