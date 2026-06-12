from __future__ import annotations

import logging
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

from sat_sim.config import OutputConfig, TimeConfig
from sat_sim.models import OneSatelliteOrbit
# TODO: add more plot types, e.g. sky tracks, Doppler vs elevation, etc.
# TODO: consider adding a CLI command for plotting, e.g. `sat-sim plot --type doppler-curves ...`
# TODO: make a dashboard to run the simulation and show plots in real time, e.g. using Streamlit or a Jupyter notebook.
# TODO: add standard plt style options, maybe in a file?
# plt.rcParams["figure.figsize"] = [8, 5]  # bigger default figure size
# plt.rcParams["font.family"] = "serif"
# plt.rcParams["font.serif"] = ["Times New Roman"] + plt.rcParams["font.serif"]
# plt.rcParams["font.size"] = 17
# plt.rcParams["pdf.fonttype"] = 42  # Ensures editable text in Illustrator

logger = logging.getLogger("sat_sim")

def prepare_plot_dir(output_config: OutputConfig) -> Path:
    """
    Create and return the plot output directory.
    """

    plot_dir = Path(output_config.output_dir) / "plots"
    plot_dir.mkdir(parents=True, exist_ok=True)

    logger.debug(f"Plot directory ready: {plot_dir}")

    return plot_dir

def plot_all_doppler_curves(
    all_orbits: list[OneSatelliteOrbit],
    output_config: OutputConfig,
    filename: str = "all_doppler_curves.png",
) -> Path:
    """
    Plot Doppler shift vs UTC time for all sampled satellite passes.
    One line per satellite pass.
    """

    plot_dir = prepare_plot_dir(output_config)
    output_path = plot_dir / filename

    if output_path.exists() and not output_config.overwrite:
        raise FileExistsError(
            f"Output plot already exists: {output_path}. "
            "Use --overwrite to replace it."
        )

    fig, ax = plt.subplots(figsize=(14, 7))

    plotted = 0

    for orbit in all_orbits:
        if len(orbit.orbit_samples) == 0:
            continue

        sat_pass = orbit.satellite_pass
        samples = orbit.orbit_samples

        times = [
            sample.timestamp_utc
            for sample in samples
        ]

        doppler_hz = [
            sample.doppler_shift_hz
            for sample in samples
        ]

        label = f"{sat_pass.satellite_name} p{sat_pass.pass_idx}"

        ax.plot(
            times,
            np.array(doppler_hz) / 1000,  # Convert to kHz
            linewidth=0.8,
            alpha=0.8,
            label=label,
        )

        plotted += 1

    ax.set_title("Doppler Curves for Visible Satellite Passes")
    ax.set_xlabel("Time (UTC)")
    ax.set_ylabel("Doppler Shift (kHz)")
    ax.grid(True, alpha=0.3)

    ax.xaxis.set_major_formatter(
        mdates.DateFormatter("%H:%M:%S")
    )

    fig.autofmt_xdate()

    if plotted <= 20:
        ax.legend(fontsize=7)

    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)

    logger.info(f"Saved Doppler plot with {plotted} curves to {output_path}")

    return output_path

