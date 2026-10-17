"""All fixtures in tests are synthetic/test only. Never copied to application data."""
import pytest
from src.schema import CapacityObservation, ConnectionPoint


@pytest.fixture
def point():
    return ConnectionPoint("TEST-ONLY", "Synthetic operator", "SYNTHETIC / TEST ONLY", 110,
                           "https://example.org/test-only")


@pytest.fixture
def observation(point):
    return CapacityObservation("TEST-OBS", point.connection_point_id, "consumption", 2030,
        10, "MVA", "published_indicative", "https://example.org/test-only", "2026-10-16T00:00:00Z",
        "SYNTHETIC / TEST ONLY. No real connection evidence.")
