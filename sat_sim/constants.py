HEADER_SATELLITE_NAME = "Satellite"
HEADER_NORAD_ID = "NORAD ID"
HEADER_PASS_ID = "Pass ID"
HEADER_GENERATION = "Generation"
HEADER_TIMESTAMP_UTC = "Timestamp (UTC)"
HEADER_DOPPLER_SHIFT_HZ = "Doppler Shift (Hz)"
HEADER_ELEVATION_DEG = "Elevation (deg)"
HEADER_AZIMUTH_DEG = "Azimuth (deg)"
HEADER_DISTANCE_KM = "Distance (km)"
TLE_AGE_HOURS = "TLE Age (hours)"


    # satellite: Satellite

    # satellite_name: str
    # satellite_norad_id: int | None
    # generation: str | None
    # pass_idx: int

    # timestamp: Time
    # timestamp_utc: datetime

    # time_from_start_of_pass_s: float  # time from the start of the satellite pass in seconds (not simulation)

    # azimuth_deg: float
    # elevation_deg: float
    # # TODO: check
    # range_km: float
    # range_rate_km_s: float

    # doppler_shift_hz: float

    # tle_epoch_utc: datetime
    # tle_age_days: float
    # tle_age_hours: float

HEADERS = [
    HEADER_SATELLITE_NAME,
    HEADER_NORAD_ID,
    HEADER_PASS_ID,
    HEADER_GENERATION,
    HEADER_TIMESTAMP_UTC,
    HEADER_DOPPLER_SHIFT_HZ,
    HEADER_ELEVATION_DEG,
    HEADER_AZIMUTH_DEG,
    HEADER_DISTANCE_KM,
    TLE_AGE_HOURS]