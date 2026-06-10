# Satellite Doppler Pass Simulator

A modular Python simulator for predicting satellite visibility, sky tracks, and Doppler shifts over a ground station.

The simulator takes a TLE file, a time window, a ground-station location, and RF center frequency, then:

1. Loads satellites from TLE.
2. Finds satellites visible in the simulation window.
3. Samples each visible satellite pass.
4. Computes azimuth, elevation, range, range-rate, and Doppler shift.
5. Saves CSV outputs.
6. Generates Doppler and sky-track plots.

This code is designed for satellite signal attribution experiments, Doppler-based identification, and later IQ/spectrum compensation workflows.

---

## Project structure

```text
simulator/
├── main.py
├── sat_sim/
│   ├── __init__.py
│   ├── args.py
│   ├── config.py
│   ├── constants.py
│   ├── fov_sats.py
│   ├── logging_utils.py
│   ├── models.py
│   ├── orbit.py
│   ├── outputs.py
│   ├── plotting.py
│   ├── station.py
│   └── tle.py
└── README.md
```

### Main modules

| File               | Purpose                                             |
| ------------------ | --------------------------------------------------- |
| `main.py`          | Top-level simulator pipeline                        |
| `args.py`          | Command-line parsing and config construction        |
| `config.py`        | Simulation configuration dataclasses                |
| `models.py`        | Core dataclasses: satellites, passes, orbit samples |
| `tle.py`           | TLE loading and optional debug satellite filtering  |
| `fov_sats.py`      | Finds visible satellite passes                      |
| `orbit.py`         | Samples orbit geometry and Doppler                  |
| `outputs.py`       | Saves CSV outputs                                   |
| `plotting.py`      | Generates Doppler and polar sky-track plots         |
| `station.py`       | Builds ground-station object                        |
| `logging_utils.py` | Logger setup                                        |
| `constants.py`     | Shared constants such as CSV headers                |

---

## Installation

Create an environment and install dependencies:

```bash
pip install numpy pandas matplotlib scipy skyfield
```

If using parallel execution, no extra dependency is needed because the simulator uses Python’s standard multiprocessing tools.

---

## Basic usage

Run a simulation with a local TLE file:

```bash
python main.py --start-time "16-07-2025 16:00:00" --duration 1800 --tz America/Chicago --tle-file ".\starlink.tle" --station-label eng --overwrite
```

This simulates a 30-minute window starting at local time `2025-07-16 16:00:00` in the `America/Chicago` timezone.

---

## Example commands

### Run with default settings

```bash
python main.py
```

### Run a 30-minute simulation

```bash
python main.py --start-time "16-07-2025 16:00:00" --duration 1800 --tz America/Chicago --tle-file ".\starlink.tle" --station-label eng --overwrite
```

### Run a 10-hour simulation

```bash
python main.py --start-time "16-07-2025 16:00:00" --duration 36000 --tz America/Chicago --tle-file ".\starlink.tle" --station-label eng --overwrite
```

### Use dish elevation limits

```bash
python main.py --start-time "16-07-2025 16:00:00" --duration 36000 --tz America/Chicago --tle-file ".\starlink.tle" --min-elevation 16 --max-elevation 65 --station-label eng --overwrite
```

### Use a different RF center frequency

```bash
python main.py --start-time "16-07-2025 16:00:00" --duration 1800 --tz America/Chicago --tle-file ".\starlink.tle" --center-freq 11575000000 --station-label eng --overwrite
```

### Run in parallel

```bash
python main.py --start-time "16-07-2025 16:00:00" --duration 36000 --tz America/Chicago --tle-file ".\starlink.tle" --parallel --workers 8 --station-label eng --overwrite
```

---

## Command-line options

| Argument                 | Description                                                                                  |
| ------------------------ | -------------------------------------------------------------------------------------------- |
| `--start-time`           | Simulation start time. Supports `"now"`, `"DD-MM-YYYY HH:MM:SS"`, or `"YYYY-MM-DD HH:MM:SS"` |
| `--end-time`             | Simulation end time                                                                          |
| `--duration`             | Simulation duration in seconds                                                               |
| `--tz`                   | Timezone, for example `UTC` or `America/Chicago`                                             |
| `--lat`                  | Ground-station latitude in degrees                                                           |
| `--lon`                  | Ground-station longitude in degrees                                                          |
| `--alt`                  | Ground-station altitude in meters                                                            |
| `--station-label`        | Optional human-readable ground-station label                                                 |
| `--center-freq`          | RF center frequency in Hz                                                                    |
| `--tle-file`             | Path to local TLE file                                                                       |
| `--step-s`               | Orbit sampling step in seconds                                                               |
| `--min-elevation`        | Minimum elevation angle in degrees                                                           |
| `--max-elevation`        | Optional maximum elevation angle in degrees                                                  |
| `--parallel`             | Enable parallel orbit sampling                                                               |
| `--workers`              | Number of parallel workers                                                                   |
| `--output-dir`           | Base output directory                                                                        |
| `--overwrite`            | Allow overwriting existing output files                                                      |
| `--log-level`            | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR`                                           |
| `--log-file`             | Optional path to save logs                                                                   |
| `--debug-sat-names-file` | Optional text file containing satellite names to simulate                                    |

---

## Output directory format

The simulator automatically creates a run-specific output directory using:

```text
{start_time}_duration_{duration}_{station_label}
```

For example:

```text
outputs/2025-07-16_16-00-00_duration_30m_eng/
```

If no station label is provided, the station label is omitted:

```text
outputs/2025-07-16_16-00-00_duration_30m/
```

---

## Output files

A typical run produces:

```text
outputs/2025-07-16_16-00-00_duration_30m_eng/
├── passes.csv
├── orbit_samples.csv
└── plots/
    ├── all_doppler_curves.png
    ├── all_doppler_curves_by_recording_duration.png
    └── all_sky_tracks_polar.png
