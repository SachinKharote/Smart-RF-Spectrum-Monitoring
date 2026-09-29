from typing import Protocol

from app.models.schemas import CurrentScan, Metrics, SimulationState


class AnalyticsAdapter(Protocol):
    """Contract for the analytics engine.

    The gateway supplies normalized scan events and consumes the resulting metrics.
    Analytics calculations remain inside the analytics implementation.
    """

    def reset(self) -> None:
        ...

    def record_scan(self, scan: CurrentScan, state: SimulationState, result: str) -> None:
        ...

    def get_metrics(self) -> Metrics:
        ...
