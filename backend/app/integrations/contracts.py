from typing import Awaitable, Callable, Protocol

from app.models.schemas import CurrentScan, SimulationState


ScanCallback = Callable[[CurrentScan, SimulationState, str], Awaitable[None]]


class SimulatorAdapter(Protocol):
    """Minimal contract the real RF simulator must implement."""

    def start(self, on_scan: ScanCallback) -> str:
        """Start simulation and invoke on_scan for each normalized scan event."""
        ...

    def stop(self) -> None:
        """Stop simulation and release simulator resources."""
        ...


class ConfigurableSimulatorAdapter(SimulatorAdapter, Protocol):
    """Optional extension used when the simulator wants the scheduler to choose scans."""

    def set_scan_provider(self, provider: Callable[[], CurrentScan]) -> None:
        ...
