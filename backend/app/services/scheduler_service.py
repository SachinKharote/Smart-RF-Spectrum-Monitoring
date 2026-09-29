from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Optional

from app.core.models import Band, BandHistory, Prediction, ScanDecision, ScanObservation


@dataclass
class SchedulerConfig:
    exploitation_weight: float = 0.55
    history_weight: float = 0.25
    prediction_weight: float = 0.20
    exploration_probability: float = 0.20
    recency_window_seconds: float = 5.0

    def validate(self) -> None:
        for name in (
            "exploitation_weight",
            "history_weight",
            "prediction_weight",
            "exploration_probability",
        ):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")
        if self.recency_window_seconds <= 0:
            raise ValueError("recency_window_seconds must be greater than 0")


class SequentialScheduler:
    """Traditional deterministic round-robin baseline."""

    def __init__(self, bands: Iterable[Band]):
        self._bands = list(bands)
        if not self._bands:
            raise ValueError("At least one band is required")
        self._index = 0
        self._sequence = 0

    def reset(self) -> None:
        self._index = 0
        self._sequence = 0

    @property
    def index(self) -> int:
        return self._index

    @property
    def band_count(self) -> int:
        return len(self._bands)

    def next_scan(self) -> ScanDecision:
        band = self._bands[self._index % len(self._bands)]
        self._index += 1
        self._sequence += 1
        return ScanDecision(
            band_id=band.band_id,
            strategy="Sequential",
            priority=float(band.priority),
            reason="Round-robin baseline",
            sequence_number=self._sequence,
            score=float(band.priority),
        )


class SmartScheduler:
    """Adaptive scheduler owned by Member 3.

    It combines ML prediction, historical feedback, baseline priority and
    controlled exploration. The ML implementation is injected through the
    PredictionProvider contract.
    """

    def __init__(
        self,
        bands: Iterable[Band],
        predictor,
        config: Optional[SchedulerConfig] = None,
        rng: Optional[random.Random] = None,
    ) -> None:
        self._bands = list(bands)
        if not self._bands:
            raise ValueError("At least one band is required")
        self.predictor = predictor
        self.config = config or SchedulerConfig()
        self.config.validate()
        self._rng = rng or random.Random(42)
        self._sequence = 0
        self.history: dict[int, BandHistory] = {
            band.band_id: BandHistory() for band in self._bands
        }
        self._last_decision: Optional[ScanDecision] = None

    def reset(self) -> None:
        self._sequence = 0
        self.history = {band.band_id: BandHistory() for band in self._bands}
        self._last_decision = None

    @property
    def last_decision(self) -> Optional[ScanDecision]:
        return self._last_decision

    def predict(self, current_time_seconds: float) -> Prediction:
        return self.predictor.predict_next(
            bands=self._bands,
            history=self.history,
            current_time_seconds=current_time_seconds,
        )

    def next_scan(
        self,
        *,
        current_time: datetime,
        current_time_seconds: float,
        prediction: Optional[Prediction] = None,
    ) -> tuple[ScanDecision, Prediction]:
        prediction = prediction or self.predict(current_time_seconds)
        predicted_band = prediction.predicted_band_id

        scored: list[tuple[Band, float]] = []
        for band in self._bands:
            h = self.history[band.band_id]
            priority_component = float(band.priority) / 5.0
            history_component = min(h.hit_rate, 1.0)

            recency_component = 0.0
            if h.last_hit_time is not None:
                elapsed = max((current_time - h.last_hit_time).total_seconds(), 0.0)
                if elapsed < self.config.recency_window_seconds:
                    recency_component = 1.0 - elapsed / self.config.recency_window_seconds

            prediction_component = 1.0 if predicted_band == band.band_id else 0.0

            score = (
                self.config.exploitation_weight * priority_component
                + self.config.history_weight * (0.7 * history_component + 0.3 * recency_component)
                + self.config.prediction_weight * prediction_component * prediction.confidence
            )
            scored.append((band, score))

        scored.sort(key=lambda item: (-item[1], item[0].band_id))
        explore = self._rng.random() < self.config.exploration_probability
        if explore:
            band = self._rng.choice(self._bands)
            reason = "Exploration: random band sampled while preserving learned state"
            score = next(s for b, s in scored if b.band_id == band.band_id)
        else:
            band, score = scored[0]
            reason = "Exploitation: priority + history + ML prediction"

        self._sequence += 1
        decision = ScanDecision(
            band_id=band.band_id,
            strategy="Smart",
            priority=float(band.priority),
            reason=reason,
            sequence_number=self._sequence,
            score=round(score, 4),
            predicted_band_id=predicted_band,
            prediction_confidence=prediction.confidence,
        )
        self._last_decision = decision
        return decision, prediction

    def apply_feedback(self, observation: ScanObservation) -> None:
        h = self.history[observation.band_id]
        h.scans += 1
        h.last_result_time = observation.scan_time
        if observation.result == "hit":
            h.hits += 1
            h.last_hit_time = observation.scan_time
        elif observation.result == "miss":
            h.misses += 1
        elif observation.result == "false_alarm":
            h.false_alarms += 1
        elif observation.result == "clear":
            h.clears += 1

    def history_snapshot(self) -> list[dict]:
        return [
            {
                "band": band.band_id,
                "scans": self.history[band.band_id].scans,
                "hits": self.history[band.band_id].hits,
                "misses": self.history[band.band_id].misses,
                "false_alarms": self.history[band.band_id].false_alarms,
                "clears": self.history[band.band_id].clears,
                "hit_rate": round(self.history[band.band_id].hit_rate, 4),
                "last_hit_time": (
                    self.history[band.band_id].last_hit_time.isoformat()
                    if self.history[band.band_id].last_hit_time
                    else None
                ),
            }
            for band in self._bands
        ]
