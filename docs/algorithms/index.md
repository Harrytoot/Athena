# Athena 算法库

> 本目录包含 Athena 投资系统的核心算法文档与实现规范。
> 当前版本: V1 (规则驱动，无 AI 自学习)

## 目录结构

| 分类 | 路径 | 描述 |
|------|------|------|
| 技术指标 | [01-technical_indicators/](./01-technical_indicators/) | MA, MACD, RSI, KDJ, 布林带等 |
| 基本面因子 | [02-fundamental_factors/](./02-fundamental_factors/) | PE, PB, ROE, 增速, 质量因子等 |
| 情绪指标 | [03-sentiment_analysis/](./03-sentiment_analysis/) | 涨跌停统计, 涨停板/开板率, 北向资金等 |
| 投资组合优化 | [04-portfolio_optimization/](./04-portfolio_optimization/) | 马科维茨, 风险平价, 最大夏普比等 |

## 已有算法

- [ALG-001: 市场综合评分 V1](./ALG-001-market-score-v1.md) — 五维度市场评分体系

## 规范

- 每个算法以独立文档呈现，命名格式: `ALG-{序号}-{简要描述}.md`
- 文档必须包含: 公式定义, 数据来源, 参数说明, API 契约, 测试要求
- V1 阶段: 固定权重, 不可自学习, 所有子评分必须可解释
