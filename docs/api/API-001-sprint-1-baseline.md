---
id: API-001
title: Sprint 1 API Baseline
status: Approved
version: 1.0.0
depends:
  - RFC-001
---

# API-001 Sprint 1 API Baseline

## Base URL

`/api/v1`

## Authentication

JWT Bearer Token in `Authorization` header.

## Endpoints

### Auth

#### POST /api/v1/auth/login

Request:
```json
{
  "username": "string",
  "password": "string"
}
```

Response (200):
```json
{
  "access_token": "string",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### GET /api/v1/auth/me

Headers: `Authorization: Bearer <token>`

Response (200):
```json
{
  "id": "uuid",
  "username": "string",
  "email": "string",
  "display_name": "string"
}
```

### Dashboard

#### GET /api/v1/dashboard

Response (200):
```json
{
  "total_assets": "decimal",
  "total_return_pct": "decimal",
  "watchlist_count": "int",
  "position_count": "int",
  "market_summary": {
    "shanghai_change_pct": "decimal",
    "shenzhen_change_pct": "decimal",
    "market_temperature": "int"
  },
  "latest_recommendations": [
    {
      "action": "string",
      "confidence": "decimal",
      "reason": "string"
    }
  ]
}
```

### Market

#### GET /api/v1/market/overview

Response (200):
```json
{
  "indices": {
    "shanghai": { "code": "string", "name": "string", "price": "decimal", "change_pct": "decimal" },
    "shenzhen": { "code": "string", "name": "string", "price": "decimal", "change_pct": "decimal" },
    "chi_next": { "code": "string", "name": "string", "price": "decimal", "change_pct": "decimal" }
  },
  "turnover": "decimal",
  "advance_count": "int",
  "decline_count": "int",
  "northbound_flow": "decimal",
  "hot_sectors": ["string"],
  "market_temperature": "int",
  "ai_summary": "string"
}
```

#### GET /api/v1/stocks/{symbol}

Response (200):
```json
{
  "symbol": "string",
  "name": "string",
  "price": "decimal",
  "change_pct": "decimal",
  "open": "decimal",
  "high": "decimal",
  "low": "decimal",
  "volume": "int",
  "turnover": "decimal",
  "pe_ratio": "decimal",
  "pb_ratio": "decimal",
  "market_cap": "decimal",
  "technical_indicators": {
    "ma5": "decimal",
    "ma20": "decimal",
    "rsi": "decimal",
    "macd": { "diff": "decimal", "dea": "decimal", "histogram": "decimal" }
  },
  "money_flow": {
    "main_force_inflow": "decimal",
    "retail_inflow": "decimal",
    "northbound_inflow": "decimal"
  },
  "ai_analysis": {
    "summary": "string",
    "risk_level": "string",
    "sentiment": "string"
  }
}
```

### Watchlist

#### GET /api/v1/watchlists

Response (200):
```json
[
  {
    "id": "uuid",
    "name": "string",
    "sort_order": "int",
    "items": [
      {
        "id": "uuid",
        "symbol": "string",
        "name": "string",
        "price": "decimal",
        "change_pct": "decimal",
        "tags": ["string"],
        "note": "string",
        "sort_order": "int"
      }
    ]
  }
]
```

#### POST /api/v1/watchlists

Request:
```json
{
  "name": "string"
}
```

Response (201): Created watchlist object.

#### DELETE /api/v1/watchlists/{id}

Response (204): No Content.

#### POST /api/v1/watchlists/{id}/items

Request:
```json
{
  "symbol": "string",
  "name": "string"
}
```

Response (201): Created item object.

#### DELETE /api/v1/watchlists/{id}/items/{item_id}

Response (204): No Content.

#### PATCH /api/v1/watchlists/{id}/items/{item_id}

Request:
```json
{
  "tags": ["string"],
  "note": "string",
  "sort_order": "int"
}
```

Response (200): Updated item object.

### Portfolio

#### GET /api/v1/portfolio

Response (200):
```json
{
  "id": "uuid",
  "name": "string",
  "cash": "decimal",
  "total_assets": "decimal",
  "total_cost": "decimal",
  "total_pnl": "decimal",
  "total_pnl_pct": "decimal",
  "positions": [
    {
      "id": "uuid",
      "symbol": "string",
      "name": "string",
      "shares": "decimal",
      "cost_price": "decimal",
      "current_price": "decimal",
      "market_value": "decimal",
      "pnl": "decimal",
      "pnl_pct": "decimal",
      "weight_pct": "decimal"
    }
  ]
}
```

#### POST /api/v1/portfolio

Request:
```json
{
  "name": "string",
  "cash": "decimal"
}
```

Response (201): Created portfolio object.

#### POST /api/v1/portfolio/positions

Request:
```json
{
  "symbol": "string",
  "name": "string",
  "shares": "decimal",
  "cost_price": "decimal"
}
```

Response (201): Created position object.

#### PATCH /api/v1/portfolio/positions/{id}

Request:
```json
{
  "shares": "decimal",
  "cost_price": "decimal"
}
```

Response (200): Updated position object.

#### DELETE /api/v1/portfolio/positions/{id}

Response (204): No Content.

### Recommendation

#### GET /api/v1/recommendations

Query params: `?limit=10`

Response (200):
```json
[
  {
    "id": "uuid",
    "action": "buy",
    "symbol": "string",
    "confidence": 75.0,
    "reason": "string",
    "risk": "medium",
    "position_suggestion": 20.0,
    "expire_at": "datetime",
    "created_at": "datetime"
  }
]
```

## References

- [RFC-001](../rfc/RFC-001-sprint-1-foundation-development-plan.md)
- [DB-001](../database/DB-001-sprint-1-baseline.md)
