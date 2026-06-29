import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.strategy_service import StrategyService
from app.infrastructure.persistence.repositories.strategy_repository import StrategyRepositoryImpl

logger = logging.getLogger(__name__)

MOMENTUM_STRATEGY = {
    "name": "动量突破策略",
    "description": "基于移动平均线金叉信号的趋势跟踪策略。当短期均线上穿长期均线时产生买入信号，适合趋势市场。",
    "category": "momentum_strategy",
    "is_template": True,
    "nodes": [
        {
            "id": "ds_mom",
            "type": "strategyNode",
            "position": {"x": 250, "y": 0},
            "data": {
                "category": "datasource",
                "label": "数据源",
                "sublabel": "行情 / 基本面",
                "properties": {"symbol": "000001", "frequency": "daily", "lookback": 200},
            },
        },
        {
            "id": "ma_ind",
            "type": "strategyNode",
            "position": {"x": 250, "y": 150},
            "data": {
                "category": "indicator",
                "label": "移动平均 MA",
                "sublabel": "趋势跟踪",
                "properties": {"period": 20, "source": "close"},
            },
        },
        {
            "id": "cross_sig",
            "type": "strategyNode",
            "position": {"x": 250, "y": 300},
            "data": {
                "category": "signal",
                "label": "交叉信号",
                "sublabel": "金叉 / 死叉",
                "properties": {"threshold": 60, "comparison": "cross_above"},
            },
        },
        {
            "id": "stop_risk",
            "type": "strategyNode",
            "position": {"x": 250, "y": 450},
            "data": {
                "category": "risk",
                "label": "止损止盈",
                "sublabel": "风控规则",
                "properties": {"stopLoss": 0.05, "takeProfit": 0.15, "positionSize": 0.2},
            },
        },
        {
            "id": "exec_mkt",
            "type": "strategyNode",
            "position": {"x": 250, "y": 600},
            "data": {
                "category": "execution",
                "label": "市价执行",
                "sublabel": "订单执行",
                "properties": {"orderType": "market", "slippage": 0.001},
            },
        },
    ],
    "edges": [
        {"id": "e0", "source": "ds_mom", "sourceHandle": "source", "target": "ma_ind", "targetHandle": "indicator_in"},
        {"id": "e1", "source": "ma_ind", "sourceHandle": "indicator_out", "target": "cross_sig", "targetHandle": "signal_in"},
        {"id": "e2", "source": "cross_sig", "sourceHandle": "signal_out", "target": "stop_risk", "targetHandle": "risk_in"},
        {"id": "e3", "source": "stop_risk", "sourceHandle": "risk_out", "target": "exec_mkt", "targetHandle": "execution_in"},
    ],
}

MEAN_REVERSION_STRATEGY = {
    "name": "均值回归策略",
    "description": "基于RSI超买超卖的均值回归策略。当RSI进入超卖区时买入，进入超买区时卖出，适合震荡市场。",
    "category": "mean_reversion_strategy",
    "is_template": True,
    "nodes": [
        {
            "id": "ds_mr",
            "type": "strategyNode",
            "position": {"x": 250, "y": 0},
            "data": {
                "category": "datasource",
                "label": "数据源",
                "sublabel": "行情 / 基本面",
                "properties": {"symbol": "000001", "frequency": "daily", "lookback": 200},
            },
        },
        {
            "id": "rsi_ind",
            "type": "strategyNode",
            "position": {"x": 250, "y": 150},
            "data": {
                "category": "indicator",
                "label": "相对强弱 RSI",
                "sublabel": "超买超卖",
                "properties": {"period": 14, "overbought": 70, "oversold": 30},
            },
        },
        {
            "id": "thresh_sig",
            "type": "strategyNode",
            "position": {"x": 250, "y": 300},
            "data": {
                "category": "signal",
                "label": "阈值信号",
                "sublabel": "数值比较",
                "properties": {"threshold": 50, "operator": "gte"},
            },
        },
        {
            "id": "stop_risk",
            "type": "strategyNode",
            "position": {"x": 250, "y": 450},
            "data": {
                "category": "risk",
                "label": "止损止盈",
                "sublabel": "风控规则",
                "properties": {"stopLoss": 0.05, "takeProfit": 0.10, "positionSize": 0.15},
            },
        },
        {
            "id": "exec_mkt",
            "type": "strategyNode",
            "position": {"x": 250, "y": 600},
            "data": {
                "category": "execution",
                "label": "市价执行",
                "sublabel": "订单执行",
                "properties": {"orderType": "market", "slippage": 0.001},
            },
        },
    ],
    "edges": [
        {"id": "e0", "source": "ds_mr", "sourceHandle": "source", "target": "rsi_ind", "targetHandle": "indicator_in"},
        {"id": "e1", "source": "rsi_ind", "sourceHandle": "indicator_out", "target": "thresh_sig", "targetHandle": "signal_in"},
        {"id": "e2", "source": "thresh_sig", "sourceHandle": "signal_out", "target": "stop_risk", "targetHandle": "risk_in"},
        {"id": "e3", "source": "stop_risk", "sourceHandle": "risk_out", "target": "exec_mkt", "targetHandle": "execution_in"},
    ],
}

