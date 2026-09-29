from fastapi import APIRouter, Query

from app.container import simulation_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("")
def dashboard(limit: int = Query(50, ge=1, le=500)):
    state = simulation_service.state_snapshot()
    metrics = state["metrics"]
    bands = simulation_service.environment.get_bands()
    return {
        "metrics": {
            "detection_rate": metrics["detection_rate"],
            "false_alarm_rate": metrics["false_alarm_rate"],
            "avg_intercept_time": metrics["avg_intercept_time"],
            "total_scans": metrics["total_scans"],
            "missed_signals": metrics["missed_signals"],
        },
        "receiver": state["current_scan"],
        "scheduler": state["scheduler"],
        "current_scan": state["current_scan"],
        "band_priorities": [
            {"band": b.band_id, "priority": b.priority}
            for b in bands
        ],
        "timeline": simulation_service.metrics.timeline(limit),
        "detections": simulation_service.metrics.detections(limit),
    }


@router.get("/metrics")
def dashboard_metrics(strategy: str | None = None):
    return simulation_service.metrics.snapshot(strategy)


@router.get("/strategies")
def dashboard_strategies():
    return {"strategies": ["Sequential", "Smart"]}


@router.get("/comparison")
def dashboard_comparison(scans: int = Query(200, ge=1, le=5000)):
    try:
        return simulation_service.comparison(scans)
    except ValueError as exc:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail=str(exc)) from exc
