# Smart EW Scan - Member 3 Backend

This is the **Backend Engineer 2 - Receiver & Smart Scheduler** implementation.

Your team division assigns Member 3 ownership of the virtual receiver, detection / hit / miss / false-alarm logic, sequential baseline, smart scheduler, feedback loop, performance metrics, backend APIs and live data. The ML model itself and frontend visualizations remain separate team responsibilities.

## Implemented scope

### Phase 1
- Virtual receiver tuning and configurable bandwidth
- Dwell time
- Detection, miss, false alarm and clear classification
- RF environment adapter contract

### Phase 2
- Traditional sequential round-robin scheduler
- Detection rate
- False-alarm rate
- Missed signals
- Average interception time
- Timeline and detection event records

### Phase 3
- Prediction interface (`PredictionProvider`)
- Confidence-aware prediction object
- Mock history-aware predictor for local development only

### Phase 4
- Smart scheduler combining baseline priority, recent history and ML prediction confidence
- Exploitation vs exploration
- Scheduler decision explanation

### Phase 5
- Hit / miss / false-alarm feedback loop
- Per-band scheduler history
- Recent-hit recency signal
- State reset between simulation runs

### Phase 6
- Sequential vs Smart metrics available through a common API shape
- `/dashboard/comparison`
- Strategy-aware metrics

### Phase 7
- Input validation and lifecycle errors
- REST smoke tests and scheduler/feedback unit tests
- CORS enabled for the separate frontend application
- WebSocket live scan events

## Run

From this `backend` directory:

```bash
python -m pip install -r requirements.txt
python -m pytest -q
uvicorn app.main:app --reload
```

Open:

`http://127.0.0.1:8000/docs`

## Main API

```text
POST /simulation/start
POST /simulation/stop
POST /simulation/reset
POST /simulation/strategy
GET  /simulation/state
GET  /simulation/metrics
GET  /simulation/scanner

GET  /receiver/state
POST /receiver/configure

GET  /dashboard
GET  /dashboard/metrics
GET  /dashboard/strategies
GET  /dashboard/comparison

WS   /ws
```

### Strategy selection

```json
POST /simulation/strategy
{
  "strategy": "Smart"
}
```

Allowed values are `Sequential` and `Smart`.

## Integration contracts

### RF simulator

The simulator teammate replaces `InMemoryRFEnvironment` with an implementation of `RFEnvironment`.

### ML prediction

The ML teammate replaces `HistoryAwareMockPredictor` with an implementation of `PredictionProvider`.

The interface is intentionally small:

```python
predict_next(
    *,
    bands,
    history,
    current_time_seconds,
) -> Prediction
```

The backend expects a predicted band and confidence. It does not train or own the ML model.

### Frontend

Frontend teammates consume REST and WebSocket outputs. No frontend implementation is included in this package.

## End-to-end loop

```text
RF environment
    -> Receiver scan
    -> Observation / hit / miss
    -> ML prediction
    -> Smart scheduler
    -> Next band
    -> Receiver
    -> Feedback history
    -> Metrics
    -> FastAPI / WebSocket
```
