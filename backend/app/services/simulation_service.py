from __future__ import annotations

import asyncio
import random
import uuid
from datetime import datetime, timedelta
from typing import Optional

from app.core.models import Prediction, ReceiverConfig, ScanObservation
from app.integrations.rf_provider import RFEnvironment
from app.integrations.mock_predictor import HistoryAwareMockPredictor
from app.services.metrics_service import MetricsService
from app.services.receiver_service import ReceiverService
from app.services.scheduler_service import SchedulerConfig, ScanDecision, SequentialScheduler, SmartScheduler
from app.state.store import event_hub


class SimulationService:
    """Owns receiver control, scanner orchestration, smart feedback and API state."""

    def __init__(self, environment: RFEnvironment, predictor=None):
        self.environment = environment
        self.metrics = MetricsService()
        self.receiver = ReceiverService(environment, self.metrics)
        bands = environment.get_bands()
        self.sequential_scheduler = SequentialScheduler(bands)
        self.smart_scheduler = SmartScheduler(
            bands,
            predictor or HistoryAwareMockPredictor(),
            config=SchedulerConfig(),
        )
        self.strategy: str = "Smart"
        self.simulation_id: Optional[str] = None
        self.running = False
        self._task: Optional[asyncio.Task] = None
        self._start_time: Optional[datetime] = None
        self._sim_time: Optional[datetime] = None

    def configure_strategy(self, strategy: str) -> None:
        if self.running:
            raise RuntimeError("Stop the simulation before changing strategy")
        if strategy not in {"Sequential", "Smart"}:
            raise ValueError("strategy must be Sequential or Smart")
        self.strategy = strategy

    def configure_receiver(self, config: ReceiverConfig) -> None:
        if self.running:
            raise RuntimeError("Stop the simulation before reconfiguring the receiver")
        self.receiver.configure(config)

    def reset(self) -> None:
        if self.running:
            raise RuntimeError("Stop the simulation before resetting the simulation")
        self.simulation_id = None
        self.metrics.reset()
        self.sequential_scheduler.reset()
        self.smart_scheduler.reset()
        self.receiver.state = self.receiver.state.__class__(
            bandwidth_mhz=self.receiver.config.bandwidth_mhz,
            dwell_time_ms=self.receiver.config.dwell_time_ms,
        )
        self._sim_time = None

    async def start(self) -> dict:
        if self.running:
            return {"simulation_id": self.simulation_id, "status": "running"}

        self.metrics.reset()
        self.sequential_scheduler.reset()
        self.smart_scheduler.reset()
        self.simulation_id = f"SIM-{uuid.uuid4().hex[:8].upper()}"
        self.running = True
        self.receiver.state.running = True
        self._start_time = datetime.now().replace(microsecond=0)
        self._sim_time = self._start_time
        self._task = asyncio.create_task(self._run_loop())
        return {"simulation_id": self.simulation_id, "status": "running", "strategy": self.strategy}

    async def stop(self) -> dict:
        self.running = False
        self.receiver.state.running = False
        if self._task:
            await self._task
            self._task = None
        return {"simulation_id": self.simulation_id, "status": "stopped", "strategy": self.strategy}

    async def _run_loop(self) -> None:
        scan_time = self._sim_time or datetime.now().replace(microsecond=0)
        while self.running:
            relative_seconds = (scan_time - (self._start_time or scan_time)).total_seconds()
            if self.strategy == "Sequential":
                decision = self.sequential_scheduler.next_scan()
                prediction = Prediction(None, 0.0, predicted_time_seconds=relative_seconds, source="not-used")
            else:
                decision, prediction = self.smart_scheduler.next_scan(
                    current_time=scan_time,
                    current_time_seconds=relative_seconds,
                )

            observation = self.receiver.scan(
                decision.band_id,
                scan_time,
                strategy=decision.strategy,
            )

            if self.strategy == "Smart":
                self.smart_scheduler.apply_feedback(observation)

            self.receiver.state.last_decision = decision
            self.receiver.state.last_prediction = prediction
            await event_hub.publish(self._event_for(observation, decision, prediction))

            scan_time += timedelta(milliseconds=self.receiver.config.dwell_time_ms)
            self._sim_time = scan_time
            await asyncio.sleep(self.receiver.config.dwell_time_ms / 1000.0)

    def _event_for(
        self,
        observation: ScanObservation,
        decision: ScanDecision,
        prediction: Prediction,
    ) -> dict:
        return {
            "type": "scan_update",
            "simulation_id": self.simulation_id,
            "scan_id": observation.scan_id,
            "sequence_number": decision.sequence_number,
            "time": round(
                (observation.scan_time - (self._start_time or observation.scan_time)).total_seconds(),
                3,
            ),
            "band": observation.band_id,
            "dwell_ms": observation.dwell_time_ms,
            "bandwidth_mhz": self.receiver.config.bandwidth_mhz,
            "strategy": decision.strategy,
            "priority": decision.priority,
            "decision_score": decision.score,
            "reason": decision.reason,
            "predicted_band": prediction.predicted_band_id,
            "prediction_confidence": prediction.confidence,
            "prediction_source": prediction.source,
            "result": observation.result,
            "actual_signal": observation.actual_signal,
            "received_signal": observation.received_signal,
            "snr_db": observation.snr_db,
            "intercept_time": observation.intercept_time_seconds,
        }

    def state_snapshot(self) -> dict:
        obs = self.receiver.state.last_observation
        decision = self.receiver.state.last_decision
        prediction = self.receiver.state.last_prediction
        return {
            "simulation_id": self.simulation_id,
            "running": self.running,
            "strategy": self.strategy,
            "current_scan": {
                "scan_id": self.receiver.state.current_scan_id,
                "band": self.receiver.state.tuned_band_id,
                "bandwidth_mhz": self.receiver.state.bandwidth_mhz,
                "dwell_ms": self.receiver.state.dwell_time_ms,
                "strategy": obs.strategy if obs else None,
                "result": self.receiver.state.last_result,
                "snr_db": obs.snr_db if obs else None,
                "intercept_time": obs.intercept_time_seconds if obs else None,
            },
            "scheduler": {
                "strategy": self.strategy,
                "selected_band": decision.band_id if decision else None,
                "priority": decision.priority if decision else None,
                "score": decision.score if decision else None,
                "reason": decision.reason if decision else None,
                "predicted_band": prediction.predicted_band_id if prediction else None,
                "prediction_confidence": prediction.confidence if prediction else None,
            },
            "metrics": self.metrics.snapshot(),
        }

    def comparison(self, scans: int = 200) -> dict:
        if scans < 1 or scans > 5000:
            raise ValueError("scans must be between 1 and 5000")

        bands = self.environment.get_bands()
        start_time = datetime.now().replace(microsecond=0)

        def run_strategy(strategy: str, seed: int) -> tuple[dict, list[dict]]:
            metrics = MetricsService()
            receiver = ReceiverService(self.environment, metrics, rng=random.Random(seed))
            receiver.configure(self.receiver.config)

            if strategy == "Sequential":
                scheduler = SequentialScheduler(bands)
                history = None
            else:
                scheduler = SmartScheduler(
                    bands,
                    self.smart_scheduler.predictor,
                    config=self.smart_scheduler.config,
                    rng=random.Random(seed),
                )
                history = scheduler.history

            scan_time = start_time
            events: list[dict] = []
            for _ in range(scans):
                relative = (scan_time - start_time).total_seconds()
                if strategy == "Sequential":
                    decision = scheduler.next_scan()
                    prediction = Prediction(None, 0.0, relative, "not-used")
                else:
                    decision, prediction = scheduler.next_scan(
                        current_time=scan_time,
                        current_time_seconds=relative,
                    )

                observation = receiver.scan(
                    decision.band_id, scan_time, strategy=strategy
                )
                if strategy == "Smart":
                    scheduler.apply_feedback(observation)

                events.append({
                    "scan_id": observation.scan_id,
                    "band": observation.band_id,
                    "result": observation.result,
                    "strategy": strategy,
                    "predicted_band": prediction.predicted_band_id,
                    "prediction_confidence": prediction.confidence,
                })
                scan_time += timedelta(milliseconds=self.receiver.config.dwell_time_ms)

            return metrics.snapshot(strategy), events

        sequential_metrics, sequential_events = run_strategy("Sequential", 1001)
        smart_metrics, smart_events = run_strategy("Smart", 1001)

        return {
            "scans_per_strategy": scans,
            "same_scenario": True,
            "Sequential": sequential_metrics,
            "Smart": smart_metrics,
            "events": {
                "Sequential": sequential_events[-50:],
                "Smart": smart_events[-50:],
            },
        }

    def scheduler_snapshot(self) -> dict:
        history = self.smart_scheduler.history_snapshot()
        return {
            "active_strategy": self.strategy,
            "sequential": {
                "next_sequence_number": self.sequential_scheduler.index + 1,
                "band_count": self.sequential_scheduler.band_count,
            },
            "smart": {
                "exploration_probability": self.smart_scheduler.config.exploration_probability,
                "last_decision": (
                    {
                        "band": self.smart_scheduler.last_decision.band_id,
                        "score": self.smart_scheduler.last_decision.score,
                        "reason": self.smart_scheduler.last_decision.reason,
                    }
                    if self.smart_scheduler.last_decision
                    else None
                ),
                "history": history,
            },
        }
