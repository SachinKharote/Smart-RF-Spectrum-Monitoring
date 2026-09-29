from __future__ import annotations

from datetime import datetime
from typing import Iterable, Protocol, Optional

from app.core.models import Band, Transmission


class RFEnvironment(Protocol):
    """Contract expected from the RF-simulator teammate.

    The receiver does not need to know how emitters or transmissions are generated.
    It only asks which transmission, if any, is active in the tuned band at a time.
    """

    def get_bands(self) -> list[Band]: ...

    def get_active_transmission(
        self, band_id: int, scan_time: datetime
    ) -> Optional[Transmission]: ...


class InMemoryRFEnvironment:
    def __init__(self, bands: Iterable[Band], transmissions: Iterable[Transmission]):
        self._bands = list(bands)
        self._transmissions = list(transmissions)

    def get_bands(self) -> list[Band]:
        return list(self._bands)

    def get_active_transmission(
        self, band_id: int, scan_time: datetime
    ) -> Optional[Transmission]:
        active = [
            tx
            for tx in self._transmissions
            if tx.band_id == band_id and tx.start_time <= scan_time <= tx.end_time
        ]
        if not active:
            return None
        return max(active, key=lambda tx: tx.signal_strength_dbm)
