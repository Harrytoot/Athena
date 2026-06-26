# ARCHITECTURE BRAIN v1.0

Status: ACTIVE — System Evolution + Sprint History + Design Reasoning

## 0. System Context

Athena is a quantitative market intelligence system built incrementally through:

- Sprint-based engineering execution
- Strict layered architecture enforcement
- Feature-driven financial modeling
- Backtest-driven validation

Current implementation status:

- Provider Layer (Mock / AkShare / Redis)
- Feature Engine (deterministic transformation)
- Feature Store (versioned historical persistence)
- MarketScore Model (weighted factor model)
- Backtest Engine (IC / RankIC evaluation)
- API Layer (FastAPI + DTO separation)

---

## 1. Core Design Principles

### 1.1 No Real-time Dependency

The system MUST NOT rely on live external API calls for:

- Backtesting
- Strategy evaluation
- Feature computation
- Market scoring analysis

All analytical computation MUST be based on:

> Feature Store (historical, versioned, persisted data)

### 1.2 Data Flow Invariance

All system execution MUST follow:

```
Remote Data → Ingestion Layer → Feature Store → Feature Engine → MarketScore → Backtest Engine
```

NO exceptions.

---

## 2. Layer Responsibility Contracts

### 2.1 Provider Layer

| Responsibility | Allowed | Forbidden |
|---------------|---------|-----------|
| Fetch raw external market data | Raw numeric extraction | Feature engineering |
| | | Scoring logic |

### 2.2 Feature Engine Layer

| Responsibility | Allowed | Forbidden |
|---------------|---------|-----------|
| Deterministic transformation of raw data | Normalization | Investment decision logic |
| Construction of FeatureItem objects | Ratio calculation | Scoring weights |
| | Statistical derivation | |

### 2.3 Feature Store Layer

| Responsibility | Guarantees |
|---------------|------------|
| Persist FeatureItems | Append-only storage |
| Provide historical queries | Time-series integrity |
| Ensure versioning and traceability | Reproducibility |

### 2.4 MarketScore Domain Layer

| Responsibility | Forbidden |
|---------------|-----------|
| Convert Features → Score | Data fetching |
| Apply deterministic weighting | Persistence logic |
| Provide market state classification | |

### 2.5 Backtest Engine Layer

| Responsibility | Critical Constraint |
|---------------|---------------------|
| Evaluate predictive power of MarketScore | MUST NOT use future data (no lookahead bias) |
| Compute IC / RankIC / returns / Sharpe | |

---

## 3. Ingestion Layer — Critical Missing Component

System MUST include a scheduled ingestion pipeline:

```
Remote API → Feature Store (append-only)
```

Responsibilities:

- Periodic data fetching
- Normalization into FeatureItems
- Persistence
- Cache refresh

This layer decouples system from real-time dependency.

---

## 4. Backtest Validity Constraints

### 4.1 Temporal Integrity

```
Feature(t) → Score(t) → Return(t+n)
```

NO forward leakage permitted.

### 4.2 Cross-sectional Evaluation

Metrics MUST be computed across assets/time slices, not single time series.

### 4.3 Deterministic Execution

Same input MUST produce identical output.

---

## 5. System Architecture Goal

Athena is NOT:

- A trading bot
- A real-time prediction engine
- An AI model system

Athena IS:

> A deterministic market feature engineering + signal validation system

---

## 6. Known System Constraints

### 6.1 External API Volatility
AkShare / external sources are unstable → MUST be decoupled via ingestion layer.

### 6.2 Feature Drift Risk
Feature definitions may evolve → MUST support versioning.

### 6.3 Score Interpretation
Score is NOT prediction → Score is a signal strength proxy.

---

## 7. System Evolution Rule

No new capability may be introduced unless:

1. Data flow remains valid
2. Feature Store remains authoritative
3. Backtest remains reproducible

If violated → architecture rejection.

---

## 8. Current System State

### Completed
- Feature Engine v1
- Feature Store v1
- MarketScore v1
- Backtest Engine v1
- Provider abstraction layer

### Missing / Next Required
- Ingestion Layer (CRITICAL)
- Scheduled data pipeline
- Feature lifecycle management (TTL / decay not yet defined)

---

## 9. Final Principle

**System correctness > feature completeness**

Any future expansion must preserve:

- Reproducibility
- Determinism
- Time alignment integrity

---

## References

- [ADR-011 Data Layer Separation](../adr/ADR-011-data-layer-separation.md)
- [ARCHITECTURE_PRINCIPLES.md](./ARCHITECTURE_PRINCIPLES.md)
- [DATA-001 Feature Contract](../data/DATA-001-feature-contract.md)
- [Sprint 2 Definition](../sprint/SPRINT-002-definition.md)
