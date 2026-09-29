from app.models.schemas import CurrentScan, Metrics, SimulationState


class MockAnalyticsEngine:
    """Development-only analytics substitute.

    It produces simple integration metrics from normalized events. Replace this
    class with the team's real analytics module without changing FastAPI routes.
    """

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.total_scans = 0
        self.hits = 0
        self.hit_times: list[float] = []

    def record_scan(self, scan: CurrentScan, state: SimulationState, result: str) -> None:
        self.total_scans += 1
        if result == "hit":
            self.hits += 1
            self.hit_times.append(state.time)

    def get_metrics(self) -> Metrics:
        if self.total_scans == 0:
            return Metrics()

        detection_rate = round((self.hits / self.total_scans) * 100, 2)
        # The current simulator contract does not identify false-positive events,
        # so the mock reports 0.0 until the real analytics module supplies it.
        false_alarm_rate = 0.0
        avg_intercept_time = round(sum(self.hit_times) / len(self.hit_times), 2) if self.hit_times else 0.0

        return Metrics(
            detection_rate=detection_rate,
            false_alarm_rate=false_alarm_rate,
            avg_intercept_time=avg_intercept_time,
        )
