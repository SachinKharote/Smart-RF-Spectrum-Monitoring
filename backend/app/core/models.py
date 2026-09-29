from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Optional

ScanResult = Literal["hit", "miss", "false_alarm", "clear"]
StrategyName = Literal["Sequential", "Smart"]


@dataclass(frozen=True)
class Band:
    band_id: int
    name: str
    start_frequency_mhz: float
    end_frequency_mhz: float
    priority: int


@dataclass(frozen=True)
class Transmission:
    transmission_id: int
    emitter_id: int
    band_id: int
    start_time: datetime
    end_time: datetime
    signal_strength_dbm: float


@dataclass(frozen=True)
class ReceiverConfig:
    bandwidth_mhz: float = 5.0
    dwell_time_ms: int = 200
    detection_probability: float = 0.72
    false_alarm_probability: float = 0.08
    processing_delay_ms: float = 50.0


@dataclass(frozen=True)
class Prediction:
    predicted_band_id: Optional[int]
    confidence: float
    predicted_time_seconds: Optional[float] = None
    source: str = "mock"


@dataclass
class ScanDecision:
    band_id: int
    strategy: str
    priority: float
    reason: str
    sequence_number: int
    score: float = 0.0
    predicted_band_id: Optional[int] = None
    prediction_confidence: Optional[float] = None


@dataclass
class ScanObservation:
    scan_id: int
    band_id: int
    scan_time: datetime
    dwell_time_ms: int
    actual_signal: bool
    received_signal: bool
    snr_db: float
    result: ScanResult
    strategy: str = "Sequential"
    transmission_id: Optional[int] = None
    emitter_id: Optional[int] = None
    transmission_start_time: Optional[datetime] = None
    intercept_time_seconds: Optional[float] = None


@dataclass
class BandHistory:
    scans: int = 0
    hits: int = 0
    misses: int = 0
    false_alarms: int = 0
    clears: int = 0
    last_hit_time: Optional[datetime] = None
    last_result_time: Optional[datetime] = None

    @property
    def hit_rate(self) -> float:
        return self.hits / self.scans if self.scans else 0.0


@dataclass
class ReceiverState:
    running: bool = False
    tuned_band_id: Optional[int] = None
    bandwidth_mhz: float = 5.0
    dwell_time_ms: int = 200
    current_scan_id: int = 0
    current_time: Optional[datetime] = None
    last_result: Optional[ScanResult] = None
    last_observation: Optional[ScanObservation] = None
    last_decision: Optional[ScanDecision] = None
    last_prediction: Optional[Prediction] = None


@dataclass
class MetricsState:
    total_scans: int = 0
    actual_signals: int = 0
    successful_detections: int = 0
    missed_signals: int = 0
    false_alarms: int = 0
    no_signal_observations: int = 0
    interception_times_seconds: list[float] = field(default_factory=list)

    @property
    def detection_rate(self) -> float:
        return (
            100.0 * self.successful_detections / self.actual_signals
            if self.actual_signals
            else 0.0
        )

    @property
    def false_alarm_rate(self) -> float:
        return (
            100.0 * self.false_alarms / self.no_signal_observations
            if self.no_signal_observations
            else 0.0
        )

    @property
    def avg_intercept_time(self) -> Optional[float]:
        if not self.interception_times_seconds:
            return None
        return sum(self.interception_times_seconds) / len(self.interception_times_seconds)
