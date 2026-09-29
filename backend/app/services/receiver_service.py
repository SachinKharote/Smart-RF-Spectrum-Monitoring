from __future__ import annotations

import random
from datetime import datetime

from app.core.models import ReceiverConfig, ReceiverState, ScanObservation
from app.integrations.rf_provider import RFEnvironment
from app.services.metrics_service import MetricsService


class ReceiverService:
    """Virtual receiver owned by Member 3.

    It is deliberately independent of the RF simulator implementation.
    The simulator is accessed only through the RFEnvironment contract.
    """

    def __init__(self, environment: RFEnvironment, metrics: MetricsService, rng: random.Random | None = None):
        self.environment = environment
        self.metrics = metrics
        self._rng = rng or random.Random()
        self.config = ReceiverConfig()
        self.state = ReceiverState(
            bandwidth_mhz=self.config.bandwidth_mhz,
            dwell_time_ms=self.config.dwell_time_ms,
        )

    def configure(self, config: ReceiverConfig) -> None:
        if config.bandwidth_mhz <= 0:
            raise ValueError("bandwidth_mhz must be greater than 0")
        if config.dwell_time_ms <= 0:
            raise ValueError("dwell_time_ms must be greater than 0")
        if not 0.0 <= config.detection_probability <= 1.0:
            raise ValueError("detection_probability must be between 0 and 1")
        if not 0.0 <= config.false_alarm_probability <= 1.0:
            raise ValueError("false_alarm_probability must be between 0 and 1")
        if config.processing_delay_ms < 0:
            raise ValueError("processing_delay_ms cannot be negative")

        self.config = config
        self.state.bandwidth_mhz = config.bandwidth_mhz
        self.state.dwell_time_ms = config.dwell_time_ms

    def tune(self, band_id: int, scan_time: datetime) -> None:
        bands = {b.band_id for b in self.environment.get_bands()}
        if band_id not in bands:
            raise ValueError(f"Unknown band_id: {band_id}")
        self.state.tuned_band_id = band_id
        self.state.current_time = scan_time

    def scan(
        self,
        band_id: int,
        scan_time: datetime,
        strategy: str = "Sequential",
    ) -> ScanObservation:
        self.tune(band_id, scan_time)
        self.state.current_scan_id += 1

        tx = self.environment.get_active_transmission(band_id, scan_time)
        actual_signal = tx is not None

        if actual_signal:
            received_signal = self._rng.random() < self.config.detection_probability
            snr_db = round(self._rng.uniform(5.0, 25.0), 2)
        else:
            received_signal = self._rng.random() < self.config.false_alarm_probability
            snr_db = round(self._rng.uniform(-10.0, 5.0), 2)

        if actual_signal and received_signal:
            result = "hit"
        elif actual_signal and not received_signal:
            result = "miss"
        elif not actual_signal and received_signal:
            result = "false_alarm"
        else:
            result = "clear"

        intercept_time_seconds = None
        if actual_signal and received_signal and tx is not None:
            intercept_time_seconds = round(
                (scan_time - tx.start_time).total_seconds()
                + (self.config.processing_delay_ms / 1000.0),
                6,
            )

        observation = ScanObservation(
            scan_id=self.state.current_scan_id,
            band_id=band_id,
            scan_time=scan_time,
            dwell_time_ms=self.config.dwell_time_ms,
            actual_signal=actual_signal,
            received_signal=received_signal,
            snr_db=snr_db,
            result=result,
            strategy=strategy,
            transmission_id=tx.transmission_id if tx else None,
            emitter_id=tx.emitter_id if tx else None,
            transmission_start_time=tx.start_time if tx else None,
            intercept_time_seconds=intercept_time_seconds,
        )

        self.state.current_time = scan_time
        self.state.last_result = result
        self.state.last_observation = observation
        self.metrics.record(observation)
        return observation
