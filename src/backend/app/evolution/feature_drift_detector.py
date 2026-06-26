import math
from dataclasses import dataclass, field
from datetime import datetime

from app.feature_store.repository import FeatureItem


@dataclass
class FeatureDriftPoint:
    feature_name: str
    category: str
    observation_count: int
    early_mean: float
    late_mean: float
    early_std: float
    late_std: float
    mean_shift: float
    volatility_change: float
    drift_score: float
    decay_trend: float
    importance_decay_rate: float
    confidence_erosion: float
    assessment: str


@dataclass
class FeatureDriftReport:
    drift_points: list[FeatureDriftPoint] = field(default_factory=list)
    overall_drift_score: float = 0.0
    most_drifted_features: list[str] = field(default_factory=list)
    stable_features: list[str] = field(default_factory=list)
    critical_decay_features: list[str] = field(default_factory=list)
    assessment: str = ""

    @property
    def has_critical_drift(self) -> bool:
        return len(self.critical_decay_features) > 0

    @property
    def drift_severity(self) -> str:
        if self.overall_drift_score >= 0.7:
            return "high"
        if self.overall_drift_score >= 0.4:
            return "medium"
        return "low"


class FeatureDriftDetector:

    def __init__(
        self,
        window_ratio: float = 0.4,
        drift_threshold: float = 0.5,
        min_observations: int = 10,
        critical_decay_threshold: float = 0.7,
    ):
        self.window_ratio = window_ratio
        self.drift_threshold = drift_threshold
        self.min_observations = min_observations
        self.critical_decay_threshold = critical_decay_threshold

    def detect(self, feature_history: list[FeatureItem]) -> FeatureDriftReport:
        if not feature_history:
            return FeatureDriftReport(assessment="无特征历史数据")

        grouped = self._group_by_feature(feature_history)

        drift_points: list[FeatureDriftPoint] = []
        for name, items in grouped.items():
            point = self._analyze_feature(name, items)
            if point:
                drift_points.append(point)

        drift_points.sort(key=lambda p: p.drift_score, reverse=True)

        overall_score = self._compute_overall_drift(drift_points)
        most_drifted = [p.feature_name for p in drift_points if p.drift_score >= self.drift_threshold]
        stable = [p.feature_name for p in drift_points if p.drift_score < self.drift_threshold]
        critical_decay = [p.feature_name for p in drift_points if p.drift_score >= self.critical_decay_threshold]
        assessment = self._assess_drift(drift_points, overall_score)

        return FeatureDriftReport(
            drift_points=drift_points,
            overall_drift_score=round(overall_score, 4),
            most_drifted_features=most_drifted,
            stable_features=stable,
            critical_decay_features=critical_decay,
            assessment=assessment,
        )

    def _group_by_feature(
        self, features: list[FeatureItem]
    ) -> dict[str, list[FeatureItem]]:
        grouped: dict[str, list[FeatureItem]] = {}
        for f in features:
            if f.name not in grouped:
                grouped[f.name] = []
            grouped[f.name].append(f)
        for name in grouped:
            grouped[name].sort(key=lambda x: x.timestamp)
        return grouped

    def _analyze_feature(
        self, name: str, items: list[FeatureItem]
    ) -> FeatureDriftPoint | None:
        n = len(items)
        if n < self.min_observations:
            return None

        values = [item.value for item in items]
        timestamps = [item.timestamp for item in items]
        confidences = [item.confidence for item in items]
        category = items[0].category

        split_idx = max(int(n * (1.0 - self.window_ratio)), self.min_observations // 2)
        early_values = values[:split_idx]
        late_values = values[split_idx:]

        early_mean = sum(early_values) / len(early_values) if early_values else 0.0
        late_mean = sum(late_values) / len(late_values) if late_values else 0.0

        early_std = self._compute_std(early_values, early_mean)
        late_std = self._compute_std(late_values, late_mean)

        mean_shift = 0.0
        pooled_std = (early_std + late_std) / 2.0 if (early_std + late_std) > 0 else 0.001
        mean_shift = abs(late_mean - early_mean) / pooled_std
        mean_shift = min(mean_shift, 5.0)

        volatility_change = late_std / early_std if early_std > 0 else 1.0
        volatility_change = max(0.1, min(volatility_change, 10.0))

        decay_trend = self._compute_trend(values)

        importance_decay = self._compute_importance_decay(values, early_std)

        conf_erosion = 0.0
        if confidences:
            early_conf = sum(confidences[:split_idx]) / split_idx if split_idx > 0 else 1.0
            late_conf = sum(confidences[split_idx:]) / (n - split_idx) if n > split_idx else 1.0
            conf_erosion = max(0.0, early_conf - late_conf)

        drift_score = self._compute_drift_score(
            mean_shift, volatility_change, abs(decay_trend), importance_decay, conf_erosion
        )

        assessment = self._assess_feature(
            name, drift_score, mean_shift, volatility_change, decay_trend
        )

        return FeatureDriftPoint(
            feature_name=name,
            category=category,
            observation_count=n,
            early_mean=round(early_mean, 6),
            late_mean=round(late_mean, 6),
            early_std=round(early_std, 6),
            late_std=round(late_std, 6),
            mean_shift=round(mean_shift, 4),
            volatility_change=round(volatility_change, 4),
            drift_score=round(drift_score, 4),
            decay_trend=round(decay_trend, 6),
            importance_decay_rate=round(importance_decay, 4),
            confidence_erosion=round(conf_erosion, 4),
            assessment=assessment,
        )

    def _compute_std(self, values: list[float], mean: float) -> float:
        n = len(values)
        if n < 2:
            return 0.0
        variance = sum((v - mean) ** 2 for v in values) / (n - 1)
        return math.sqrt(max(0.0, variance))

    def _compute_trend(self, values: list[float]) -> float:
        n = len(values)
        if n < 2:
            return 0.0
        x_mean = (n - 1) / 2.0
        y_mean = sum(values) / n
        numerator = sum((i - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        if denominator == 0:
            return 0.0
        slope = numerator / denominator
        if y_mean != 0:
            slope = slope / abs(y_mean)
        return max(-5.0, min(slope, 5.0))

    def _compute_importance_decay(
        self, values: list[float], early_std: float
    ) -> float:
        n = len(values)
        if n < self.min_observations:
            return 0.0

        half = n // 2
        first_half = values[:half]
        second_half = values[half:]

        def signal_to_noise(vals: list[float]) -> float:
            if len(vals) < 2:
                return 0.0
            m = sum(vals) / len(vals)
            s = self._compute_std(vals, m)
            return abs(m) / s if s > 0 else 0.0

        snr_early = signal_to_noise(first_half)
        snr_late = signal_to_noise(second_half)

        if snr_early <= 0:
            return 0.0
        decay = 1.0 - (snr_late / snr_early)
        return max(0.0, min(1.0, decay))

    def _compute_drift_score(
        self,
        mean_shift: float,
        volatility_change: float,
        abs_trend: float,
        importance_decay: float,
        confidence_erosion: float,
    ) -> float:
        mean_component = min(1.0, mean_shift / 3.0) * 0.30

        vol_component = 0.0
        if volatility_change >= 1.0:
            vol_component = min(1.0, (volatility_change - 1.0) / 2.0) * 0.25
        else:
            vol_component = min(1.0, abs(1.0 - volatility_change)) * 0.25
        vol_component = vol_component * 0.25

        trend_component = min(1.0, abs_trend / 0.5) * 0.20

        importance_component = importance_decay * 0.15

        confidence_component = confidence_erosion * 0.10

        score = mean_component + vol_component + trend_component + importance_component + confidence_component
        return min(1.0, max(0.0, score))

    def _compute_overall_drift(self, points: list[FeatureDriftPoint]) -> float:
        if not points:
            return 0.0
        return sum(p.drift_score for p in points) / len(points)

    def _assess_feature(
        self,
        name: str,
        drift_score: float,
        mean_shift: float,
        volatility_change: float,
        decay_trend: float,
    ) -> str:
        parts: list[str] = []

        if drift_score >= 0.7:
            parts.append(f"特征 {name}: 严重漂移")
        elif drift_score >= 0.5:
            parts.append(f"特征 {name}: 显著漂移")
        elif drift_score >= 0.3:
            parts.append(f"特征 {name}: 轻微漂移")
        else:
            parts.append(f"特征 {name}: 稳定")

        if mean_shift > 2.0:
            parts.append("均值大幅偏移")
        elif mean_shift > 1.0:
            parts.append("均值偏移明显")

        if volatility_change > 2.0:
            parts.append("波动率显著变化")
        elif volatility_change > 1.5 or volatility_change < 0.5:
            parts.append("波动率变化")

        if abs(decay_trend) > 0.1:
            direction = "上升" if decay_trend > 0 else "下降"
            parts.append(f"趋势{direction}")

        return " | ".join(parts)

    def _assess_drift(
        self, points: list[FeatureDriftPoint], overall_score: float
    ) -> str:
        parts: list[str] = []

        if overall_score >= 0.7:
            parts.append("特征漂移: 严重")
        elif overall_score >= 0.5:
            parts.append("特征漂移: 显著")
        elif overall_score >= 0.3:
            parts.append("特征漂移: 轻微")
        else:
            parts.append("特征漂移: 正常")

        parts.append(f"综合漂移评分: {overall_score:.2f}")

        drifted = [p for p in points if p.drift_score >= 0.5]
        if drifted:
            parts.append(f"漂移特征数: {len(drifted)}")
            names = ", ".join(p.feature_name for p in drifted[:3])
            parts.append(f"主要漂移特征: {names}")
        else:
            parts.append("所有特征稳定")

        return " | ".join(parts)
