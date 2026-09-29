from datetime import datetime, timedelta

from app.core.models import Band, BandHistory, Transmission
from app.integrations.mock_predictor import HistoryAwareMockPredictor
from app.integrations.rf_provider import InMemoryRFEnvironment
from app.services.metrics_service import MetricsService
from app.services.receiver_service import ReceiverService
from app.services.scheduler_service import SmartScheduler, SchedulerConfig


def build_bands():
    return [
        Band(1, "Band 1", 100, 105, 5),
        Band(2, "Band 2", 105, 110, 3),
        Band(3, "Band 3", 110, 115, 1),
    ]


def test_mock_predictor_returns_valid_prediction():
    bands = build_bands()
    predictor = HistoryAwareMockPredictor()
    prediction = predictor.predict_next(
        bands=bands,
        history={1: BandHistory(), 2: BandHistory(), 3: BandHistory()},
        current_time_seconds=0.0,
    )
    assert prediction.predicted_band_id == 1
    assert 0.0 <= prediction.confidence <= 1.0


def test_smart_scheduler_uses_prediction_and_feedback():
    bands = build_bands()
    scheduler = SmartScheduler(
        bands,
        HistoryAwareMockPredictor(),
        SchedulerConfig(exploration_probability=0.0),
    )
    now = datetime(2026, 1, 1, 10, 0, 0)
    decision, prediction = scheduler.next_scan(current_time=now, current_time_seconds=0.0)
    assert decision.strategy == "Smart"
    assert decision.band_id == prediction.predicted_band_id

    env = InMemoryRFEnvironment(bands, [
        Transmission(1, 1, 1, now, now + timedelta(seconds=2), -40)
    ])
    receiver = ReceiverService(env, MetricsService())
    receiver.configure(receiver.config.__class__(
        detection_probability=1.0,
        false_alarm_probability=0.0,
        bandwidth_mhz=5.0,
        dwell_time_ms=200,
    ))
    obs = receiver.scan(1, now, strategy="Smart")
    scheduler.apply_feedback(obs)
    assert scheduler.history[1].hits == 1
    assert scheduler.history[1].scans == 1
    assert scheduler.history[1].last_hit_time == now


def test_scheduler_exploration_is_deterministic_with_seed():
    bands = build_bands()
    scheduler = SmartScheduler(
        bands,
        HistoryAwareMockPredictor(),
        SchedulerConfig(exploration_probability=1.0),
    )
    now = datetime(2026, 1, 1, 10, 0, 0)
    decisions = [
        scheduler.next_scan(current_time=now, current_time_seconds=float(i))[0].band_id
        for i in range(5)
    ]
    assert decisions == [1, 1, 3, 3, 1]
