from __future__ import annotations

from datetime import datetime, timedelta

from app.core.models import Band, Transmission
from app.integrations.rf_provider import InMemoryRFEnvironment
from app.services.simulation_service import SimulationService


# Temporary local environment for end-to-end development.
# Member 2 can replace InMemoryRFEnvironment with the real RF simulator adapter.
bands = [
    Band(1, "Band 1", 100.0, 105.0, 5),
    Band(2, "Band 2", 105.0, 110.0, 4),
    Band(3, "Band 3", 110.0, 115.0, 3),
    Band(4, "Band 4", 115.0, 120.0, 5),
    Band(5, "Band 5", 120.0, 125.0, 2),
    Band(6, "Band 6", 125.0, 130.0, 4),
    Band(7, "Band 7", 130.0, 135.0, 3),
    Band(8, "Band 8", 135.0, 140.0, 5),
    Band(9, "Band 9", 140.0, 145.0, 2),
    Band(10, "Band 10", 145.0, 150.0, 4),
]

scenario_start = datetime.now().replace(microsecond=0)
transmissions = [
    Transmission(1, 1, 3, scenario_start + timedelta(seconds=1), scenario_start + timedelta(seconds=4), -45.0),
    Transmission(2, 4, 8, scenario_start + timedelta(seconds=2), scenario_start + timedelta(seconds=6), -38.0),
    Transmission(3, 2, 6, scenario_start + timedelta(seconds=5), scenario_start + timedelta(seconds=8), -52.0),
]

environment = InMemoryRFEnvironment(bands, transmissions)
simulation_service = SimulationService(environment)
