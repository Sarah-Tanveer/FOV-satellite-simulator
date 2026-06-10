from __future__ import annotations

import logging
from collections import defaultdict

from skyfield.timelib import Time

from sat_sim.config import ExecutionConfig, TimeConfig
from sat_sim.models import Satellite, SatellitePass
from sat_sim.station import GroundStation


RISE_EVENT = 0
PEAK_EVENT = 1
SET_EVENT = 2


def find_visible_passes(
    satellites: list[Satellite],
    station: GroundStation,
    time_config: TimeConfig,
    execution_config: ExecutionConfig,
    logger: logging.Logger | None = None,
) -> list[SatellitePass]:
    """
    Find satellite passes over the ground station.

    This replaces the older check_field_of_view() function, but keeps
    the same core idea:

        1. Check whether the satellite is already above the elevation
           threshold at the simulation start.
        2. Ask Skyfield for rise/peak/set events.
        3. Convert those events into SatellitePass objects.
        4. Use start_time/end_time as the actual clipped simulation interval.

    Important distinction
    ---------------------
    rise_time / peak_time / set_time:
        Actual Skyfield events inside the query window, if present.

    start_time / end_time:
        The time interval we actually simulate for this pass.

    Therefore:
        rise_time can be None, but start_time should never be None.
        set_time can be None, but end_time should never be None.
    
    Note: 
        For now we dont consider the max_elevation_deg parameter in execution_config when finding passes.
        Instead, we will apply the max elevation limit later during orbit sampling.
        This is because skyfield api does not take max elevation limit as input for find_events (unlike gpredict etc)
    """

    if logger is None:
        logger = logging.getLogger("sat_sim")

    start_time = time_config.start_sf
    end_time = time_config.end_sf
    min_elevation_deg = execution_config.min_elevation_deg

    logger.debug(
        "Finding visible passes for %d satellites from %s to %s",
        len(satellites),
        start_time.utc_iso(),
        end_time.utc_iso(),
    )
    logger.debug("Minimum elevation threshold: %.2f deg", min_elevation_deg)

    if execution_config.max_elevation_deg is not None:
        logger.debug(
            "Maximum elevation limit %.2f deg will be applied later during orbit sampling",
            execution_config.max_elevation_deg,
        )

    all_passes: list[SatellitePass] = []
    pass_counts_by_satellite: dict[str, int] = defaultdict(int) # {sat: count, ....}

    for satellite in satellites:
        pass_start_index = pass_counts_by_satellite[satellite.name] # default dict so when this key doesnt exist it will initilise by itself to 0 (since int datatype is specified)

        sat_passes = find_passes_for_one_satellite(
            satellite=satellite,
            station=station,
            start_time=start_time,
            end_time=end_time,
            min_elevation_deg=min_elevation_deg,
            pass_start_index=pass_start_index,
            logger=logger,
        )

        all_passes.extend(sat_passes)
        pass_counts_by_satellite[satellite.name] += len(sat_passes)

    visible_satellite_names = {sat_pass.satellite_name for sat_pass in all_passes}

    logger.info("Found %d visible passes", len(all_passes))
    logger.info("Found %d visible satellites", len(visible_satellite_names))

    # Note: the satellites get filtered out while reading tle in debug mode
    if execution_config.debug_sat_names_file is not None:
        for sat in satellites:
            if sat.name not in visible_satellite_names:
                logger.error(
                    f"Satellite loaded but not visible in FOV/time window: {sat.name}"
                )

    return all_passes


