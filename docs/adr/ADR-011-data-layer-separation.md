# ADR-011 Data Layer Separation — Ingestion, Feature Store, Cache Isolation

## Status

Approved (2026-06-26)

---

## Context

Athena 当前数据层存在架构违规：

### 问题 1: data_worker 绕过 Feature Store

`data_worker/sync.py` 直接调用 AKShare 并写入 Redis：

```
AKShare → Redis (Cache)
```

缺少：

- Feature Store 持久化
- Normalizer 转换层
- FeatureItem 格式契约

### 问题 2: data_worker 承担了跨层职责

`sync_market_overview()` 在同步阶段计算 `market_regime` 和 `temperature`。Provider 层不应做特征计算。

### 问题 3: Feature Engine 无真实接入

`feature_engine/market_features.py` 仅对接 Mock Provider，未对接真实 Ingestion Pipeline。

### 问题 4: Backtest 存在间接耦合风险

当前 backtest_engine 目录存在但未锁定数据来源，可能在后续开发中直接调用 Provider/API。

---

## Decision 1 — Data Architecture Principle

System must NOT directly depend on remote APIs for:

- Backtesting
- Feature computation
- Strategy evaluation

All analytical workflows MUST rely on:

```
Remote API → Ingestion Layer → Feature Store → Cache
```

**Rationale**: 保证回测可重复、特征可追溯、策略可审计。任何绕过 Feature Store 的数据访问都会破坏可复现性。

---

## Decision 2 — Data Layer Separation

Four layers with strict responsibilities:

| Layer | Responsibility | Forbidden |
|-------|---------------|-----------|
| Provider Layer | Raw data acquisition only | Transformation, caching |
| Feature Engine | Deterministic transformation only | API calls, persistence |
| Feature Store | Persistence + versioning + history | API calls, transformation |
| Cache Layer | Performance optimization only | Long-term storage, computation |

NO cross-layer responsibilities allowed.

**Rationale**: 每层职责单一，可独立测试、替换、扩展。

---

## Decision 3 — Ingestion Requirement

System MUST include scheduled ingestion pipeline:

1. Pull remote data (AkShare or equivalent)
2. Normalize into FeatureItem format
3. Persist to Feature Store (append-only)
4. Update cache for dashboard usage

**Pipeline**:

```
data_worker (scheduler)
  → Provider (raw acquisition)
  → Normalizer (→ FeatureItem)
  → FeatureRepository.save_batch() (Feature Store)
  → Redis cache update (Cache Layer)
```

**Rationale**: Append-only 保证历史可回溯；Cache 只存最新快照供仪表盘使用。

---

## Decision 4 — Backtest Principle

Backtest MUST NOT call external APIs.

All backtest computations must be based on Feature Store historical dataset ONLY.

**Rule**: 任何 Backtest Engine 的构造函数只接受 `FeatureRepository` 作为数据源。

**Rationale**: 确保回测结果可重现，不同时间运行同一回测得到相同结果。

---

## Decision 5 — System Goal Clarification

Athena is NOT a real-time prediction system.

Athena is a:

```
Market Data → Feature Engineering → Signal Validation System
```

**Implications**:

- No real-time tick data requirement
- No low-latency requirement
- No streaming inference requirement
- Batch processing is the default mode
- Daily/periodic feature update is sufficient

**Rationale**: 明确系统边界，防止 scope creep。

---

## Consequences

### Positive

- 回测可重复、结果可信
- 特征计算可追溯（谁、何时、用什么源）
- 每层可独立测试和替换
- 新数据源接入不影响算法层
- 系统边界清晰，防止功能蔓延

### Negative

- data_worker 需要重构（当前直接写 Redis）
- 增加 Feature Store 持久化开销
- 仪表盘读取多一层间接

### Migration Path (Sprint 2)

1. **Normalizer** — 新增 `data_worker/normalizer.py`，将 AKShare 原始数据转为 FeatureItem
2. **Feature Store 接入** — data_worker 调用 `FeatureRepository.save_batch()` 写入数据库
3. **Cache 降级** — 从 Feature Store 读取最新数据更新 Redis Cache，而非直接写
4. **Backtest 锁定** — 确保 Backtest Engine 仅接受 FeatureRepository
5. **data_worker 清理** — 移除 `sync_market_overview` 中的 regime/temperature 计算，移至 Feature Engine

---

## References

- [ARCHITECTURE BRAIN v1.0](../architecture/ARCHITECTURE_BRAIN.md) — comprehensive superset
- [ARCHITECTURE_PRINCIPLES.md](../architecture/ARCHITECTURE_PRINCIPLES.md)
- [DATA-001 Feature Contract](../data/DATA-001-feature-contract.md)
- [ADR-006 Architecture Corrections](./ADR-006-architecture-corrections.md)
- [AES-002 AI Architecture](../aes/AES-002-ai-architecture.md)
- [SPRINT-002 Definition](../sprint/SPRINT-002-definition.md)
- [Feature Repository](../src/backend/app/feature_store/repository.py)
- [Feature Model](../src/backend/app/feature_store/models.py)
