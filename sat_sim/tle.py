from __future__ import annotations

import logging
from pathlib import Path

from skyfield.api import load

from sat_sim.config import ExecutionConfig, TLEConfig, TimeConfig
from sat_sim.models import Satellite


DEFAULT_TLE_URL = "https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=tle"

from pathlib import Path

from sat_sim.models import Satellite

def normalize_satellite_name(name: str) -> str:
    """
    Normalize satellite names for matching.

    This lets:
        STARLINK-1011
        Starlink 1011
        starlink_1011

    match more reliably.
    """

    return (
        name.strip()
        .upper()
        .replace("_", "-")
        .replace(" ", "-")
    )

def read_debug_satellite_names(
    debug_sat_names_file: str,
    logger,
) -> list[str]:
    """
    Read requested satellite names from a debug text file.

    Blank lines and lines starting with # are ignored.
    """

    path = Path(debug_sat_names_file)

    if not path.exists():
        raise FileNotFoundError(f"Debug satellite names file does not exist: {path}")

    names: list[str] = []

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            name = line.strip()

            if name == "":
                continue

            if name.startswith("#"):
                continue

            names.append(name)

    logger.info(f"Loaded {len(names)} requested debug satellite names from {path}")

    return names

def filter_satellites_by_debug_names(
    satellites: list[Satellite],
    requested_names: list[str],
    logger,
) -> list[Satellite]:
    """
    Keep only satellites requested by name.

    Logs an error if a requested satellite name is not found in the TLE,
    but continues with the satellites that were found.
    """

    satellites_by_name = {
        normalize_satellite_name(sat.name): sat
        for sat in satellites
    }

    filtered_satellites: list[Satellite] = []

    for requested_name in requested_names:
        key = normalize_satellite_name(requested_name)

        if key not in satellites_by_name:
            logger.error(
                f"Debug satellite requested but not found in TLE: {requested_name}"
            )
            continue

        filtered_satellites.append(satellites_by_name[key])

    logger.info(
        f"Debug satellite filter kept {len(filtered_satellites)} / "
        f"{len(requested_names)} requested satellites"
    )

    return filtered_satellites

def load_satellites(
    tle_config: TLEConfig,
    time_config: TimeConfig,
    execution_config: ExecutionConfig,
    logger: logging.Logger | None = None,
) -> list[Satellite]:
    """
    Load satellites from a TLE file or from the default online TLE source.

    Parameters
    ----------
    tle_config:
        TLE configuration from SimulationConfig.

    time_config:
        Time configuration. We use time_config.start_sf to calculate
        each satellite's TLE age at the start of the simulation.

    logger:
        Optional logger.

    Returns
    -------
    list[Satellite]
        Satellites wrapped in our Satellite model.
    """

    if logger is None:
        logger = logging.getLogger("sat_sim")

    if tle_config.tle_file is not None:
        tle_path = Path(tle_config.tle_file)

        if not tle_path.exists():
            raise FileNotFoundError(f"TLE file does not exist: {tle_path}")

        logger.debug("Loading TLEs from file: %s", tle_path)
        skyfield_sats = load.tle_file(str(tle_path))

    else:
        logger.info("No TLE file provided. Loading default Starlink TLEs from CelesTrak.")
        logger.debug("TLE URL: %s", DEFAULT_TLE_URL)
        skyfield_sats = load.tle_file(DEFAULT_TLE_URL)

    satellites: list[Satellite] = []

    for skyfield_sat in skyfield_sats:
        generation = infer_generation_from_name(skyfield_sat.name)

        sat = Satellite.from_skyfield(
            sat=skyfield_sat,
            simulation_start_time=time_config.start_sf,
            generation=generation,
            metadata={},
        )

        satellites.append(sat)

    if satellites:
        ages_days = [sat.tle_age_days for sat in satellites]
        logger.debug(
            "TLE age at simulation start: min=%.3f days, max=%.3f days",
            min(ages_days),
            max(ages_days),
        )
    if execution_config.debug_sat_names_file is not None:
        logger.info(
            f"Debug satellite subset mode enabled: "
            f"{execution_config.debug_sat_names_file}"
        )

        requested_names = read_debug_satellite_names(
            debug_sat_names_file=execution_config.debug_sat_names_file,
            logger=logger,
        )

        satellites = filter_satellites_by_debug_names(
            satellites=satellites,
            requested_names=requested_names,
            logger=logger,
        )
        logger.info(f"Number of satellites requested for debug mode: {len(requested_names)}")
    logger.info("Loaded %d satellites", len(satellites))

    return satellites


def infer_generation_from_name(name: str) -> str | None:
    """
    Infer satellite generation from name.

    For now, this is intentionally conservative.

    A proper Starlink generation label should eventually come from a
    metadata CSV keyed by NORAD ID, because name-based inference is not
    reliable enough for publication-quality labels.

    Returns
    -------
    str | None
        Currently returns "unknown" for Starlink satellites and None otherwise.
    """
    # TODO: Implement proper generation inference logic
    name_upper = name.upper()

    if "STARLINK" in name_upper:
        return "unknown"

    return None