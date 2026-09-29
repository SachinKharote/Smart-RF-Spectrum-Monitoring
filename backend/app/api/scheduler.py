from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.container import simulation_service

router = APIRouter(prefix="/scheduler", tags=["scheduler"])


class SchedulerConfigRequest(BaseModel):
    exploitation_weight: float = Field(0.55, ge=0.0, le=1.0)
    history_weight: float = Field(0.25, ge=0.0, le=1.0)
    prediction_weight: float = Field(0.20, ge=0.0, le=1.0)
    exploration_probability: float = Field(0.20, ge=0.0, le=1.0)
    recency_window_seconds: float = Field(5.0, gt=0.0)


@router.get("/state")
def scheduler_state():
    return simulation_service.scheduler_snapshot()


@router.post("/configure")
def configure_scheduler(config: SchedulerConfigRequest):
    if simulation_service.running:
        raise HTTPException(status_code=409, detail="Stop the simulation before reconfiguring the scheduler")
    try:
        from app.services.scheduler_service import SchedulerConfig
        new_config = SchedulerConfig(**config.model_dump())
        new_config.validate()
        simulation_service.smart_scheduler.config = new_config
        return {"status": "configured", "config": config.model_dump()}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
