from __future__ import annotations

from typing import Sequence

from app.core.models import Band, BandHistory, Prediction


class HistoryAwareMockPredictor:
    """Development substitute for Member 1's ML model.

    It deliberately does not claim to be ML. It uses baseline band priority and
    recent hit rate so the rest of the system can be exercised end-to-end.
    """

    def __init__(self, recency_bonus: float = 3.0) -> None:
        self.recency_bonus = recency_bonus

    def predict_next(
        self,
        *,
        bands: Sequence[Band],
        history: dict[int, BandHistory],
        current_time_seconds: float,
    ) -> Prediction:
        if not bands:
            return Prediction(None, 0.0, source="mock")

        scores: list[tuple[int, float]] = []
        for band in bands:
            h = history.get(band.band_id, BandHistory())
            score = float(band.priority) + self.recency_bonus * h.hit_rate
            scores.append((band.band_id, score))

        scores.sort(key=lambda item: (-item[1], item[0]))
        predicted_band, best_score = scores[0]
        total = sum(max(score, 0.0) for _, score in scores)
        confidence = best_score / total if total else 0.0

        return Prediction(
            predicted_band_id=predicted_band,
            confidence=round(min(max(confidence, 0.0), 1.0), 4),
            predicted_time_seconds=current_time_seconds,
            source="mock-history",
        )
