from datetime import datetime, timedelta

from app.core.models import Band, Transmission
from app.integrations.rf_provider import InMemoryRFEnvironment
from app.services.metrics_service import MetricsService
from app.services.receiver_service import ReceiverService
from app.services.scheduler_service import SequentialScheduler


def test_sequential_scheduler_cycles_deterministically():
    bands = [
        Band(1, "Band 1", 100, 105, 5),
        Band(2, "Band 2", 105, 110, 4),
        Band(3, "Band 3", 110, 115, 3),
    ]
    scheduler = SequentialScheduler(bands)

    decisions = [scheduler.next_scan() for _ in range(5)]

    assert [d.band_id for d in decisions] == [1, 2, 3, 1, 2]
    assert [d.sequence_number for d in decisions] == [1, 2, 3, 4, 5]
    assert all(d.strategy == "Sequential" for d in decisions)


def test_phase2_metrics_track_detection_false_alarm_and_intercept_time():
    now = datetime(2026, 1, 1, 10, 0, 0)
    bands = [Band(1, "Band 1", 100, 105, 5)]
    transmissions = [
        Transmission(1, 1, 1, now, now + timedelta(seconds=2), -45),
    ]
    environment = InMemoryRFEnvironment(bands, transmissions)
    metrics = MetricsService()
    receiver = ReceiverService(environment, metrics)
    receiver.configure(
        receiver.config.__class__(
            detection_probability=1.0,
            false_alarm_probability=0.0,
            processing_delay_ms=50.0,
            bandwidth_mhz=5.0,
            dwell_time_ms=200,
        )
    )

    hit = receiver.scan(1, now, strategy="Sequential")

    assert hit.result == "hit"
    assert hit.intercept_time_seconds == 0.05
    assert metrics.snapshot("Sequential")["successful_detections"] == 1
    assert metrics.snapshot("Sequential")["detection_rate"] == 100.0
    assert metrics.snapshot("Sequential")["avg_intercept_time"] == 0.05

    later = now + timedelta(seconds=5)
    clear = receiver.scan(1, later, strategy="Sequential")
    assert clear.result == "clear"
    assert metrics.snapshot("Sequential")["false_alarm_rate"] == 0.0


def test_metrics_exposes_timeline_and_detections():
    now = datetime(2026, 1, 1, 10, 0, 0)
    bands = [Band(1, "Band 1", 100, 105, 5)]
    transmissions = [
        Transmission(1, 1, 1, now, now + timedelta(seconds=2), -45),
    ]
    metrics = MetricsService()
    receiver = ReceiverService(InMemoryRFEnvironment(bands, transmissions), metrics)
    receiver.configure(
        receiver.config.__class__(
            detection_probability=1.0,
            false_alarm_probability=0.0,
            bandwidth_mhz=5.0,
            dwell_time_ms=200,
        )
    )

    receiver.scan(1, now, strategy="Sequential")

    timeline = metrics.timeline()
    detections = metrics.detections()

    assert len(timeline) == 1
    assert timeline[0]["result"] == "hit"
    assert len(detections) == 1
    assert detections[0]["result"] == "hit"
