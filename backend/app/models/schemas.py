from typing import List, Literal
from pydantic import BaseModel, Field, ConfigDict


SimulationResult = Literal["hit", "miss", "idle"]
SimulationStatus = Literal["running", "stopped", "idle"]


class SimulationStartResponse(BaseModel):
    simulation_id: str
    status: Literal["running", "stopped"]


class SimulationStopResponse(BaseModel):
    simulation_id: str
    status: Literal["running", "stopped"]


class SimulationState(BaseModel):
    time: float = 0.0
    current_band: int = 0
    dwell_ms: int = 0
    result: SimulationResult = "idle"


class Metrics(BaseModel):
    detection_rate: float = 0.0
    false_alarm_rate: float = 0.0
    avg_intercept_time: float = 0.0


class CurrentScan(BaseModel):
    band: int = 0
    dwell_ms: int = 0
    priority: float = Field(default=0.0, ge=0.0, le=1.0)


class ScanEvent(BaseModel):
    time: float
    band: int
    dwell_ms: int
    priority: float = Field(ge=0.0, le=1.0)
    result: Literal["hit", "miss"]


class DetectionEvent(BaseModel):
    time: float
    band: int
    confidence: float = Field(ge=0.0, le=1.0)


class DashboardResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metrics: Metrics
    current_scan: CurrentScan
    band_priorities: List[CurrentScan] = Field(default_factory=list)
    timeline: List[ScanEvent] = Field(default_factory=list)
    detections: List[DetectionEvent] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: Literal["healthy"]
    simulator: Literal["configured", "not_configured"]
    scheduler: Literal["configured", "not_configured"]
    analytics: Literal["configured", "not_configured"]


class LiveScanUpdate(BaseModel):
    type: Literal["scan_update"]
    time: float
    band: int
    dwell_ms: int
    priority: float = Field(ge=0.0, le=1.0)
    result: Literal["hit", "miss"]
