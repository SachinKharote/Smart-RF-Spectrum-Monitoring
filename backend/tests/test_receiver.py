from datetime import datetime, timedelta

from app.core.models import Band, Transmission
from app.integrations.rf_provider import InMemoryRFEnvironment
from app.services.metrics_service import MetricsService
from app.services.receiver_service import ReceiverService


def test_receiver_detects_known_signal_when_probability_is_one():
    now = datetime(2026, 1, 1, 10, 0, 0)
    bands = [Band(1, "Band 1", 100, 105, 5)]
    transmissions = [
        Transmission(1, 1, 1, now, now + timedelta(seconds=2), -40),
    ]
    receiver = ReceiverService(
        InMemoryRFEnvironment(bands, transmissions), MetricsService()
    )
    receiver.configure(receiver.config.__class__(
        detection_probability=1.0,
        false_alarm_probability=0.0,
        bandwidth_mhz=5.0,
        dwell_time_ms=200,
    ))

    obs = receiver.scan(1, now)

    assert obs.actual_signal is True
    assert obs.received_signal is True
    assert obs.result == "hit"


def test_receiver_returns_clear_when_no_signal_and_zero_false_alarm_probability():
    now = datetime(2026, 1, 1, 10, 0, 0)
    bands = [Band(1, "Band 1", 100, 105, 5)]
    receiver = ReceiverService(InMemoryRFEnvironment(bands, []), MetricsService())
    receiver.configure(receiver.config.__class__(
        detection_probability=1.0,
        false_alarm_probability=0.0,
        bandwidth_mhz=5.0,
        dwell_time_ms=200,
    ))

    obs = receiver.scan(1, now)

    assert obs.actual_signal is False
    assert obs.received_signal is False
    assert obs.result == "clear"
