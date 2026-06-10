from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from skyfield.timelib import Time, Timescale


@dataclass(frozen=True) # read only, immutable once initialised
class TimeConfig:
    """
    Experiment time configuration.

    start_dt/end_dt:
        Timezone-aware datetimes in the user-provided timezone.

    start_dt_utc/end_dt_utc:
        Same times converted to UTC. Use these for logging, CSVs,
        and sanity checks.

    start_sf/end_sf:
        Skyfield Time objects. Use these directly for find_events(),
        altaz(), Doppler calculation, etc.

    timescale:
        Skyfield Timescale object used to construct start_sf/end_sf.
    """
    # the two can be same if tz == UTC, but we want to keep both for clarity and to avoid timezone-related bugs
    start_dt: datetime
    end_dt: datetime
    start_dt_utc: datetime
    end_dt_utc: datetime

    # convert only once to avoid repeated conversions and potential timezone bugs
    start_sf: Time
    end_sf: Time
    timescale: Timescale

    # can either be specified or calculated from start_dt and duration_s
    duration_s: float

    # V IMPORTANT: this is the timezone string provided by the user, not necessarily "UTC"
    timezone: str

@dataclass(frozen=True)
class GroundStationConfig:
    """
    Ground station location.
    """

    lat_deg: float
    lon_deg: float
    alt_m: float
    # not necessary for the core simulation, but useful for labeling outputs and sanity checks
    label: str | None = None


@dataclass(frozen=True)
class RFConfig:
    """
    RF configuration for Doppler calculation.
    """
    # only used for Doppler calculation
    center_freq_hz: float


@dataclass(frozen=True)
class TLEConfig:
    """
    TLE source configuration.
    """
    # if none then we download TLEs and save the tle in a file otherwise use the one provided by the user
    tle_file: str | None


@dataclass(frozen=True)
class ExecutionConfig:
    """
    Execution settings.

    workers/parallel are included now so the code is parallel-ready later,
    even if we initially run everything serially.
    """

    step_s: float # time step for iterating though orbital positions and calculating Doppler shifts
    min_elevation_deg: float 
    # Optional maximum elevation due to hardware/tracking limits. If not set then max elevation == 180 - min_elevation (i.e. no max elevation constraint).
    # Example: a dish that can only track up to 65 degrees elevation.
    max_elevation_deg: float | None

    # num of workers can either be set or be calculated as num_cpus - 1
    workers: int
    # by default should be false but parallel is supported
    parallel: bool

    debug_sat_names_file: str | None = None


@dataclass(frozen=True)
class OutputConfig:
    """
    Output paths and file-writing behavior.
    """

    output_dir: str
    overwrite: bool
    log_level: str
    log_file: str | None


@dataclass(frozen=True)
class SimulationConfig:
    """
    Top-level simulator configuration.
    """

    time: TimeConfig
    ground_station: GroundStationConfig
    rf: RFConfig
    tle: TLEConfig
    execution: ExecutionConfig
    output: OutputConfig

