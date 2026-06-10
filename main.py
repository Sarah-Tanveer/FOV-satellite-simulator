from __future__ import annotations
import time


from sat_sim.args import parse_args
from sat_sim.logging_utils import setup_logger
from sat_sim.station import GroundStation
from sat_sim.tle import load_satellites
from sat_sim.fov_sats import find_visible_passes
from sat_sim.orbit import sample_orbits_for_all_passes
from sat_sim.output import save_all_orbits_to_csv
from sat_sim.plotting import (
    plot_all_doppler_curves,
    plot_all_doppler_curves_by_pass_duration,
    plot_all_orbits_polar,
)
from sat_sim.tle import load_satellites

def main():
    overall_start_time = time.time()
    config = parse_args()

    logger = setup_logger(
        name="sat_sim",
        level=config.output.log_level,
        log_file=config.output.log_file,
    )

    station = GroundStation.from_config(config.ground_station)

    logger.info("Simulation config loaded")

    logger.info("Time configuration")
    logger.info(f"  Start local:    {config.time.start_dt}")
    logger.info(f"  End local:      {config.time.end_dt}")
    logger.debug(f"  Start UTC:      {config.time.start_dt_utc}")
    logger.debug(f"  End UTC:        {config.time.end_dt_utc}")
    logger.debug(f"  Start Skyfield: {config.time.start_sf.utc_iso()}")
    logger.debug(f"  End Skyfield:   {config.time.end_sf.utc_iso()}")
    logger.info(f"  Duration:       {config.time.duration_s:.3f} s")
    logger.info(f"  Timezone:       {config.time.timezone}")

    logger.info("Ground station")
    logger.info(f"  {station.display_name}")

    logger.debug("RF configuration")
    logger.debug(f"  Center freq:    {config.rf.center_freq_hz:.3f} Hz")

    logger.info("TLE configuration")
    logger.info(f"  TLE file:       {config.tle.tle_file}")

    logger.info("Execution configuration")
    logger.info(f"  Step:           {config.execution.step_s:.3f} s")
    logger.info(f"  Min elevation:  {config.execution.min_elevation_deg:.2f} deg")
    logger.info(f"  Max elevation:  {config.execution.max_elevation_deg}")
    logger.info(f"  Workers:        {config.execution.workers}")
    logger.info(f"  Parallel:       {config.execution.parallel}")

    logger.info("Output configuration")
    logger.info(f"  Output dir:     {config.output.output_dir}")
    logger.info(f"  Overwrite:      {config.output.overwrite}")
    logger.info(f"  Log level:      {config.output.log_level}")
    logger.info(f"  Log file:       {config.output.log_file}")

    # ------------------------------------------------------------
    # Load satellites from TLE
    # ------------------------------------------------------------
    satellites = load_satellites(
        tle_config=config.tle,
        time_config=config.time,
        execution_config=config.execution,
        logger=logger,
    )

    logger.debug("First few loaded satellites:")
    for sat in satellites[:5]:
        logger.debug(
            f"  {sat.name} | NORAD={sat.norad_id} | "
            f"TLE epoch={sat.tle_epoch_utc.isoformat()} | "
            f"TLE age={sat.tle_age_days:.3f} days | "
            f"generation={sat.generation}"
        )

    # ------------------------------------------------------------
    # Find visible satellite passes
    # ------------------------------------------------------------
    satellite_passes = find_visible_passes(
        satellites=satellites,
        station=station,
        time_config=config.time,
        execution_config=config.execution,
        logger=logger,
    )

    logger.debug("First few visible passes:")
    for sat_pass in satellite_passes[:10]:
        logger.debug(
            f"  {sat_pass.satellite_name} | "
            f"NORAD={sat_pass.satellite_norad_id} | "
            f"pass={sat_pass.pass_idx} | "
            f"start={sat_pass.start_time.utc_iso()} | "
            f"end={sat_pass.end_time.utc_iso()} | "
            f"duration={sat_pass.duration_s:.1f} s | "
            f"rise={sat_pass.rise_time.utc_iso() if sat_pass.rise_time is not None else None} | "
            f"peak={sat_pass.peak_time.utc_iso() if sat_pass.peak_time is not None else None} | "
            f"set={sat_pass.set_time.utc_iso() if sat_pass.set_time is not None else None} | "
            f"starts_before_window={sat_pass.starts_before_window} | "
            f"ends_after_window={sat_pass.ends_after_window}"
        )

    # ------------------------------------------------------------
    # Sample orbit/Doppler for all visible passes
    # ------------------------------------------------------------
    orbits = sample_orbits_for_all_passes(
        satellite_passes=satellite_passes,
        station=station,
        rf_config=config.rf,
        execution_config=config.execution,
        time_config=config.time,
        logger=logger,
    )

    logger.info("First few orbit samples:")
    for sample in orbits[:5]:
        logger.info(
            f"satellite={sample.satellite_pass.satellite_name} | "
            f"pass={sample.satellite_pass.pass_idx} | "
        )
        for orbit_sample in sample.orbit_samples[:5]:
            logger.info(
                f"  t={orbit_sample.timestamp.utc_iso()} | "
                f"  el={orbit_sample.elevation_deg:.2f} deg | "
                f"  az={orbit_sample.azimuth_deg:.2f} deg | "
                f"  range={orbit_sample.range_km:.2f} km | "
                f"  rr={orbit_sample.range_rate_km_s:.6f} km/s | "
                f"  doppler={orbit_sample.doppler_shift_hz:.2f} Hz"
            )

    logger.info(f"Loaded satellites: {len(satellites)}")
    logger.info(f"Visible passes:    {len(satellite_passes)}")
    logger.info(f"Orbits:     {len(orbits)}")
    logger.info(f"Number of orbit samples: {sum(len(orbit.orbit_samples) for orbit in orbits)}")

    orbit_samples_csv = save_all_orbits_to_csv(
    orbits=orbits,
    output_config=config.output,
)
    logger.info(f"Saved orbit samples to CSV: {orbit_samples_csv}")
    doppler_plot = plot_all_doppler_curves(
    all_orbits=orbits,
    output_config=config.output,)

    logger.info(f"Saved Doppler plot:       {doppler_plot}")

    doppler_duration_plot = plot_all_doppler_curves_by_pass_duration(
        all_orbits=orbits,
        output_config=config.output, time_config=config.time,
    )

    logger.info(f"Saved Doppler duration plot: {doppler_duration_plot}")

    polar_plot = plot_all_orbits_polar(
    all_orbits=orbits,
    output_config=config.output,
    )

    logger.info(f"Saved polar plot:         {polar_plot}")

    overall_end_time = time.time()
    overall_duration = overall_end_time - overall_start_time
    logger.info(f"Overall execution time: {overall_duration:.2f} seconds")
    logger.info("Done.")


if __name__ == "__main__":
    main()