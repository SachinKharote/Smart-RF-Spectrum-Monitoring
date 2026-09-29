from __future__ import annotations

from collections import defaultdict

from app.core.models import MetricsState, ScanObservation


class MetricsService:
    """Collects receiver metrics grouped by strategy."""

    def __init__(self) -> None:
        self.state = MetricsState()
        self._by_strategy: dict[str, MetricsState] = defaultdict(MetricsState)
        self._observations: list[ScanObservation] = []

    def reset(self) -> None:
        self.state = MetricsState()
        self._by_strategy = defaultdict(MetricsState)
        self._observations.clear()

    def record(self, observation: ScanObservation) -> None:
        self._record_into(self.state, observation)
        self._record_into(self._by_strategy[observation.strategy], observation)
        self._observations.append(observation)

    @staticmethod
    def _record_into(state: MetricsState, observation: ScanObservation) -> None:
        state.total_scans += 1
        if observation.actual_signal:
            state.actual_signals += 1
            if observation.received_signal:
                state.successful_detections += 1
                if observation.intercept_time_seconds is not None:
                    state.interception_times_seconds.append(observation.intercept_time_seconds)
            else:
                state.missed_signals += 1
        else:
            state.no_signal_observations += 1
            if observation.received_signal:
                state.false_alarms += 1

    def snapshot(self, strategy: str | None = None) -> dict:
        state = self._by_strategy.get(strategy) if strategy else self.state
        if state is None:
            return self._empty_snapshot(strategy)
        return {
            "strategy": strategy,
            "total_scans": state.total_scans,
            "actual_signals": state.actual_signals,
            "successful_detections": state.successful_detections,
            "missed_signals": state.missed_signals,
            "false_alarms": state.false_alarms,
            "no_signal_observations": state.no_signal_observations,
            "detection_rate": round(state.detection_rate, 2),
            "false_alarm_rate": round(state.false_alarm_rate, 2),
            "avg_intercept_time": (
                round(state.avg_intercept_time, 3)
                if state.avg_intercept_time is not None
                else None
            ),
        }

    @staticmethod
    def _empty_snapshot(strategy: str | None) -> dict:
        return {
            "strategy": strategy,
            "total_scans": 0,
            "actual_signals": 0,
            "successful_detections": 0,
            "missed_signals": 0,
            "false_alarms": 0,
            "no_signal_observations": 0,
            "detection_rate": 0.0,
            "false_alarm_rate": 0.0,
            "avg_intercept_time": None,
        }

    def strategies(self) -> list[str]:
        return sorted(self._by_strategy.keys())

    def timeline(self, limit: int = 50) -> list[dict]:
        return [
            {
                "scan_id": obs.scan_id,
                "band": obs.band_id,
                "strategy": obs.strategy,
                "time": obs.scan_time.isoformat(),
                "result": obs.result,
                "snr_db": obs.snr_db,
                "actual_signal": obs.actual_signal,
            }
            for obs in self._observations[-limit:]
        ] if limit > 0 else []

    def detections(self, limit: int = 50) -> list[dict]:
        hits = [obs for obs in self._observations if obs.result in {"hit", "false_alarm"}]
        return [
            {
                "scan_id": obs.scan_id,
                "band": obs.band_id,
                "strategy": obs.strategy,
                "result": obs.result,
                "emitter_id": obs.emitter_id,
                "transmission_id": obs.transmission_id,
                "snr_db": obs.snr_db,
                "intercept_time": obs.intercept_time_seconds,
            }
            for obs in hits[-limit:]
        ] if limit > 0 else []
