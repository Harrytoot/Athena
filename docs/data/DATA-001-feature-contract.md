========================================
ARCHITECT MODE
========================================

Document Level : A
Git            : YES
OpenCode       : YES
Action         : CREATE
Priority       : P0

Target File

docs/data/DATA-001-feature-contract.md

========================================

# DATA-001 Feature Contract

## Purpose

统一 Athena 内部所有数据表示。

任何数据提供方（AkShare、Tushare、BaoStock、自建服务）返回的数据必须转换为统一 Feature。

算法层不得直接消费 Provider 原始数据。

---

## Pipeline

Provider

↓

Normalizer

↓

Feature Store

↓

Algorithm

↓

API

---

## Feature Schema

Feature

id

name

category

value

unit

confidence

source

update_time

expire_time

version

---

## Categories

- Market
- Index
- ETF
- Stock
- Industry
- Capital Flow
- Valuation
- Macro
- Sentiment
- Policy

---

## Naming Convention

snake_case

Example

market_turnover

northbound_net_inflow

up_limit_count

breadth_ratio

volatility_20d

---

## Rules

禁止 Algorithm 直接访问 Provider。

所有算法只能访问 Feature。

未来新增数据源不得影响算法层。

========================================