def plot_all_doppler_curves_by_pass_duration(
    all_orbits: list[OneSatelliteOrbit],
    output_config: OutputConfig,
    time_config: TimeConfig,
    filename: str = "all_doppler_curves_by_pass_duration.png",
) -> Path:
    """
    Plot Doppler shift vs time from start of recording/simulation.

    This should look like the UTC timestamp Doppler plot, except the x-axis
    is elapsed seconds from the simulation start instead of wall-clock time.
    """

    plot_dir = prepare_plot_dir(output_config)
    output_path = plot_dir / filename

    if output_path.exists() and not output_config.overwrite:
        raise FileExistsError(
            f"Output plot already exists: {output_path}. "
            "Use --overwrite to replace it."
        )

    recording_start_utc = time_config.start_dt_utc

    fig, ax = plt.subplots(figsize=(14, 7))

    plotted = 0

    for orbit in all_orbits:
        if len(orbit.orbit_samples) == 0:
            continue

        sat_pass = orbit.satellite_pass
        samples = orbit.orbit_samples

        time_from_recording_start_s = [
            (sample.timestamp_utc.replace(tzinfo=recording_start_utc.tzinfo) - recording_start_utc).total_seconds()
            if sample.timestamp_utc.tzinfo is None
            else (sample.timestamp_utc - recording_start_utc).total_seconds()
            for sample in samples
        ]

        doppler_hz = [
            sample.doppler_shift_hz
            for sample in samples
        ]

        label = f"{sat_pass.satellite_name} p{sat_pass.pass_idx}"

        ax.plot(
            time_from_recording_start_s,
            doppler_hz,
            linewidth=0.8,
            alpha=0.8,
            label=label,
        )

        plotted += 1

    ax.set_title("Doppler Curves vs Time from Recording Start")
    ax.set_xlabel("Time from Recording Start (s)")
    ax.set_ylabel("Doppler Shift (Hz)")
    ax.grid(True, alpha=0.3)

    if plotted <= 20:
        ax.legend(fontsize=7)

    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)

    logger.info(
        f"Saved recording-duration Doppler plot with {plotted} curves to {output_path}"
    )

    return output_path

def plot_all_orbits_polar(
    all_orbits: list[OneSatelliteOrbit],
    output_config: OutputConfig,
    filename: str = "all_sky_tracks_polar.png",
) -> Path:
    """
    Plot satellite sky tracks as a polar azimuth/elevation plot.

    Convention:
        theta = azimuth in radians
        r = 90 - elevation

    Therefore:
        center = zenith, elevation 90 deg
        outer edge = horizon, elevation 0 deg
    """

    plot_dir = prepare_plot_dir(output_config)
    output_path = plot_dir / filename

    if output_path.exists() and not output_config.overwrite:
        raise FileExistsError(
            f"Output plot already exists: {output_path}. "
            "Use --overwrite to replace it."
        )

    fig, ax = plt.subplots(
        figsize=(9, 9),
        subplot_kw={"projection": "polar"},
    )

    plotted = 0

    for orbit in all_orbits:
        if len(orbit.orbit_samples) == 0:
            continue

        sat_pass = orbit.satellite_pass
        samples = orbit.orbit_samples

        az_rad = [
            np.deg2rad(sample.azimuth_deg)
            for sample in samples
        ]

        radius = [
            90.0 - sample.elevation_deg
            for sample in samples
        ]

        label = f"{sat_pass.satellite_name} p{sat_pass.pass_idx}"

        ax.plot(
            az_rad,
            radius,
            linewidth=0.8,
            alpha=0.75,
            label=label,
        )

        # Optional: mark start/end, but small because many tracks get cluttered.
        ax.scatter(
            az_rad[0],
            radius[0],
            s=8,
            marker="o",
            alpha=0.7,
        )

        ax.scatter(
            az_rad[-1],
            radius[-1],
            s=8,
            marker="x",
            alpha=0.7,
        )

        plotted += 1

    # North at top, azimuth increasing clockwise.
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)

    # IMPORTANT:
    # Do NOT invert rlim because radius = 90 - elevation already handles it.
    ax.set_rlim(0, 90)

    # Radial ticks are radius values, but labels should show elevation.
    radius_ticks = [0, 15, 30, 45, 60, 75, 90]
    elevation_labels = ["90°", "75°", "60°", "45°", "30°", "15°", "0°"]

    ax.set_rticks(radius_ticks)
    ax.set_yticklabels(elevation_labels)

    ax.set_title("Satellite Sky Tracks", pad=25)

    # Put radial elevation labels away from the densest default location.
    ax.set_rlabel_position(22.5)

    ax.grid(True, alpha=0.35)

    if plotted <= 20:
        ax.legend(
            fontsize=7,
            loc="upper right",
            bbox_to_anchor=(1.30, 1.12),
        )

    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)

    logger.info(f"Saved polar sky-track plot with {plotted} tracks to {output_path}")

    return output_path