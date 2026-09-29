from __future__ import annotations

from typing import Protocol, Sequence

from app.core.models import Band, BandHistory, Prediction


class PredictionProvider(Protocol):
    """Contract for the ML teammate's prediction module.

    The prediction provider returns a likely next band and confidence. It does
    not own receiver control, scheduling, metrics, or API behavior.
    """

    def predict_next(
        self,
        *,
        bands: Sequence[Band],
        history: dict[int, BandHistory],
        current_time_seconds: float,
    ) -> Prediction: ...
