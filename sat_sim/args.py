from __future__ import annotations
import argparse
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from skyfield.api import load
from skyfield.timelib import Time, Timescale

import re

from sat_sim.config import (
    ExecutionConfig,
    GroundStationConfig,
    OutputConfig,
    RFConfig,
    SimulationConfig,
    TLEConfig,
    TimeConfig,
)

def sanitize_for_path(text: str) -> str:
    """
    Make a string safe to use as part of a folder name.
    """

    text = text.strip()
    text = re.sub(r"\s+", "_", text)
    text = re.sub(r"[^A-Za-z0-9_.-]", "_", text)
    text = re.sub(r"_+", "_", text)

    return text.strip("_")


def format_duration_for_path(duration_s: float) -> str:
    """
    Format duration for a readable folder name.
    """

    duration_s_int = int(round(duration_s))

    if duration_s_int % 3600 == 0:
        return f"{duration_s_int // 3600}h"

    if duration_s_int % 60 == 0:
        return f"{duration_s_int // 60}m"

    return f"{duration_s_int}s"


def build_run_output_dir(
    base_output_dir: str,
    start_dt,
    duration_s: float,
    station_label: str | None, debug_mode: bool = False
) -> str:
    """
    Build automatic output directory name:

        {start_time}_duration_{duration}_{station_label_if_given}
    """

    start_label = start_dt.strftime("%Y-%m-%d_%H-%M-%S")
    duration_label = format_duration_for_path(duration_s)

    parts = [
        start_label,
        f"duration_{duration_label}",
    ]

    if station_label is not None and station_label.strip() != "":
        parts.append(sanitize_for_path(station_label))

    run_dir_name = "_".join(parts)
    if debug_mode:
        run_dir_name += "_DEBUG"
    return str(Path(base_output_dir) / run_dir_name)

def parse_time(s: str, tz: str) -> datetime:
    """
    Parse user time input.

    Accepted:
      - "now"
      - "16-07-2025 16:00:00"
      - "2025-07-16 16:00:00"

    Returns
    -------
    Timezone-aware datetime in the user-provided timezone.
    """

    try:
        tzinfo = ZoneInfo(tz)
    except ZoneInfoNotFoundError:
        raise argparse.ArgumentTypeError(f"Invalid timezone: {tz}")

    if s.lower() == "now":
        return datetime.now(tzinfo)

    formats = [
        "%d-%m-%Y %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
    ]

    for fmt in formats:
        try:
            naive_dt = datetime.strptime(s, fmt)
            return naive_dt.replace(tzinfo=tzinfo)
        except ValueError:
            pass

    raise argparse.ArgumentTypeError(
        f"Invalid time format: {s}. Use 'DD-MM-YYYY HH:MM:SS', "
        f"'YYYY-MM-DD HH:MM:SS', or 'now'."
    )

def datetime_utc_to_skyfield(dt_utc: datetime, ts: Timescale) -> Time:
    """
    Convert a timezone-aware datetime to a Skyfield Time.

    The input is converted to UTC before creating the Skyfield Time.
    """

    if dt_utc.tzinfo is None:
        raise ValueError("dt_utc must be timezone-aware")

    dt_utc = dt_utc.astimezone(timezone.utc)

    return ts.utc(
        dt_utc.year,
        dt_utc.month,
        dt_utc.day,
        dt_utc.hour,
        dt_utc.minute,
        dt_utc.second + dt_utc.microsecond / 1e6,
    )