```

### `passes.csv`
TODO:
One row per visible satellite pass.

Typical columns include:

| Column             | Description                                    |
| ------------------ | ---------------------------------------------- |
| `Satellite`        | Satellite name from TLE                        |
| `Norad ID`         | NORAD catalog ID                               |
| `Generation`       | Optional generation label                      |
| `Pass ID`          | Pass index for that satellite                  |
| `Rise Time (UTC)`  | Rise time within simulation window, if present |
| `Peak Time (UTC)`  | Peak time within simulation window, if present |
| `Set Time (UTC)`   | Set time within simulation window, if present  |
| `Start Time (UTC)` | Clipped start time used for sampling           |
| `End Time (UTC)`   | Clipped end time used for sampling             |
| `Duration (s)`     | Pass duration in seconds                       |
| `TLE Epoch (UTC)`  | TLE epoch timestamp                            |
| `TLE Age (days)`   | TLE age at simulation start                    |
| `TLE Age (hours)`  | TLE age at simulation start                    |

### `orbit_samples.csv`

One row per sampled time point.

Typical columns include:

| Column               | Description                            |
| -------------------- | -------------------------------------- |
| `Satellite`          | Satellite name                         |
| `Norad ID`           | NORAD catalog ID                       |
| `Pass ID`            | Pass index                             |
| `Generation`         | Optional generation label              |
| `Timestamp (UTC)`    | Sample timestamp                       |
| `Doppler Shift (Hz)` | Predicted Doppler shift                |
| `Elevation`          | Elevation angle in degrees             |
| `Azimuth`            | Azimuth angle in degrees               |
| `Distance (km)`      | Range from ground station to satellite |
| `TLE Age (hours)`    | TLE age at simulation start            |

---

## Plots

### Doppler vs UTC time

```text
plots/all_doppler_curves.png
```

Plots Doppler shift against absolute UTC timestamp.

This is useful for comparing the simulated Doppler curves directly with a real recording timeline.

### Doppler vs recording duration

```text
plots/all_doppler_curves_by_recording_duration.png
```

Plots Doppler shift against elapsed seconds from the simulation or recording start.

This should look identical to the UTC-time Doppler plot, except the x-axis is in seconds rather than timestamps.

### Polar sky-track plot

```text
plots/all_sky_tracks_polar.png
```

Plots satellite sky tracks in azimuth/elevation coordinates.

The convention is:

```text
theta = azimuth
r = 90 - elevation
```

So:

```text
center = zenith, 90 degrees elevation
outer edge = horizon, 0 degrees elevation
```

---

## Doppler sign convention

The simulator uses:

```text
doppler = f0 * (-range_rate / c)
```

where:

| Quantity     | Meaning                                         |
| ------------ | ----------------------------------------------- |
| `f0`         | RF center frequency in Hz                       |
| `range_rate` | satellite range-rate relative to ground station |
| `c`          | speed of light                                  |

Sign convention:

```text
range_rate < 0  -> satellite approaching -> positive Doppler
range_rate > 0  -> satellite receding    -> negative Doppler
```

---

## Elevation filtering

The simulator applies elevation constraints in two places:

1. `fov_sats.py` finds candidate passes using the minimum elevation threshold.
2. `orbit.py` filters individual samples using both minimum and maximum elevation limits.

This allows hardware constraints such as:

```text
16 degrees <= elevation <= 65 degrees
```

The maximum elevation is applied during orbit sampling because Skyfield’s event finder naturally works with threshold crossings, not arbitrary min/max tracking windows.

---

## Debug satellite subset mode

For debugging, you can restrict simulation to a few satellites.

Create a text file:

```text
debug_sats.txt
```

Example:

```text
STARLINK-1011
STARLINK-1029
STARLINK-1035
```

Then run:

```bash
python main.py --start-time "16-07-2025 16:00:00" --duration 1800 --tz America/Chicago --tle-file ".\starlink.tle" --debug-sat-names-file ".\debug_sats.txt" --station-label eng --overwrite
```

Behavior:

* If a requested satellite is not found in the TLE, the simulator logs an error and continues.
* If a requested satellite is found in the TLE but is not visible in the simulation window, the simulator logs an error and continues.
* Only requested satellites are considered.

---

## Parallel execution

Parallel orbit sampling can be enabled with:

```bash
--parallel
```

Optionally specify worker count:

```bash
--workers 8
```

Example:

```bash
python main.py --start-time "16-07-2025 16:00:00" --duration 36000 --tz America/Chicago --tle-file ".\starlink.tle" --parallel --workers 8 --station-label eng --overwrite
```

Parallelization is performed over satellite passes:

```text
SatellitePass -> OneSatelliteOrbit
```

This means each visible pass is sampled independently.

For small simulations, parallel execution may be slower because process startup overhead can dominate. It is most useful for long simulations, dense TLE files, or small sampling steps.

---

## Runtime reporting

The simulator reports timing information, including:

```text
Orbit sampling runtime
Orbit sampling speed
Total simulator runtime
```

This is useful for comparing serial and parallel performance.

Example logs:

```text
2026-06-10 16:20:11 | INFO | sat_sim | Orbit sampling runtime: 2.841 s
2026-06-10 16:20:11 | INFO | sat_sim | Orbit sampling speed: 12,534.7 samples/s
2026-06-10 16:20:12 | INFO | sat_sim | Total simulator runtime: 4.192 s
```

---

## Data model

The simulator uses a hierarchical internal representation:

```text
Satellite
└── SatellitePass
    └── OneSatelliteOrbit
        ├── OrbitSample
        ├── OrbitSample
        ├── OrbitSample
        └── ...
