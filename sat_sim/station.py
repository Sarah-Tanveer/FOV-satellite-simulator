from __future__ import annotations

from dataclasses import dataclass

from skyfield.api import wgs84
from skyfield.toposlib import GeographicPosition

from sat_sim.config import GroundStationConfig


@dataclass(frozen=True)
class GroundStation:
    """
    Ground station used for satellite visibility and Doppler calculations.

    This wraps the Skyfield GeographicPosition object so the rest of the
    simulator can carry both human-readable metadata and the Skyfield object.
    """

    lat_deg: float
    lon_deg: float
    alt_m: float
    label: str | None
    skyfield_position: GeographicPosition

    @classmethod
    def from_config(cls, config: GroundStationConfig) -> "GroundStation":
        """
        Build a GroundStation from GroundStationConfig.
        """

        skyfield_position = wgs84.latlon(
            latitude_degrees=config.lat_deg,
            longitude_degrees=config.lon_deg,
            elevation_m=config.alt_m,
        )

        return cls(
            lat_deg=config.lat_deg,
            lon_deg=config.lon_deg,
            alt_m=config.alt_m,
            label=config.label,
            skyfield_position=skyfield_position,
        )

    @property
    def display_name(self) -> str:
        """
        Human-readable name for logs and output metadata.
        """
        info_str = f"lat={self.lat_deg:.6f}, lon={self.lon_deg:.6f}, alt={self.alt_m:.1f}m"
        if self.label:
            return f"{self.label}: {info_str}"
        else:
            return f"ground station: {info_str}"