import random

from app.models.schemas import CurrentScan


class MockMLScheduler:
    """Local scheduler substitute for integration testing only."""

    def __init__(self) -> None:
        self.bands = [900, 1800, 2450, 3500, 5800]

    def get_next_scan(self) -> CurrentScan:
        band = random.choice(self.bands)
        dwell_ms = random.choice([50, 100, 150, 200])
        priority = round(random.uniform(0.40, 0.99), 2)
        return CurrentScan(band=band, dwell_ms=dwell_ms, priority=priority)