```

### `Satellite`

Stores satellite metadata and TLE age.

### `SatellitePass`

Stores one visible pass over the ground station.

### `OrbitSample`

Stores one sampled timestamp within a pass:

* timestamp
* azimuth
* elevation
* range
* range-rate
* Doppler shift
* TLE age

### `OneSatelliteOrbit`

Groups one `SatellitePass` with its associated list of `OrbitSample`s.

---

## Notes

* TLE age is calculated as:

```text
simulation_start_time - tle_epoch
```

* Positive TLE age means the TLE is older than the simulation start.
* Negative TLE age means the TLE epoch is after the simulation start.
* Times in output CSVs are UTC.
* The automatic output folder uses the local simulation start time from `--tz`.
* Doppler calculations use the configured RF center frequency.

---

## Typical workflow

1. Prepare a TLE file.
2. Run the simulator for the desired time window.
3. Inspect `passes.csv` to see which satellites were visible.
4. Inspect `orbit_samples.csv` for Doppler and geometry values.
5. Use Doppler plots to compare predicted curves with real spectrum/IQ observations.
6. Use the polar plot to understand where satellites were in the sky.
7. Use debug satellite mode to isolate specific candidates.

---

## Example full command

```bash
python main.py --start-time "16-07-2025 16:00:00" --duration 1800 --tz America/Chicago --tle-file ".\starlink.tle" --center-freq 11575000000 --min-elevation 16 --max-elevation 65 --station-label eng --output-dir outputs --overwrite --log-level INFO
```

This creates a run directory similar to:

```text
outputs/2025-07-16_16-00-00_duration_30m_eng/
```

with CSV outputs and plots.
# Satellite Doppler Pass Simulator

A modular Python simulator for predicting satellite visibility, sky tracks, and Doppler shifts over a ground station.

The simulator takes a TLE file, a time window, a ground-station location, and RF center frequency, then:

1. Loads satellites from TLE.
2. Finds satellites visible in the simulation window.
3. Samples each visible satellite pass.
4. Computes azimuth, elevation, range, range-rate, and Doppler shift.
5. Saves CSV outputs.
6. Generates Doppler and sky-track plots.

This code is designed for satellite signal attribution experiments, Doppler-based identification, and later IQ/spectrum compensation workflows.

---

## Project structure

```text
simulator/
├── main.py
├── sat_sim/
│   ├── __init__.py
│   ├── args.py
│   ├── config.py
│   ├── constants.py
│   ├── fov_sats.py
│   ├── logging_utils.py
│   ├── models.py
│   ├── orbit.py
│   ├── outputs.py
│   ├── plotting.py
│   ├── station.py
│   └── tle.py
└── README.md
```

### Main modules

| File               | Purpose                                             |
| ------------------ | --------------------------------------------------- |
| `main.py`          | Top-level simulator pipeline                        |
| `args.py`          | Command-line parsing and config construction        |
| `config.py`        | Simulation configuration dataclasses                |
| `models.py`        | Core dataclasses: satellites, passes, orbit samples |
| `tle.py`           | TLE loading and optional debug satellite filtering  |
| `fov_sats.py`      | Finds visible satellite passes                      |
| `orbit.py`         | Samples orbit geometry and Doppler                  |
| `outputs.py`       | Saves CSV outputs                                   |
| `plotting.py`      | Generates Doppler and polar sky-track plots         |
| `station.py`       | Builds ground-station object                        |
| `logging_utils.py` | Logger setup                                        |
| `constants.py`     | Shared constants such as CSV headers                |

---

## Installation

Create an environment and install dependencies:

```bash
pip install numpy pandas matplotlib scipy skyfield
```

If using parallel execution, no extra dependency is needed because the simulator uses Python’s standard multiprocessing tools.

---

## Basic usage

Run a simulation with a local TLE file:

```bash
python main.py --start-time "16-07-2025 16:00:00" --duration 1800 --tz America/Chicago --tle-file ".\starlink.tle" --station-label eng --overwrite
```

This simulates a 30-minute window starting at local time `2025-07-16 16:00:00` in the `America/Chicago` timezone.

---

## Example commands

### Run with default settings

```bash
python main.py
```

### Run a 30-minute simulation

```bash
python main.py --start-time "16-07-2025 16:00:00" --duration 1800 --tz America/Chicago --tle-file ".\starlink.tle" --station-label eng --overwrite
```

### Run a 10-hour simulation

```bash
python main.py --start-time "16-07-2025 16:00:00" --duration 36000 --tz America/Chicago --tle-file ".\starlink.tle" --station-label eng --overwrite
```

### Use dish elevation limits

```bash
python main.py --start-time "16-07-2025 16:00:00" --duration 36000 --tz America/Chicago --tle-file ".\starlink.tle" --min-elevation 16 --max-elevation 65 --station-label eng --overwrite
```

### Use a different RF center frequency

```bash
python main.py --start-time "16-07-2025 16:00:00" --duration 1800 --tz America/Chicago --tle-file ".\starlink.tle" --center-freq 11575000000 --station-label eng --overwrite
```

### Run in parallel

```bash
python main.py --start-time "16-07-2025 16:00:00" --duration 36000 --tz America/Chicago --tle-file ".\starlink.tle" --parallel --workers 8 --station-label eng --overwrite
```

---

## Command-line options

| Argument                 | Description                                                                                  |
| ------------------------ | -------------------------------------------------------------------------------------------- |
| `--start-time`           | Simulation start time. Supports `"now"`, `"DD-MM-YYYY HH:MM:SS"`, or `"YYYY-MM-DD HH:MM:SS"` |
| `--end-time`             | Simulation end time                                                                          |
| `--duration`             | Simulation duration in seconds                                                               |
| `--tz`                   | Timezone, for example `UTC` or `America/Chicago`                                             |
| `--lat`                  | Ground-station latitude in degrees                                                           |
| `--lon`                  | Ground-station longitude in degrees                                                          |
| `--alt`                  | Ground-station altitude in meters                                                            |
| `--station-label`        | Optional human-readable ground-station label                                                 |
| `--center-freq`          | RF center frequency in Hz                                                                    |
| `--tle-file`             | Path to local TLE file                                                                       |
| `--step-s`               | Orbit sampling step in seconds                                                               |
| `--min-elevation`        | Minimum elevation angle in degrees                                                           |
| `--max-elevation`        | Optional maximum elevation angle in degrees                                                  |
| `--parallel`             | Enable parallel orbit sampling                                                               |
| `--workers`              | Number of parallel workers                                                                   |
| `--output-dir`           | Base output directory                                                                        |
| `--overwrite`            | Allow overwriting existing output files                                                      |
| `--log-level`            | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR`                                           |
| `--log-file`             | Optional path to save logs                                                                   |
| `--debug-sat-names-file` | Optional text file containing satellite names to simulate                                    |

