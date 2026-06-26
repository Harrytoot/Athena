from dataclasses import dataclass, field


LONG_THRESHOLD = 60
SHORT_THRESHOLD = 40


@dataclass
class SignalSeries:
    timestamps: list
    scores: list[float] = field(default_factory=list)
    signals: list[int] = field(default_factory=list)
    states: list[str] = field(default_factory=list)


def generate_signal(score: float) -> int:
    if score >= LONG_THRESHOLD:
        return 1
    if score <= SHORT_THRESHOLD:
        return -1
    return 0


def generate_series(scores: list[float]) -> list[int]:
    return [generate_signal(s) for s in scores]
