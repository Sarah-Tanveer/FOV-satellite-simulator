from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from skyfield.api import EarthSatellite
from skyfield.timelib import Time


@dataclass(frozen=True)
class Satellite:
    """
    Satellite and its metadata.

    tle_age_*:
        Age of the TLE at the start time of the simulation:

            simulation_start_time - tle_epoch

        Positive means the TLE is older than the simulation start.
        Negative means the TLE epoch is after the simulation start.
    """

    name: str
    norad_id: int | None
    skyfield_sat: EarthSatellite

    tle_epoch_utc: datetime
    tle_age_days: float
    tle_age_hours: float

    generation: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_skyfield(
        cls,
        sat: EarthSatellite,
        simulation_start_time: Time,
        generation: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "Satellite":
        """
        Create a Satellite object from a Skyfield EarthSatellite.

        TLE age is calculated relative to the simulation start time.
        """

        norad_id = None
        try:
            norad_id = int(sat.model.satnum)
        except AttributeError:
            pass

        tle_epoch_utc = sat.epoch.utc_datetime().replace(tzinfo=timezone.utc)

        sim_start_utc = simulation_start_time.utc_datetime().replace(
            tzinfo=timezone.utc
        )

        tle_age_days = (
            sim_start_utc - tle_epoch_utc
        ).total_seconds() / 86400.0

        tle_age_hours = tle_age_days * 24.0

        return cls(
            name=sat.name,
            norad_id=norad_id,
            skyfield_sat=sat,
            tle_epoch_utc=tle_epoch_utc,
            tle_age_days=tle_age_days,
            tle_age_hours=tle_age_hours,
            generation=generation,
            metadata=metadata or {},
        )

    def tle_age_days_at(self, t: Time) -> float:
        """
        Calculate TLE age in days at any given Skyfield time.
        Useful if later you want per-sample age.
        """

        t_utc = t.utc_datetime().replace(tzinfo=timezone.utc)
        return (t_utc - self.tle_epoch_utc).total_seconds() / 86400.0

    def tle_age_hours_at(self, t: Time) -> float:
        """
        Calculate TLE age in hours at any given Skyfield time.
        Useful if later you want per-sample age.
        """

        return self.tle_age_days_at(t) * 24.0

@dataclass(frozen=True)
class SatellitePass:
    """
    Information about a satellite pass over the ground station at a specific time
    """

    satellite: Satellite

    # at least one of name or norad id should be present
    satellite_name: str
    satellite_norad_id: int | None

    pass_idx: int  # index of the pass for this satellite (simple enumeration per satellite)

    # rise_time might not be == start_time if the satellite is already above the horizon
    # at the start of the simulation,
    # and similarly set_time might not be == end_time if the satellite is still above the horizon
    # at the end of the simulation
    rise_time: Time | None
    set_time: Time | None
    peak_time: Time | None

    # Actual interval used for simulation.
    # These should never be None.
    start_time: Time
    end_time: Time
    duration_s: float

    # True if the real rise happened before the simulation window.
    starts_before_window: bool = False

    # True if the real set happens after the simulation window.
    ends_after_window: bool = False


@dataclass(frozen=True)
class OrbitSample:
    """
    Information about a satellite's position and velocity at a specific time sample.
    """

    satellite: Satellite

    satellite_name: str
    satellite_norad_id: int | None
    generation: str | None
    pass_idx: int

    timestamp: Time
    timestamp_utc: datetime

    time_from_start_of_pass_s: float  # time from the start of the satellite pass in seconds (not simulation)

    azimuth_deg: float
    elevation_deg: float
    # TODO: check
    range_km: float
    range_rate_km_s: float

    doppler_shift_hz: float

    tle_epoch_utc: datetime
    tle_age_days: float
    tle_age_hours: float

@dataclass(frozen=True)
class OneSatelliteOrbit:
    """
    A visible satellite pass together with its sampled orbit/Doppler data.
    """

    satellite_pass: SatellitePass
    orbit_samples: list[OrbitSample]