---

## Output directory format

The simulator automatically creates a run-specific output directory using:

```text
{start_time}_duration_{duration}_{station_label}
```

For example:

```text
outputs/2025-07-16_16-00-00_duration_30m_eng/
```

If no station label is provided, the station label is omitted:

```text
outputs/2025-07-16_16-00-00_duration_30m/
```

---

## Output files

A typical run produces:

```text
outputs/2025-07-16_16-00-00_duration_30m_eng/
├── passes.csv
├── orbit_samples.csv
└── plots/
    ├── all_doppler_curves.png
    ├── all_doppler_curves_by_recording_duration.png
    └── all_sky_tracks_polar.png
```

### `passes.csv`

One row per visible satellite pass.

Typical columns include:

| Column             | Description                                    |
| ------------------ | ---------------------------------------------- |
| `Satellite`        | Satellite name from TLE                        |
| `Norad ID`         | NORAD catalog ID                               |
| `Generation`       | Optional generation label                      |
| `Pass ID`          | Pass index for that satellite                  |
| `Rise Time (UTC)`  | Rise time within simulation window, if present |
| `Peak Time (UTC)`  | Peak time within simulation window, if present |
| `Set Time (UTC)`   | Set time within simulation window, if present  |
| `Start Time (UTC)` | Clipped start time used for sampling           |
| `End Time (UTC)`   | Clipped end time used for sampling             |
| `Duration (s)`     | Pass duration in seconds                       |
| `TLE Epoch (UTC)`  | TLE epoch timestamp                            |
| `TLE Age (days)`   | TLE age at simulation start                    |
| `TLE Age (hours)`  | TLE age at simulation start                    |

