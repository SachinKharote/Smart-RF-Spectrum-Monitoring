from fastapi import APIRouter, HTTPException

from app.core.models import ReceiverConfig
from app.container import simulation_service

router = APIRouter(prefix="/receiver", tags=["receiver"])


@router.get("/state")
def receiver_state():
    return simulation_service.state_snapshot()["current_scan"]


@router.post("/configure")
def configure_receiver(config: ReceiverConfig):
    try:
        simulation_service.configure_receiver(config)
        return {
            "status": "configured",
            "config": {
                "bandwidth_mhz": config.bandwidth_mhz,
                "dwell_time_ms": config.dwell_time_ms,
                "detection_probability": config.detection_probability,
                "false_alarm_probability": config.false_alarm_probability,
                "processing_delay_ms": config.processing_delay_ms,
            },
        }
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
