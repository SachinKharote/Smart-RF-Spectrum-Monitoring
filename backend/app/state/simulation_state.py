from dataclasses import dataclass, field
from typing import List

from app.models.schemas import CurrentScan, DetectionEvent, Metrics, ScanEvent, SimulationState


@dataclass
class SimulationStore:
    simulation_id: str = "SIM001"
    running: bool = False
    _sequence: int = 1
    state: SimulationState = field(default_factory=SimulationState)
    metrics: Metrics = field(default_factory=Metrics)
    current_scan: CurrentScan = field(default_factory=CurrentScan)
    band_priorities: List[CurrentScan] = field(default_factory=list)
    timeline: List[ScanEvent] = field(default_factory=list)
    detections: List[DetectionEvent] = field(default_factory=list)

    def start_new(self) -> str:
        self.simulation_id = f"SIM{self._sequence:03d}"
        self._sequence += 1
        self.running = True
        self.state = SimulationState()
        self.metrics = Metrics()
        self.current_scan = CurrentScan()
        self.band_priorities.clear()
        self.timeline.clear()
        self.detections.clear()
        return self.simulation_id

    def stop(self) -> None:
        self.running = False


store = SimulationStore()