### `orbit_samples.csv`

One row per sampled time point.

Typical columns include:

| Column               | Description                            |
| -------------------- | -------------------------------------- |
| `Satellite`          | Satellite name                         |
| `Norad ID`           | NORAD catalog ID                       |
| `Pass ID`            | Pass index                             |
| `Generation`         | Optional generation label              |
| `Timestamp (UTC)`    | Sample timestamp                       |
| `Doppler Shift (Hz)` | Predicted Doppler shift                |
| `Elevation`          | Elevation angle in degrees             |
| `Azimuth`            | Azimuth angle in degrees               |
| `Distance (km)`      | Range from ground station to satellite |
| `TLE Age (hours)`    | TLE age at simulation start            |

---

## Plots

### Doppler vs UTC time

```text
plots/all_doppler_curves.png
```

Plots Doppler shift against absolute UTC timestamp.

This is useful for comparing the simulated Doppler curves directly with a real recording timeline.

### Doppler vs recording duration

```text
plots/all_doppler_curves_by_recording_duration.png
```

Plots Doppler shift against elapsed seconds from the simulation or recording start.

This should look identical to the UTC-time Doppler plot, except the x-axis is in seconds rather than timestamps.

### Polar sky-track plot

```text
plots/all_sky_tracks_polar.png
```

Plots satellite sky tracks in azimuth/elevation coordinates.

The convention is:

```text
theta = azimuth
r = 90 - elevation
```

So:

```text
center = zenith, 90 degrees elevation
outer edge = horizon, 0 degrees elevation
```

---

## Doppler sign convention

The simulator uses:

```text
doppler = f0 * (-range_rate / c)
```

where:

| Quantity     | Meaning                                         |
| ------------ | ----------------------------------------------- |
| `f0`         | RF center frequency in Hz                       |
| `range_rate` | satellite range-rate relative to ground station |
| `c`          | speed of light                                  |

Sign convention:

```text
range_rate < 0  -> satellite approaching -> positive Doppler
range_rate > 0  -> satellite receding    -> negative Doppler
```

---

## Elevation filtering

The simulator applies elevation constraints in two places:

1. `fov_sats.py` finds candidate passes using the minimum elevation threshold.
2. `orbit.py` filters individual samples using both minimum and maximum elevation limits.

This allows hardware constraints such as:

```text
16 degrees <= elevation <= 65 degrees
```

The maximum elevation is applied during orbit sampling because Skyfield’s event finder naturally works with threshold crossings, not arbitrary min/max tracking windows.

---

## Debug satellite subset mode

For debugging, you can restrict simulation to a few satellites.

Create a text file:

```text
debug_sats.txt
```

Example:

```text
STARLINK-1011
STARLINK-1029
STARLINK-1035
```

Then run:

```bash
python main.py --start-time "16-07-2025 16:00:00" --duration 1800 --tz America/Chicago --tle-file ".\starlink.tle" --debug-sat-names-file ".\debug_sats.txt" --station-label eng --overwrite
```

Behavior:

* If a requested satellite is not found in the TLE, the simulator logs an error and continues.
* If a requested satellite is found in the TLE but is not visible in the simulation window, the simulator logs an error and continues.
* Only requested satellites are considered.

---

## Parallel execution

Parallel orbit sampling can be enabled with:

```bash
--parallel
```

Optionally specify worker count:

```bash
--workers 8
```

Example:

```bash
python main.py --start-time "16-07-2025 16:00:00" --duration 36000 --tz America/Chicago --tle-file ".\starlink.tle" --parallel --workers 8 --station-label eng --overwrite
```

Parallelization is performed over satellite passes:

```text
SatellitePass -> OneSatelliteOrbit
```

This means each visible pass is sampled independently.

For small simulations, parallel execution may be slower because process startup overhead can dominate. It is most useful for long simulations, dense TLE files, or small sampling steps.

---

## Runtime reporting

The simulator reports timing information, including:

```text
Orbit sampling runtime
Orbit sampling speed
Total simulator runtime
```

This is useful for comparing serial and parallel performance.

Example logs:

```text
2026-06-10 16:20:11 | INFO | sat_sim | Orbit sampling runtime: 2.841 s
2026-06-10 16:20:11 | INFO | sat_sim | Orbit sampling speed: 12,534.7 samples/s
2026-06-10 16:20:12 | INFO | sat_sim | Total simulator runtime: 4.192 s
```

---

## Data model

The simulator uses a hierarchical internal representation:

```text
Satellite
└── SatellitePass
    └── OneSatelliteOrbit
        ├── OrbitSample
        ├── OrbitSample
        ├── OrbitSample
        └── ...
```