def parse_args() -> SimulationConfig:
    parser = argparse.ArgumentParser(
        description="Satellite Doppler simulator"
    )

    # ------------------------------------------------------------
    # Time configuration
    # ------------------------------------------------------------
    parser.add_argument(
        "--start-time",
        type=str,
        default="now",
        help=(
            "Start time of the experiment. Use 'now', "
            "'DD-MM-YYYY HH:MM:SS', or 'YYYY-MM-DD HH:MM:SS'. "
            "Default: now."
        ),
    )

    # ------------------------------------------------------------
    # Mutually exclusive group for duration vs end time
    # ------------------------------------------------------------
    time_group = parser.add_mutually_exclusive_group()

    time_group.add_argument(
        "--duration",
        type=float,
        default=None,
        help=(
            "Duration of the experiment in seconds. "
            "Mutually exclusive with --end-time; use duration to auto-calculate end time."
        ),
    )

    time_group.add_argument(
        "--end-time",
        type=str,
        default=None,
        help=(
            "End time of the experiment. Use 'DD-MM-YYYY HH:MM:SS' "
            "or 'YYYY-MM-DD HH:MM:SS'. Mutually exclusive with --duration; "
            "use end time to manually specify the experiment's end."
        ),
    )

    parser.add_argument(
        "--tz",
        type=str,
        default="UTC",
        help=(
            "Time zone used for interpreting start/end times. "
            "Default: UTC. Example: America/Chicago."
        ),
    )

    # ------------------------------------------------------------
    # Ground station information
    # ------------------------------------------------------------
    parser.add_argument(
        "--lat",
        type=float,
        default=43.07180200933477,
        help="Latitude of the ground station in degrees.",
    )

    parser.add_argument(
        "--lon",
        type=float,
        default=-89.41244173090192,
        help="Longitude of the ground station in degrees.",
    )

    parser.add_argument(
        "--alt",
        type=float,
        default=267.0,
        help="Altitude of the ground station in meters.",
    )

    parser.add_argument(
        "--station-label",
        type=str,
        default=None,
        help="Optional ground station label used in output filenames/metadata.",
    )

    # ------------------------------------------------------------
    # Doppler / RF configuration
    # ------------------------------------------------------------
    parser.add_argument(
        "--center-freq",
        type=float,
        default=11.575e9,
        help="RF center frequency used for Doppler calculation in Hz.",
    )

    # ------------------------------------------------------------
    # TLE configuration
    # ------------------------------------------------------------
    parser.add_argument(
        "--tle-file",
        type=str,
        default=None,
        help="Path to TLE file. If omitted, the simulator will download TLEs directly.",
    )

    # ------------------------------------------------------------
    # Execution configuration
    # ------------------------------------------------------------
    parser.add_argument(
        "--step-s",
        type=float,
        default=1.0,
        help="Time step in seconds for Doppler/orbit samples. Default: 1.0.",
    )

    parser.add_argument(
        "--min-elevation",
        type=float,
        default=0.0,
        help="Minimum allowed elevation in degrees. Default: 0.0.",
    )

    parser.add_argument(
        "--max-elevation",
        type=float,
        default=None,
        help=(
            "Optional maximum allowed elevation in degrees, useful for tracking dish "
            "mechanical limits. Example: 65."
        ),
    )

    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Enable parallel satellite/pass simulation.",
    )

    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help=(
            "Number of workers for parallel execution. "
            "Only used if --parallel is set. "
            "If --parallel is set and --workers is omitted, defaults to CPU count - 1."
        ),
    )
    
    # ------------------------------------------------------------
    # Logging configuration
    # ------------------------------------------------------------

    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level. Default: INFO.",
    )

    parser.add_argument(
        "--log-file",
        type=str,
        default=None,
        help="Optional path to a log file.",
    )

    # ------------------------------------------------------------
    # Output configuration
    # ------------------------------------------------------------
    parser.add_argument(
        "--output-dir",
        type=str,
        default="outputs",
        help="Directory where outputs will be written. Default: outputs.",
    )

    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing output files.",
    )
    # ------------------------------------------------------------
    # Debug mode for sampling orbits of specific satellites only (identified by name)
    # ------------------------------------------------------------
    parser.add_argument(
    "--debug-sat-names-file",
    type=str,
    default=None,
    help=(
        "Optional debug mode: path to a text file containing satellite names "
        "to consider, one satellite name per line. Only these satellites will "
        "be used from the TLE."
    ),)

    args = parser.parse_args()

    # ------------------------------------------------------------
    # Validate timezone
    # ------------------------------------------------------------
    try:
        ZoneInfo(args.tz)
    except ZoneInfoNotFoundError:
        parser.error(f"Invalid timezone: {args.tz}")

    # ------------------------------------------------------------
    # Validate execution settings
    # ------------------------------------------------------------
    if args.step_s <= 0:
        parser.error("--step-s must be positive")

    if args.min_elevation < -90 or args.min_elevation > 90:
        parser.error("--min-elevation must be between -90 and 90 degrees")

    if args.max_elevation is not None:
        if args.max_elevation < -90 or args.max_elevation > 90:
            parser.error("--max-elevation must be between -90 and 90 degrees")

        if args.max_elevation < args.min_elevation:
            parser.error("--max-elevation must be >= --min-elevation")
    # ------------------------------------------------------------
    # Validate / resolve parallel execution settings
    # ------------------------------------------------------------
    if args.parallel:
        if args.workers is None:
            workers = max(1, (os.cpu_count() or 2) - 1)
        else:
            workers = args.workers

        if workers <= 0:
            parser.error("--workers must be positive")

    else:
        workers = 1

        if args.workers is not None:
            parser.error("--workers can only be used when --parallel is set")
    

    # ------------------------------------------------------------
    # Build time config
    # ------------------------------------------------------------
    start_dt = parse_time(args.start_time, args.tz)

    if args.end_time is not None:
        end_dt = parse_time(args.end_time, args.tz)

        if end_dt <= start_dt:
            parser.error("--end-time must be after --start-time")

        duration_s = (end_dt - start_dt).total_seconds()

    else:
        duration_s = 30.0 if args.duration is None else args.duration

        if duration_s <= 0:
            parser.error("--duration must be positive")

        end_dt = start_dt + timedelta(seconds=duration_s)

    start_dt_utc = start_dt.astimezone(timezone.utc)
    end_dt_utc = end_dt.astimezone(timezone.utc)

    timescale = load.timescale()
    start_sf = datetime_utc_to_skyfield(start_dt_utc, timescale)
    end_sf = datetime_utc_to_skyfield(end_dt_utc, timescale)
    time_config=TimeConfig(
            start_dt=start_dt,
            end_dt=end_dt,
            start_dt_utc=start_dt_utc,
            end_dt_utc=end_dt_utc,
            start_sf=start_sf,
            end_sf=end_sf,
            timescale=timescale,
            duration_s=duration_s,
            timezone=args.tz,
        )
    ground_station=GroundStationConfig(
            lat_deg=args.lat,
            lon_deg=args.lon,
            alt_m=args.alt,
            label=args.station_label,
        )
    rf=RFConfig(
            center_freq_hz=args.center_freq,
        )
    tle=TLEConfig(
            tle_file=args.tle_file,
        )
    execution_config = ExecutionConfig(
    step_s=args.step_s,
    min_elevation_deg=args.min_elevation,
    max_elevation_deg=args.max_elevation,
    workers=workers,
    parallel=args.parallel,
    debug_sat_names_file=args.debug_sat_names_file,
    )
    
    run_output_dir = build_run_output_dir(
        base_output_dir=args.output_dir,
        start_dt=time_config.start_dt,
        duration_s=time_config.duration_s,
        station_label=args.station_label,
        debug_mode=execution_config.debug_sat_names_file is not None,
    )

    output_config = OutputConfig(
        output_dir=run_output_dir,
        overwrite=args.overwrite,
        log_level=args.log_level,
        log_file=args.log_file,
    )

    return SimulationConfig(
        time=time_config,
        ground_station=ground_station,
        rf=rf,
        tle=tle,
        execution=execution_config,
        output=output_config
    )