VOLATILITY_BREAKOUT_STRATEGY = {
    "name": "波动率突破策略",
    "description": "基于MACD柱状图变化的波动率突破策略。通过检测MACD动能柱的扩张和收缩来判断趋势启动和衰竭，适合波动率较高的市场环境。",
    "category": "volatility_breakout_strategy",
    "is_template": True,
    "nodes": [
        {
            "id": "ds_vb",
            "type": "strategyNode",
            "position": {"x": 250, "y": 0},
            "data": {
                "category": "datasource",
                "label": "数据源",
                "sublabel": "行情 / 基本面",
                "properties": {"symbol": "000001", "frequency": "daily", "lookback": 200},
            },
        },
        {
            "id": "macd_ind",
            "type": "strategyNode",
            "position": {"x": 250, "y": 150},
            "data": {
                "category": "indicator",
                "label": "MACD",
                "sublabel": "趋势动能",
                "properties": {"fast": 12, "slow": 26, "signal": 9},
            },
        },
        {
            "id": "cross_sig",
            "type": "strategyNode",
            "position": {"x": 250, "y": 300},
            "data": {
                "category": "signal",
                "label": "交叉信号",
                "sublabel": "金叉 / 死叉",
                "properties": {"threshold": 60, "comparison": "cross_above"},
            },
        },
        {
            "id": "stop_risk",
            "type": "strategyNode",
            "position": {"x": 250, "y": 450},
            "data": {
                "category": "risk",
                "label": "止损止盈",
                "sublabel": "风控规则",
                "properties": {"stopLoss": 0.07, "takeProfit": 0.20, "positionSize": 0.25},
            },
        },
        {
            "id": "exec_mkt",
            "type": "strategyNode",
            "position": {"x": 250, "y": 600},
            "data": {
                "category": "execution",
                "label": "市价执行",
                "sublabel": "订单执行",
                "properties": {"orderType": "market", "slippage": 0.001},
            },
        },
    ],
    "edges": [
        {"id": "e0", "source": "ds_vb", "sourceHandle": "source", "target": "macd_ind", "targetHandle": "indicator_in"},
        {"id": "e1", "source": "macd_ind", "sourceHandle": "indicator_out", "target": "cross_sig", "targetHandle": "signal_in"},
        {"id": "e2", "source": "cross_sig", "sourceHandle": "signal_out", "target": "stop_risk", "targetHandle": "risk_in"},
        {"id": "e3", "source": "stop_risk", "sourceHandle": "risk_out", "target": "exec_mkt", "targetHandle": "execution_in"},
    ],
}

DEFAULT_STRATEGIES = [MOMENTUM_STRATEGY, MEAN_REVERSION_STRATEGY, VOLATILITY_BREAKOUT_STRATEGY]


class StrategySeeder:

    async def seed(self, session: AsyncSession, user_id: str) -> list[str]:
        repo = StrategyRepositoryImpl(session)
        service = StrategyService(repo)

        existing = await service.list_templates()
        if len(existing) >= 3:
            logger.info("Strategy templates already seeded (%d found), skipping", len(existing))
            return [s.id for s in existing]

        created_ids: list[str] = []
        for template in DEFAULT_STRATEGIES:
            from app.application.dtos.strategy_dtos import StrategyCreateRequest

            req = StrategyCreateRequest(
                name=template["name"],
                description=template["description"],
                category=template["category"],
                nodes=template["nodes"],
                edges=template["edges"],
                is_template=template["is_template"],
            )
            response = await service.create_strategy(user_id, req)
            created_ids.append(response.id)
            logger.info("Seeded strategy template: %s", template["name"])

        logger.info("Strategy seeding complete: %d templates created", len(created_ids))
        return created_ids


def get_strategy_seeder() -> StrategySeeder:
    return StrategySeeder()