### `Satellite`

Stores satellite metadata and TLE age.

### `SatellitePass`

Stores one visible pass over the ground station.

### `OrbitSample`

Stores one sampled timestamp within a pass:

* timestamp
* azimuth
* elevation
* range
* range-rate
* Doppler shift
* TLE age

### `OneSatelliteOrbit`

Groups one `SatellitePass` with its associated list of `OrbitSample`s.

---

## Notes

* TLE age is calculated as:

```text
simulation_start_time - tle_epoch
```

* Positive TLE age means the TLE is older than the simulation start.
* Negative TLE age means the TLE epoch is after the simulation start.
* Times in output CSVs are UTC.
* The automatic output folder uses the local simulation start time from `--tz`.
* Doppler calculations use the configured RF center frequency.

---

## Typical workflow

1. Prepare a TLE file.
2. Run the simulator for the desired time window.
3. Inspect `passes.csv` to see which satellites were visible.
4. Inspect `orbit_samples.csv` for Doppler and geometry values.
5. Use Doppler plots to compare predicted curves with real spectrum/IQ observations.
6. Use the polar plot to understand where satellites were in the sky.
7. Use debug satellite mode to isolate specific candidates.

---

## Example full command

```bash
python main.py --start-time "16-07-2025 16:00:00" --duration 1800 --tz America/Chicago --tle-file ".\starlink.tle" --center-freq 11575000000 --min-elevation 16 --max-elevation 65 --station-label eng --output-dir outputs --overwrite --log-level INFO
```

This creates a run directory similar to:

```text
outputs/2025-07-16_16-00-00_duration_30m_eng/
```

with CSV outputs and plots.
# Satellite Doppler Pass Simulator

A modular Python simulator for predicting satellite visibility, sky tracks, and Doppler shifts over a ground station.

The simulator takes a TLE file, a time window, a ground-station location, and RF center frequency, then:

1. Loads satellites from TLE.
2. Finds satellites visible in the simulation window.
3. Samples each visible satellite pass.
4. Computes azimuth, elevation, range, range-rate, and Doppler shift.
5. Saves CSV outputs.
6. Generates Doppler and sky-track plots.

This code is designed for satellite signal attribution experiments, Doppler-based identification, and later IQ/spectrum compensation workflows.

---

## Project structure

```text
simulator/
├── main.py
├── sat_sim/
│   ├── __init__.py
│   ├── args.py
│   ├── config.py
│   ├── constants.py
│   ├── fov_sats.py
│   ├── logging_utils.py
│   ├── models.py
│   ├── orbit.py
│   ├── outputs.py
│   ├── plotting.py
│   ├── station.py
│   └── tle.py
└── README.md
```

### Main modules

| File               | Purpose                                             |
| ------------------ | --------------------------------------------------- |
| `main.py`          | Top-level simulator pipeline                        |
| `args.py`          | Command-line parsing and config construction        |
| `config.py`        | Simulation configuration dataclasses                |
| `models.py`        | Core dataclasses: satellites, passes, orbit samples |
| `tle.py`           | TLE loading and optional debug satellite filtering  |
| `fov_sats.py`      | Finds visible satellite passes                      |
| `orbit.py`         | Samples orbit geometry and Doppler                  |
| `outputs.py`       | Saves CSV outputs                                   |
| `plotting.py`      | Generates Doppler and polar sky-track plots         |
| `station.py`       | Builds ground-station object                        |
| `logging_utils.py` | Logger setup                                        |
| `constants.py`     | Shared constants such as CSV headers                |

---

## Installation

Create an environment and install dependencies:

```bash
pip install numpy pandas matplotlib scipy skyfield
```

If using parallel execution, no extra dependency is needed because the simulator uses Python’s standard multiprocessing tools.

---

## Basic usage

Run a simulation with a local TLE file:

```bash
python main.py --start-time "16-07-2025 16:00:00" --duration 1800 --tz America/Chicago --tle-file ".\starlink.tle" --station-label eng --overwrite
```

This simulates a 30-minute window starting at local time `2025-07-16 16:00:00` in the `America/Chicago` timezone.

---

## Example commands

### Run with default settings

```bash
python main.py
```

### Run a 30-minute simulation

```bash
python main.py --start-time "16-07-2025 16:00:00" --duration 1800 --tz America/Chicago --tle-file ".\starlink.tle" --station-label eng --overwrite
```

### Run a 10-hour simulation

```bash
python main.py --start-time "16-07-2025 16:00:00" --duration 36000 --tz America/Chicago --tle-file ".\starlink.tle" --station-label eng --overwrite
```

### Use dish elevation limits

```bash
python main.py --start-time "16-07-2025 16:00:00" --duration 36000 --tz America/Chicago --tle-file ".\starlink.tle" --min-elevation 16 --max-elevation 65 --station-label eng --overwrite
```

### Use a different RF center frequency

