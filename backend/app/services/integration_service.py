from asyncio import Lock

from app.integrations.analytics_contract import AnalyticsAdapter
from app.integrations.contracts import SimulatorAdapter
from app.integrations.scheduler_contract import SchedulerAdapter
from app.models.schemas import (
    CurrentScan,
    DashboardResponse,
    DetectionEvent,
    Metrics,
    ScanEvent,
    SimulationState,
)
from app.services.websocket_manager import ws_manager
from app.state.simulation_state import store


class IntegrationService:
    """Single stable communication layer between the Python modules and FastAPI."""

    def __init__(self) -> None:
        self.simulator: SimulatorAdapter | None = None
        self.scheduler: SchedulerAdapter | None = None
        self.analytics: AnalyticsAdapter | None = None
        self._lifecycle_lock = Lock()

    def set_simulator(self, simulator: SimulatorAdapter) -> None:
        self.simulator = simulator

    def set_scheduler(self, scheduler: SchedulerAdapter) -> None:
        self.scheduler = scheduler

    def set_analytics(self, analytics: AnalyticsAdapter) -> None:
        self.analytics = analytics

    def configure_scheduler_backed_simulator(self) -> None:
        """Connect a simulator's optional scan-provider hook to the scheduler."""
        if self.scheduler is None or self.simulator is None:
            return
        setter = getattr(self.simulator, "set_scan_provider", None)
        if setter is not None:
            setter(self.get_next_scan)

    async def start_simulation(self) -> str:
        async with self._lifecycle_lock:
            if store.running:
                return store.simulation_id
            if self.simulator is None:
                raise RuntimeError("Simulator is not configured")
            if self.analytics is not None:
                self.analytics.reset()
            simulation_id = store.start_new()
            self.configure_scheduler_backed_simulator()
            try:
                self.simulator.start(self.update_scan)
            except Exception:
                store.stop()
                raise
            return simulation_id

    async def stop_simulation(self) -> None:
        async with self._lifecycle_lock:
            if self.simulator is not None:
                self.simulator.stop()
            store.stop()

    def get_next_scan(self) -> CurrentScan:
        if self.scheduler is None:
            raise RuntimeError("Scheduler is not configured")
        scan = self.scheduler.get_next_scan()
        store.current_scan = scan
        self._upsert_band_priority(scan)
        return scan

    def _upsert_band_priority(self, scan: CurrentScan) -> None:
        for index, existing in enumerate(store.band_priorities):
            if existing.band == scan.band:
                store.band_priorities[index] = scan
                return
        store.band_priorities.append(scan)

    def get_state(self) -> SimulationState:
        return store.state

    def get_dashboard(self) -> DashboardResponse:
        return DashboardResponse(
            metrics=store.metrics,
            current_scan=store.current_scan,
            band_priorities=store.band_priorities,
            timeline=store.timeline[-200:],
            detections=store.detections[-200:],
        )

    async def update_scan(self, scan: CurrentScan, state: SimulationState, result: str) -> None:
        store.current_scan = scan
        self._upsert_band_priority(scan)
        store.state = state

        store.timeline.append(
            ScanEvent(
                time=state.time,
                band=state.current_band,
                dwell_ms=state.dwell_ms,
                priority=scan.priority,
                result=result,
            )
        )

        if result == "hit":
            store.detections.append(
                DetectionEvent(
                    time=state.time,
                    band=state.current_band,
                    confidence=scan.priority,
                )
            )

        if self.analytics is not None:
            self.analytics.record_scan(scan, state, result)
            store.metrics = self.analytics.get_metrics()

        await ws_manager.broadcast(
            {
                "type": "scan_update",
                "time": state.time,
                "band": state.current_band,
                "dwell_ms": state.dwell_ms,
                "priority": scan.priority,
                "result": result,
            }
        )

    def add_scan_event(self, event: ScanEvent) -> None:
        store.timeline.append(event)

    def add_detection(self, event: DetectionEvent) -> None:
        store.detections.append(event)

    def update_metrics(self, metrics: Metrics) -> None:
        store.metrics = metrics


integration_service = IntegrationService()
