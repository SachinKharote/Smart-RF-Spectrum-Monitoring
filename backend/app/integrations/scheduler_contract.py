from typing import Protocol

from app.models.schemas import CurrentScan


class SchedulerAdapter(Protocol):
    """The gateway consumes normalized scheduler output and knows nothing about ML logic."""

    def get_next_scan(self) -> CurrentScan:
        ...
