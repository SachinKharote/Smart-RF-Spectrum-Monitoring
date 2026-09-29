import asyncio
import random
from typing import Awaitable, Callable, Optional

from app.models.schemas import CurrentScan, SimulationState
from app.integrations.contracts import ScanCallback


class MockRFSimulator:
    """Local-only simulator used to exercise the complete integration path."""

    def __init__(self, scan_provider: Callable[[], CurrentScan]) -> None:
        self.running = False
        self._task: Optional[asyncio.Task] = None
        self._simulation_id = "SIM001"
        self._time = 0.0
        self._scan_provider = scan_provider

    def set_scan_provider(self, provider: Callable[[], CurrentScan]) -> None:
        self._scan_provider = provider

    def start(self, on_scan: ScanCallback) -> str:
        if self.running:
            return self._simulation_id

        self.running = True
        self._time = 0.0
        self._task = asyncio.create_task(self._run(on_scan))
        return self._simulation_id

    def stop(self) -> None:
        self.running = False
        if self._task and not self._task.done():
            self._task.cancel()
        self._task = None

    async def _run(self, on_scan: ScanCallback) -> None:
        try:
            while self.running:
                scan = self._scan_provider()
                result = random.choice(["hit", "miss", "miss", "hit"])
                self._time = round(self._time + scan.dwell_ms / 1000, 2)
                state = SimulationState(
                    time=self._time,
                    current_band=scan.band,
                    dwell_ms=scan.dwell_ms,
                    result=result,
                )
                await on_scan(scan, state, result)
                await asyncio.sleep(scan.dwell_ms / 1000)
        except asyncio.CancelledError:
            pass
