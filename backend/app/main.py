from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import dashboard, receiver, simulation, scheduler, websocket

app = FastAPI(title="Smart EW Scan - Member 3 Backend", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(simulation.router)
app.include_router(receiver.router)
app.include_router(dashboard.router)
app.include_router(scheduler.router)
app.include_router(websocket.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "member3-backend"}