def find_passes_for_one_satellite(
    satellite: Satellite,
    station: GroundStation,
    start_time: Time,
    end_time: Time,
    min_elevation_deg: float,
    pass_start_index: int = 0,
    logger: logging.Logger | None = None,
) -> list[SatellitePass]:
    """
    Find all passes for one satellite within the simulation window.

    Logic
    -----
    Case A: satellite has rise event, no need to check peak event
        start_time = rise event
        if set event exists:
            end_time = set event
        else:
            end_time = simulation end

    Case B: satellite has peak/set event but no rise event
        satellite was already visible at simulation start
        start_time = simulation start
        end_time = set event or simulation end

    Case C: no events
        if satellite is visible at simulation start: check explicitly using altaz() and min_elevation_deg
            start_time = simulation start
            end_time = simulation end
        else:
            no pass
    """

    if logger is None:
        logger = logging.getLogger("sat_sim")

    skyfield_sat = satellite.skyfield_sat
    ground_station = station.skyfield_position

    passes: list[SatellitePass] = []

    # ------------------------------------------------------------
    # Check whether satellite is already visible at simulation start.
    # This is the key check for the edge case:
    # satellite already in FOV at start and no events occur before end.
    # ------------------------------------------------------------
    alt_start, _, _ = (skyfield_sat - ground_station).at(start_time).altaz()
    visible_at_start = alt_start.degrees >= min_elevation_deg

    event_times, event_types = skyfield_sat.find_events(
        ground_station,
        start_time,
        end_time,
        altitude_degrees=min_elevation_deg,
    )

    events: list[tuple[Time, int]] = [
        (event_time, int(event_type))
        for event_time, event_type in zip(event_times, event_types)
    ]

    logger.debug(
        "%s: visible_at_start=%s, alt_start=%.2f deg, events=%s",
        satellite.name,
        visible_at_start,
        alt_start.degrees,
        [(t.utc_iso(), e) for t, e in events],
    )

    # ------------------------------------------------------------
    # Case C: will probably happen for shorter simulation windows
    # No events inside the simulation window.
    # If visible at start, then pass is the whole simulation window.
    # If not visible at start, then no pass.
    # ------------------------------------------------------------
    if len(events) == 0:
        if not visible_at_start:
            return []

        duration_s = skyfield_duration_seconds(start_time, end_time)

        return [
            SatellitePass(
                satellite=satellite,
                satellite_name=satellite.name,
                satellite_norad_id=satellite.norad_id,
                pass_idx=pass_start_index,
                rise_time=None,
                peak_time=None,
                set_time=None,
                start_time=start_time,
                end_time=end_time,
                duration_s=duration_s,
                starts_before_window=True,
                ends_after_window=True,
            )
        ]

    # ------------------------------------------------------------
    # If visible at simulation start, we are already inside a pass.
    # The real rise happened before the simulation window.
    # ------------------------------------------------------------
    current_start_time: Time | None = start_time if visible_at_start else None
    current_rise_time: Time | None = None
    current_peak_time: Time | None = None
    starts_before_window = visible_at_start

    for event_time, event_type in events:
        if event_type == RISE_EVENT:
            # Start a new pass.
            current_start_time = event_time
            current_rise_time = event_time
            current_peak_time = None
            starts_before_window = False

        elif event_type == PEAK_EVENT:
            # Peak belongs to the current pass.
            current_peak_time = event_time

            # If there is a peak but no rise, the satellite was already visible.
            if current_start_time is None:
                current_start_time = start_time
                current_rise_time = None
                starts_before_window = True

        elif event_type == SET_EVENT:
            # If there is a set but no rise, the satellite was already visible.
            if current_start_time is None:
                if visible_at_start:
                    current_start_time = start_time
                    current_rise_time = None
                    starts_before_window = True
                else:
                    # Defensive skip. A set without being visible at start
                    # should not normally produce a usable pass.
                    continue

            pass_end_time = event_time
            duration_s = skyfield_duration_seconds(current_start_time, pass_end_time)

            if duration_s > 0:
                pass_idx = pass_start_index + len(passes)

                passes.append(
                    SatellitePass(
                        satellite=satellite,
                        satellite_name=satellite.name,
                        satellite_norad_id=satellite.norad_id,
                        pass_idx=pass_idx,
                        rise_time=current_rise_time,
                        peak_time=current_peak_time,
                        set_time=event_time,
                        start_time=current_start_time,
                        end_time=pass_end_time,
                        duration_s=duration_s,
                        starts_before_window=starts_before_window,
                        ends_after_window=False,
                    )
                )

            # Reset after set.
            current_start_time = None
            current_rise_time = None
            current_peak_time = None
            starts_before_window = False
            visible_at_start = False

    # ------------------------------------------------------------
    # If we started a pass but never saw a set before simulation end,
    # close the pass at simulation end.
    # ------------------------------------------------------------
    if current_start_time is not None:
        duration_s = skyfield_duration_seconds(current_start_time, end_time)

        if duration_s > 0:
            pass_idx = pass_start_index + len(passes)

            passes.append(
                SatellitePass(
                    satellite=satellite,
                    satellite_name=satellite.name,
                    satellite_norad_id=satellite.norad_id,
                    pass_idx=pass_idx,
                    rise_time=current_rise_time,
                    peak_time=current_peak_time,
                    set_time=None,
                    start_time=current_start_time,
                    end_time=end_time,
                    duration_s=duration_s,
                    starts_before_window=starts_before_window,
                    ends_after_window=True,
                )
            )

    if passes:
        logger.debug(
            "%s: found %d pass(es)",
            satellite.name,
            len(passes),
        )

    return passes


def skyfield_duration_seconds(start_time: Time, end_time: Time) -> float:
    """
    Duration between two Skyfield Time objects in seconds.
    """

    return (end_time.utc_datetime() - start_time.utc_datetime()).total_seconds()