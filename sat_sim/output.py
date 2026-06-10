from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from sat_sim.config import OutputConfig
from sat_sim.models import OrbitSample, SatellitePass, OneSatelliteOrbit
from sat_sim.constants import HEADERS


logger = logging.getLogger("sat_sim")


def prepare_output_dir(output_config: OutputConfig) -> Path:
    """
    Create and return the output directory.
    """

    output_dir = Path(output_config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.debug(f"Output directory ready: {output_dir}")

    return output_dir

def all_orbits_to_dataframe(orbits: list[OneSatelliteOrbit]) -> pd.DataFrame:
    """
    Convert all sampled satellite passes into one flat DataFrame.
    One row per OrbitSample.
    """

    data = []
    headers = HEADERS

    for orbit in orbits:
        for sample in orbit.orbit_samples:
            info = [
                sample.satellite_name,
                sample.satellite_norad_id,
                sample.pass_idx,
                sample.generation,
                sample.timestamp_utc.isoformat(),
                sample.doppler_shift_hz,
                sample.elevation_deg,
                sample.azimuth_deg,
                sample.range_km,
                sample.tle_age_hours,
            ]

            if len(info) != len(headers):
                raise ValueError(
                    f"HEADERS has {len(headers)} columns but row has {len(info)} values. "
                    f"HEADERS={headers}"
                )

            row = dict(zip(headers, info))
            data.append(row)

    df = pd.DataFrame(data, columns=headers)

    return df

def save_all_orbits_to_csv(
    orbits: list[OneSatelliteOrbit],
    output_config: OutputConfig,
    filename: str = "orbit_samples.csv",
) -> Path:
    """
    Save all orbit samples from all satellite passes to one CSV.
    """

    output_dir = Path(output_config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / filename

    if output_path.exists() and not output_config.overwrite:
        raise FileExistsError(
            f"Output file already exists: {output_path}. "
            "Use --overwrite to replace it."
        )

    df = all_orbits_to_dataframe(orbits)
    df.to_csv(output_path, index=False)

    logger.info(f"Saved {len(df):,} orbit samples to {output_path}")

    return output_path