```bash
python main.py --start-time "16-07-2025 16:00:00" --duration 1800 --tz America/Chicago --tle-file ".\starlink.tle" --center-freq 11575000000 --station-label eng --overwrite
```

### Run in parallel

```bash
python main.py --start-time "16-07-2025 16:00:00" --duration 36000 --tz America/Chicago --tle-file ".\starlink.tle" --parallel --workers 8 --station-label eng --overwrite
```

---

## Command-line options

| Argument                 | Description                                                                                  |
| ------------------------ | -------------------------------------------------------------------------------------------- |
| `--start-time`           | Simulation start time. Supports `"now"`, `"DD-MM-YYYY HH:MM:SS"`, or `"YYYY-MM-DD HH:MM:SS"` |
| `--end-time`             | Simulation end time                                                                          |
| `--duration`             | Simulation duration in seconds                                                               |
| `--tz`                   | Timezone, for example `UTC` or `America/Chicago`                                             |
| `--lat`                  | Ground-station latitude in degrees                                                           |
| `--lon`                  | Ground-station longitude in degrees                                                          |
| `--alt`                  | Ground-station altitude in meters                                                            |
| `--station-label`        | Optional human-readable ground-station label                                                 |
| `--center-freq`          | RF center frequency in Hz                                                                    |
| `--tle-file`             | Path to local TLE file                                                                       |
| `--step-s`               | Orbit sampling step in seconds                                                               |
| `--min-elevation`        | Minimum elevation angle in degrees                                                           |
| `--max-elevation`        | Optional maximum elevation angle in degrees                                                  |
| `--parallel`             | Enable parallel orbit sampling                                                               |
| `--workers`              | Number of parallel workers                                                                   |
| `--output-dir`           | Base output directory                                                                        |
| `--overwrite`            | Allow overwriting existing output files                                                      |
| `--log-level`            | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR`                                           |
| `--log-file`             | Optional path to save logs                                                                   |
| `--debug-sat-names-file` | Optional text file containing satellite names to simulate                                    |

---

## Output directory format

The simulator automatically creates a run-specific output directory using:

```text
{start_time}_duration_{duration}_{station_label}
```

For example:

```text
outputs/2025-07-16_16-00-00_duration_30m_eng/
```

If no station label is provided, the station label is omitted:

```text
outputs/2025-07-16_16-00-00_duration_30m/
```

---

## Output files

A typical run produces:

```text
outputs/2025-07-16_16-00-00_duration_30m_eng/
├── passes.csv
├── orbit_samples.csv
└── plots/
    ├── all_doppler_curves.png
    ├── all_doppler_curves_by_recording_duration.png
    └── all_sky_tracks_polar.png
