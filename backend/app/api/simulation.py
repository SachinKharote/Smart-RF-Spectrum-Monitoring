from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.container import simulation_service

router = APIRouter(prefix="/simulation", tags=["simulation"])


class StrategyRequest(BaseModel):
    strategy: str = Field(pattern="^(Sequential|Smart)$")


@router.post("/start")
async def start_simulation():
    return await simulation_service.start()


@router.post("/stop")
async def stop_simulation():
    return await simulation_service.stop()


@router.post("/reset")
def reset_simulation():
    try:
        simulation_service.reset()
        return {"status": "reset"}
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/strategy")
def configure_strategy(payload: StrategyRequest):
    try:
        simulation_service.configure_strategy(payload.strategy)
        return {"status": "configured", "strategy": payload.strategy}
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/state")
def simulation_state():
    return simulation_service.state_snapshot()


@router.get("/metrics")
def simulation_metrics(strategy: str | None = None):
    return simulation_service.metrics.snapshot(strategy)


@router.get("/scanner")
def scanner_state():
    return simulation_service.scheduler_snapshot()
