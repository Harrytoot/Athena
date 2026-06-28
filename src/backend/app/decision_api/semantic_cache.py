import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.decision_semantics.registry import DEFAULT_SEMANTIC_VERSION
from app.decision_semantics.schema import DecisionSemantic


def _make_hash(symbol: str, score_values: dict, registry_version: str, timestamp_bucket: str) -> str:
    payload = {
        "symbol": symbol,
        "score_values": score_values,
        "registry_version": registry_version,
        "timestamp_bucket": timestamp_bucket,
    }
    raw = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class SemanticCache:
    _store: dict[str, DecisionSemantic] = {}

    def get(
        self,
        symbol: str,
        score_values: dict,
        registry_version: str = DEFAULT_SEMANTIC_VERSION,
        timestamp_bucket: str | None = None,
    ) -> DecisionSemantic | None:
        bucket = timestamp_bucket or _default_timestamp_bucket()
        key = _make_hash(symbol, score_values, registry_version, bucket)
        return self._store.get(key)

    def set(
        self,
        symbol: str,
        score_values: dict,
        semantic: DecisionSemantic,
        registry_version: str = DEFAULT_SEMANTIC_VERSION,
        timestamp_bucket: str | None = None,
    ) -> str:
        bucket = timestamp_bucket or _default_timestamp_bucket()
        key = _make_hash(symbol, score_values, registry_version, bucket)
        self._store[key] = semantic
        return key

    def clear(self) -> None:
        self._store.clear()

    @property
    def size(self) -> int:
        return len(self._store)


def _default_timestamp_bucket() -> str:
    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%dT%H")
