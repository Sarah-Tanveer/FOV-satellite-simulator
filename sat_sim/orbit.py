from __future__ import annotations

import os
import logging
from datetime import timedelta

from scipy.constants import speed_of_light
from skyfield.timelib import Time, Timescale

from sat_sim.config import ExecutionConfig, RFConfig, TimeConfig
from sat_sim.models import OrbitSample, SatellitePass, OneSatelliteOrbit
from sat_sim.station import GroundStation
from skyfield.units import Velocity, Angle, AngleRate, Distance
from typing import Any
from concurrent.futures import ThreadPoolExecutor, as_completed, ProcessPoolExecutor

C_KM_PER_S = speed_of_light / 1000.0

def calc_doppler_shift(freq_hz: float, range_rate_km_s: float) -> float:
    """
    # TODO: confirm datatype of range_rate from skyfield api
    Calculate the Doppler shift for a given frequency and relative velocity.

    Parameters
    ----------
    freq_hz:
        center frequency in Hz.
    range_rate_km_s:
        Range rate in km/s
    Returns
    -------
    float
        Doppler-shifted frequency in Hz.
    -------
    Sign convention
    ---------------
    If range_rate_km_s is negative, the satellite is approaching.
    That gives positive Doppler.

    doppler = f0 * (-range_rate / c)
    """
    # print(f"range_rate: {type(range_rate_km_s)}, value: {range_rate_km_s}")
    return freq_hz * ((-1 * range_rate_km_s) / C_KM_PER_S) # make sure that the range rate units and speed of lifht units match 

def check_elevation_limit(
    el_deg: float,
    min_elevation_deg: float,
    max_elevation_deg: float | None = None, logger: logging.Logger | None = None
) -> bool:
    """
    Check if the satellite is above the minimum elevation limit and below the maximum elevation limit (if provided).
    """

    if el_deg < min_elevation_deg:
        if logger:
            logger.error("Elevation %.2f deg is below the minimum elevation limit of %.2f deg. Skipping sample.", el_deg, min_elevation_deg)
        return False

    if max_elevation_deg is not None and el_deg > max_elevation_deg:
        if logger:
            logger.debug("Elevation %.2f deg is above the maximum elevation limit of %.2f deg. Skipping sample.", el_deg, max_elevation_deg)
        return False

    return True

def advance_time_by_step(time: Time, time_step: float, timescale: Timescale) -> Time:
    """
    Advance a skyfield Time object by a certain number of seconds.
    We use the timescale from the config to maintain consistency in time handling across the codebase. (This seemed to lead to errors previously)
    """
    return timescale.utc(
        time.utc_datetime() + timedelta(seconds=time_step))

def get_alt_az_range(sat_pos: Any, ground_station_loc: Any) -> tuple[Angle, Angle, Distance, AngleRate, AngleRate, Velocity]:
        info = sat_pos.frame_latlon_and_rates(ground_station_loc)
        alt_deg: Angle = info[0]
        az_deg: Angle = info[1]
        radial_distance: Distance = info[2]
        lat_rate: AngleRate = info[3]
        lon_rate: AngleRate = info[4]
        range_rate: Velocity = info[5]
        return alt_deg, az_deg, radial_distance, lat_rate, lon_rate, range_rate

def sample_orbit_for_one_pass(satellite_pass: SatellitePass,
                          station: GroundStation,
                          rf_config: RFConfig,
                          execution_config: ExecutionConfig,
                          time_config: TimeConfig,
                          logger: logging.Logger | None = None) -> OneSatelliteOrbit:
    """
    Sample the orbit for one satellite *pass* during a pass at regular time intervals defined by execution_config.step_s.
    FOV sats are already filtered out by min elevation, location, time window
    """
    if logger is None:
        logger = logging.getLogger("sat_sim")
    
    satellite = satellite_pass.satellite
    skyfield_sat = satellite.skyfield_sat
    ground_station_loc = station.skyfield_position

    samples: list[OrbitSample] = []

    current_time = satellite_pass.start_time

    # .tt is used to comapre skyfield time datatypes; so we need to make sure to use the skufiled time object (this is true for the satellite pass class)
    while current_time.tt <= satellite_pass.end_time.tt:
        # pos of satellite relative to ground station at current time
        pos = (skyfield_sat - ground_station_loc).at(current_time)
        # Anlge, Angle, Distance, AngleRate, AngleRate, Velocity (skyfield datatypes)
        # alt_deg: Angle, az_deg: Angle, radial_distance: Distance, lat_rate: AngleRate, lon_rate: AngleRate, range_rate: Velocity = pos.frame_latlon_and_rates(ground_station_loc)
        alt_deg, az_deg, radial_distance, lat_rate, lon_rate, range_rate = get_alt_az_range(pos, ground_station_loc)
        el_deg = float(alt_deg.degrees)
        az_deg = float(az_deg.degrees % 360) # make sure az is between 0 and 360
        range_km = float(radial_distance.km)
        range_rate_km_s = float(range_rate.km_per_s)

        # filerting based on elevation limits
        if not check_elevation_limit(
            el_deg=el_deg,
            min_elevation_deg=execution_config.min_elevation_deg,
            max_elevation_deg=execution_config.max_elevation_deg, logger=logger
        ):
            current_time = advance_time_by_step(current_time, execution_config.step_s, time_config.timescale)
            continue

        doppler_shift_hz = calc_doppler_shift(freq_hz=rf_config.center_freq_hz, range_rate_km_s=range_rate_km_s)
        dt = (current_time.utc_datetime() - satellite_pass.start_time.utc_datetime()).total_seconds()
        

        sample = OrbitSample(
            satellite=satellite,
            satellite_name=satellite.name,
            satellite_norad_id=satellite.norad_id,
            generation=satellite.generation,
            pass_idx=satellite_pass.pass_idx,
            timestamp=current_time,
            timestamp_utc=current_time.utc_datetime().replace(tzinfo=None),
            time_from_start_of_pass_s=dt,
            azimuth_deg=az_deg,
            elevation_deg=el_deg,
            range_km=range_km,
            range_rate_km_s=range_rate_km_s,
            doppler_shift_hz=doppler_shift_hz,
            tle_epoch_utc=satellite.tle_epoch_utc,
            tle_age_days=satellite.tle_age_days,    
            tle_age_hours=satellite.tle_age_days * 24.0) # convert to hours for easier interpretation
        samples.append(sample)

        current_time = advance_time_by_step(
            current_time,
            execution_config.step_s,
            time_config.timescale,
        )

    logger.debug(
        f"Sampled orbit for satellite {satellite.name} | "
        f"NORAD={satellite.norad_id} | "
        f"pass={satellite_pass.pass_idx} | "
        f"start={satellite_pass.start_time.utc_iso()} | "
        f"end={satellite_pass.end_time.utc_iso()} | "
        f"samples={len(samples)}"
    )
    return OneSatelliteOrbit(satellite_pass=satellite_pass, orbit_samples=samples)