```

### `passes.csv`

One row per visible satellite pass.

Typical columns include:

| Column             | Description                                    |
| ------------------ | ---------------------------------------------- |
| `Satellite`        | Satellite name from TLE                        |
| `Norad ID`         | NORAD catalog ID                               |
| `Generation`       | Optional generation label                      |
| `Pass ID`          | Pass index for that satellite                  |
| `Rise Time (UTC)`  | Rise time within simulation window, if present |
| `Peak Time (UTC)`  | Peak time within simulation window, if present |
| `Set Time (UTC)`   | Set time within simulation window, if present  |
| `Start Time (UTC)` | Clipped start time used for sampling           |
| `End Time (UTC)`   | Clipped end time used for sampling             |
| `Duration (s)`     | Pass duration in seconds                       |
| `TLE Epoch (UTC)`  | TLE epoch timestamp                            |
| `TLE Age (days)`   | TLE age at simulation start                    |
| `TLE Age (hours)`  | TLE age at simulation start                    |

### `orbit_samples.csv`

One row per sampled time point.

Typical columns include:

| Column               | Description                            |
| -------------------- | -------------------------------------- |
| `Satellite`          | Satellite name                         |
| `Norad ID`           | NORAD catalog ID                       |
| `Pass ID`            | Pass index                             |
| `Generation`         | Optional generation label              |
| `Timestamp (UTC)`    | Sample timestamp                       |
| `Doppler Shift (Hz)` | Predicted Doppler shift                |
| `Elevation`          | Elevation angle in degrees             |
| `Azimuth`            | Azimuth angle in degrees               |
| `Distance (km)`      | Range from ground station to satellite |
| `TLE Age (hours)`    | TLE age at simulation start            |

---

## Plots

### Doppler vs UTC time

```text
plots/all_doppler_curves.png
```

Plots Doppler shift against absolute UTC timestamp.

This is useful for comparing the simulated Doppler curves directly with a real recording timeline.

### Doppler vs recording duration

```text
plots/all_doppler_curves_by_recording_duration.png
```

Plots Doppler shift against elapsed seconds from the simulation or recording start.

This should look identical to the UTC-time Doppler plot, except the x-axis is in seconds rather than timestamps.

### Polar sky-track plot

```text
plots/all_sky_tracks_polar.png
```

Plots satellite sky tracks in azimuth/elevation coordinates.

The convention is:

```text
theta = azimuth
r = 90 - elevation
```

So:

```text
center = zenith, 90 degrees elevation
outer edge = horizon, 0 degrees elevation
```

---

## Doppler sign convention

The simulator uses:

```text
doppler = f0 * (-range_rate / c)
```

where:

| Quantity     | Meaning                                         |
| ------------ | ----------------------------------------------- |
| `f0`         | RF center frequency in Hz                       |
| `range_rate` | satellite range-rate relative to ground station |
| `c`          | speed of light                                  |

Sign convention:

```text
range_rate < 0  -> satellite approaching -> positive Doppler
range_rate > 0  -> satellite receding    -> negative Doppler
```

---

## Elevation filtering

The simulator applies elevation constraints in two places:

1. `fov_sats.py` finds candidate passes using the minimum elevation threshold.
2. `orbit.py` filters individual samples using both minimum and maximum elevation limits.

This allows hardware constraints such as:

```text
16 degrees <= elevation <= 65 degrees
```

The maximum elevation is applied during orbit sampling because Skyfield’s event finder naturally works with threshold crossings, not arbitrary min/max tracking windows.

---

## Debug satellite subset mode

For debugging, you can restrict simulation to a few satellites.

Create a text file:

```text
debug_sats.txt
```

Example:

```text
STARLINK-1011
STARLINK-1029
STARLINK-1035
```

Then run:

```bash
python main.py --start-time "16-07-2025 16:00:00" --duration 1800 --tz America/Chicago --tle-file ".\starlink.tle" --debug-sat-names-file ".\debug_sats.txt" --station-label eng --overwrite
```

Behavior:

* If a requested satellite is not found in the TLE, the simulator logs an error and continues.
* If a requested satellite is found in the TLE but is not visible in the simulation window, the simulator logs an error and continues.
* Only requested satellites are considered.

---

## Parallel execution

Parallel orbit sampling can be enabled with:

```bash
--parallel
```

Optionally specify worker count:

```bash
--workers 8
```

Example:

```bash
python main.py --start-time "16-07-2025 16:00:00" --duration 36000 --tz America/Chicago --tle-file ".\starlink.tle" --parallel --workers 8 --station-label eng --overwrite
```

Parallelization is performed over satellite passes:

```text
SatellitePass -> OneSatelliteOrbit
```

This means each visible pass is sampled independently.

For small simulations, parallel execution may be slower because process startup overhead can dominate. It is most useful for long simulations, dense TLE files, or small sampling steps.

---

## Runtime reporting

The simulator reports timing information, including:

```text
Orbit sampling runtime
Orbit sampling speed
Total simulator runtime
```

This is useful for comparing serial and parallel performance.

Example logs:

```text
2026-06-10 16:20:11 | INFO | sat_sim | Orbit sampling runtime: 2.841 s
2026-06-10 16:20:11 | INFO | sat_sim | Orbit sampling speed: 12,534.7 samples/s
2026-06-10 16:20:12 | INFO | sat_sim | Total simulator runtime: 4.192 s
```

---

## Data model

The simulator uses a hierarchical internal representation:

```text
Satellite
└── SatellitePass
    └── OneSatelliteOrbit
        ├── OrbitSample
        ├── OrbitSample
        ├── OrbitSample
        └── ...
```

### `Satellite`

Stores satellite metadata and TLE age.

### `SatellitePass`

Stores one visible pass over the ground station.

### `OrbitSample`

Stores one sampled timestamp within a pass:

* timestamp
* azimuth
* elevation
* range
* range-rate
* Doppler shift
* TLE age

### `OneSatelliteOrbit`

Groups one `SatellitePass` with its associated list of `OrbitSample`s.

---

## Notes

* TLE age is calculated as:

```text
simulation_start_time - tle_epoch
```

* Positive TLE age means the TLE is older than the simulation start.
* Negative TLE age means the TLE epoch is after the simulation start.
* Times in output CSVs are UTC.
* The automatic output folder uses the local simulation start time from `--tz`.
* Doppler calculations use the configured RF center frequency.

---

## Typical workflow

1. Prepare a TLE file.
2. Run the simulator for the desired time window.
3. Inspect `passes.csv` to see which satellites were visible.
4. Inspect `orbit_samples.csv` for Doppler and geometry values.
5. Use Doppler plots to compare predicted curves with real spectrum/IQ observations.
6. Use the polar plot to understand where satellites were in the sky.
7. Use debug satellite mode to isolate specific candidates.

---

## Example full command

```bash
python main.py --start-time "16-07-2025 16:00:00" --duration 1800 --tz America/Chicago --tle-file ".\starlink.tle" --center-freq 11575000000 --min-elevation 16 --max-elevation 65 --station-label eng --output-dir outputs --overwrite --log-level INFO
```

This creates a run directory similar to:

```text
outputs/2025-07-16_16-00-00_duration_30m_eng/
```

with CSV outputs and plots.
