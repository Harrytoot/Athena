---
id: TASK-0006
title: Epic-006 Recommendation
epic: Recommendation
status: Pending
priority: High
dependencies:
  - ADR-001
  - RFC-001
  - TASK-0002
  - TASK-0003
  - TASK-0005
---

# TASK-0006 Epic-006 Recommendation

## Goal

基于 Rule Engine 的推荐系统。禁止调用 LLM。Recommendation 包含 Action / Confidence / Reason / Risk / Position Suggestion / Expire Time。

## Domain

Recommendation, Strategy

## Tasks

### Backend

- [ ] 创建 Recommendation 实体 (domain/entities/recommendation.py)
- [ ] 创建 RuleEngine 接口 (domain/services/rule_engine.py)
- [ ] 创建 MockRuleEngine 实现（基于持仓/市场数据生成规则推荐）
- [ ] 创建 RecommendationService (application/services/recommendation_service.py)
- [ ] 创建 GET /api/v1/recommendations 接口
- [ ] 数据库迁移：recommendations 表
- [ ] 单元测试

### Frontend

- [ ] 创建 Recommendation 页面
- [ ] 创建 RecommendationCard 组件（单条推荐展示）
- [ ] 创建 RecommendationAction 组件（Action / Confidence / Risk 展示）
- [ ] 创建 PositionSuggestion 组件（仓位建议展示）

## Mock Rule Examples

- 市场温度 > 70 → 推荐增仓
- 市场温度 < 30 → 推荐减仓
- 持仓浮亏 > 10% → 建议止损
- 持仓集中度 > 30% → 建议分散

## Acceptance Criteria

- GET /api/v1/recommendations 返回基于规则的推荐
- 推荐包含 Action / Confidence / Reason / Risk / Position Suggestion
- 不调用 LLM
- 前端正确展示推荐卡片

## References

- [RFC-001](../rfc/RFC-001-sprint-1-foundation-development-plan.md)
