# Member 3 Integration Contracts

## RF simulator -> receiver

The receiver depends on the `RFEnvironment` protocol in `app/integrations/rf_provider.py`.

```python
class RFEnvironment(Protocol):
    def get_bands(self) -> list[Band]: ...
    def get_active_transmission(
        self, band_id: int, scan_time: datetime
    ) -> Transmission | None: ...
```

The simulator owns how emitters, noise and transmissions are generated. The receiver only consumes the environment state it needs for a scan.

## ML prediction -> smart scheduler

The scheduler depends on the `PredictionProvider` protocol in `app/integrations/prediction_contract.py`.

```python
predict_next(
    *,
    bands,
    history,
    current_time_seconds,
) -> Prediction
```

Expected prediction payload:

```json
{
  "predicted_band_id": 8,
  "confidence": 0.91,
  "predicted_time_seconds": 12.4,
  "source": "ml"
}
```

The scheduler owns the final scan decision. The ML model does not directly control the receiver.

## Receiver / scheduler -> frontend

REST endpoints expose stable state and metrics. WebSocket `/ws` emits `scan_update` objects with receiver result, selected band, scheduler reason, prediction and confidence.

## Replacement rule

The local `InMemoryRFEnvironment` and `HistoryAwareMockPredictor` are development substitutes only. Replace them with the real team modules by implementing the two contracts. Do not rewrite the API layer or frontend contract.