def sample_orbit_worker(
    satellite_pass: SatellitePass,
    station: GroundStation,
    rf_config: RFConfig,
    execution_config: ExecutionConfig,
    time_config: TimeConfig,
) -> OneSatelliteOrbit:
    """
    Worker wrapper for parallel orbit sampling.

    This intentionally does not take a logger because loggers do not behave
    cleanly across multiprocessing on Windows.
    """

    return sample_orbit_for_one_pass(
        satellite_pass=satellite_pass,
        station=station,
        rf_config=rf_config,
        execution_config=execution_config,
        time_config=time_config,
        logger=None,
    )

def sample_orbits_for_all_passes(
        satellite_passes: list[SatellitePass],
        station: GroundStation,
        rf_config: RFConfig,
        execution_config: ExecutionConfig,
        time_config: TimeConfig,
        logger: logging.Logger | None = None) -> list[OneSatelliteOrbit]:
    """
    Sample the orbits for all visible satellite passes.
    Sample the orbits for all visible satellite passes.

    If execution_config.parallel is False:
        run serially.

    If execution_config.parallel is True:
        parallelize over satellite passes.
    """
    if logger is None:
        logger = logging.getLogger("sat_sim")
    
    logger.info(f"Orbit time step: {execution_config.step_s} seconds")
    logger.info(f"Parallel enabled: {execution_config.parallel}")
    if execution_config.parallel:
        logger.info(f"Workers: {execution_config.workers}")
    
    if not execution_config.parallel:
        all_orbits: list[OneSatelliteOrbit] = []

        for sat_pass in satellite_passes:
            samples_for_pass = sample_orbit_for_one_pass(
                satellite_pass=sat_pass,
                station=station,
                rf_config=rf_config,
                execution_config=execution_config,
                time_config=time_config,
                logger=logger
            )
            all_orbits.append(samples_for_pass)

        total_samples = sum(
        len(one_orbit.orbit_samples)
        for one_orbit in all_orbits
    )

        logger.info(
            f"Sampled orbits for {len(satellite_passes)} satellite passes, "
            f"resulting in {total_samples} total samples"
        )
        return all_orbits

    all_orbits = []
    executor_cls = ThreadPoolExecutor if os.name == "nt" else ProcessPoolExecutor
    logger.info("Parallel executor: %s", executor_cls.__name__)

    with executor_cls(max_workers=execution_config.workers) as executor:
        future_to_pass = {
            executor.submit(
                sample_orbit_worker,
                satellite_pass=sat_pass,
                station=station,
                rf_config=rf_config,
                execution_config=execution_config,
                time_config=time_config,
            ): sat_pass
            for sat_pass in satellite_passes
        }

        for future in as_completed(future_to_pass):
            sat_pass = future_to_pass[future]
            try:
                one_orbit = future.result()
                all_orbits.append(one_orbit)
            except Exception as exc:
                logger.error(
                    f"Error sampling orbit for satellite {sat_pass.satellite_name} "
                    f"pass {sat_pass.pass_idx}: {exc}"
                )
                continue
        # Keep deterministic order after parallel execution.
    all_orbits.sort(
        key=lambda orbit: (
            orbit.satellite_pass.satellite_name,
            orbit.satellite_pass.pass_idx,
            orbit.satellite_pass.start_time.tt,
        )
    )

    total_samples = sum(
        len(one_orbit.orbit_samples)
        for one_orbit in all_orbits
    )

    logger.info(
        f"Sampled orbits for {len(all_orbits)} / {len(satellite_passes)} satellite passes, "
        f"resulting in {total_samples} total samples"
    )

    return all_orbits
