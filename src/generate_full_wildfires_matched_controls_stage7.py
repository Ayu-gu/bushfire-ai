import math
import os
import random
import re
from datetime import timedelta

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio

from dbfread import DBF
from pyproj import Transformer
from shapely.geometry import Point


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_PATH = (
    "data/full_wildfires_2000plus_stage6.csv"
)

OUTPUT_PATH = (
    "data/full_wildfires_matched_controls_stage7.csv"
)

FIRE_SHAPEFILE = (
    "/Users/ayubgurung/Downloads/"
    "fire_npwsfirehistory/"
    "NPWSFireHistory.shp"
)

VEGETATION_RASTER = (
    "/Users/ayubgurung/Downloads/"
    "SVTM_NSW_Extant_PCT_vC2_0_M2_2_108/"
    "SVTM_NSW_Extant_PCT_vC2_0_M2_2_5m.tif"
)

VEGETATION_DBF = (
    "/Users/ayubgurung/Downloads/"
    "SVTM_NSW_Extant_PCT_vC2_0_M2_2_108/"
    "SVTM_NSW_Extant_PCT_vC2_0_M2_2_5m.tif.vat.dbf"
)

ELEVATION_TILE_DIR = (
    "data/elevation_tiles_v07"
)


# ============================================================
# CONTROL GENERATION SETTINGS
# ============================================================

TARGET_CONTROLS = 9249

MIN_DISTANCE_KM = 20.0
MAX_DISTANCE_KM = 100.0

MAX_ELEVATION_DIFFERENCE_M = 300.0

# Candidate must not be inside or within this distance
# of a relevant mapped wildfire perimeter.
FIRE_BUFFER_M = 1000.0

# For fires with an exact date but unreliable/missing EndDate,
# treat ±7 days around StartDate as relevant.
FIRE_DATE_WINDOW_DAYS = 7

MAX_ATTEMPTS_PER_FIRE = 1000

RANDOM_SEED = 42

NO_PCT_LABEL = "NO_MAPPED_PCT"

CHECKPOINT_EVERY = 250


# ============================================================
# REPRODUCIBILITY
# ============================================================

random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)


# ============================================================
# HELPERS
# ============================================================

def safe_text(value, fallback="UNKNOWN_ATTRIBUTE"):
    if value is None:
        return fallback

    try:
        if pd.isna(value):
            return fallback
    except Exception:
        pass

    value = str(value).strip()

    if not value:
        return fallback

    return value


def haversine_km(
    lat1,
    lon1,
    lat2,
    lon2,
):
    earth_radius_km = 6371.0088

    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a),
    )

    return earth_radius_km * c


def random_location_nearby(
    latitude,
    longitude,
):
    distance_km = random.uniform(
        MIN_DISTANCE_KM,
        MAX_DISTANCE_KM,
    )

    bearing = random.uniform(
        0,
        2 * math.pi,
    )

    earth_radius_km = 6371.0088

    lat1 = math.radians(latitude)
    lon1 = math.radians(longitude)

    angular_distance = (
        distance_km
        / earth_radius_km
    )

    lat2 = math.asin(
        math.sin(lat1)
        * math.cos(angular_distance)
        +
        math.cos(lat1)
        * math.sin(angular_distance)
        * math.cos(bearing)
    )

    lon2 = lon1 + math.atan2(
        math.sin(bearing)
        * math.sin(angular_distance)
        * math.cos(lat1),

        math.cos(angular_distance)
        -
        math.sin(lat1)
        * math.sin(lat2),
    )

    return (
        math.degrees(lat2),
        math.degrees(lon2),
        distance_km,
    )


# ============================================================
# VEGETATION LOOKUP
# ============================================================

def load_vegetation_lookup():
    print(
        "\nLoading vegetation attribute table..."
    )

    table = DBF(
        VEGETATION_DBF,
        load=True,
        encoding="cp1252",
    )

    lookup = {}

    for record in table:
        raster_value = int(
            record["Value"]
        )

        lookup[raster_value] = {
            "pct_id":
                safe_text(record["PCTID"]),

            "pct_name":
                safe_text(record["PCTName"]),

            "vegetation_class":
                safe_text(record["vegClass"]),

            "vegetation_formation":
                safe_text(record["vegForm"]),
        }

    print(
        f"Vegetation lookup records: "
        f"{len(lookup):,}"
    )

    return lookup


# ============================================================
# VEGETATION SAMPLER
# ============================================================

class VegetationSampler:

    def __init__(
        self,
        raster_path,
        lookup,
    ):
        self.dataset = rasterio.open(
            raster_path
        )

        self.lookup = lookup

        self.transformer = (
            Transformer.from_crs(
                "EPSG:4326",
                self.dataset.crs,
                always_xy=True,
            )
        )

    def sample(
        self,
        latitude,
        longitude,
    ):
        x, y = self.transformer.transform(
            longitude,
            latitude,
        )

        bounds = self.dataset.bounds

        if not (
            bounds.left <= x <= bounds.right
            and
            bounds.bottom <= y <= bounds.top
        ):
            return None, "outside_vegetation_raster"

        sample = next(
            self.dataset.sample(
                [(x, y)],
                masked=True,
            )
        )[0]

        if getattr(
            sample,
            "mask",
            False,
        ):
            return {
                "pct_id":
                    NO_PCT_LABEL,

                "pct_name":
                    NO_PCT_LABEL,

                "vegetation_class":
                    NO_PCT_LABEL,

                "vegetation_formation":
                    NO_PCT_LABEL,
            }, "no_mapped_pct"

        raster_value = int(sample)

        vegetation = self.lookup.get(
            raster_value
        )

        if vegetation is None:
            return None, "unknown_vegetation_value"

        return vegetation, "mapped"

    def close(self):
        self.dataset.close()


# ============================================================
# ELEVATION TILE INDEX
# ============================================================

class ElevationSampler:

    def __init__(
        self,
        tile_directory,
    ):
        print(
            "\nIndexing local elevation tiles..."
        )

        self.tiles = []

        for filename in sorted(
            os.listdir(tile_directory)
        ):
            if not filename.lower().endswith(
                ".tif"
            ):
                continue

            path = os.path.join(
                tile_directory,
                filename,
            )

            try:
                with rasterio.open(path) as ds:
                    bounds = ds.bounds
                    crs = ds.crs

                    if crs is None:
                        continue

                    self.tiles.append(
                        {
                            "path": path,
                            "bounds": bounds,
                            "crs": crs,
                        }
                    )

            except Exception:
                continue

        if not self.tiles:
            raise RuntimeError(
                "No usable elevation tiles found."
            )

        self.cache = {}

        print(
            f"Indexed elevation tiles: "
            f"{len(self.tiles):,}"
        )

    def _find_tile(
        self,
        latitude,
        longitude,
    ):
        for tile in self.tiles:
            bounds = tile["bounds"]

            # Existing DEM tiles are expected to use
            # geographic coordinates.
            if (
                bounds.left
                <= longitude
                <= bounds.right
                and
                bounds.bottom
                <= latitude
                <= bounds.top
            ):
                return tile

        return None

    def sample(
        self,
        latitude,
        longitude,
    ):
        tile = self._find_tile(
            latitude,
            longitude,
        )

        if tile is None:
            return None

        path = tile["path"]

        if path not in self.cache:
            self.cache[path] = (
                rasterio.open(path)
            )

        dataset = self.cache[path]

        value = next(
            dataset.sample(
                [(longitude, latitude)],
                masked=True,
            )
        )[0]

        if getattr(
            value,
            "mask",
            False,
        ):
            return None

        value = float(value)

        if not math.isfinite(value):
            return None

        return value

    def close(self):
        for dataset in (
            self.cache.values()
        ):
            dataset.close()


# ============================================================
# FIRE SEASON PARSER
# ============================================================

def parse_fire_season(label):
    if pd.isna(label):
        return None

    text = str(label)

    # Examples:
    # 2019-20 Wildfire
    # 2020-21 Wildfire

    match = re.search(
        r"\b(19|20)(\d{2})-(\d{2})\b",
        text,
    )

    if not match:
        return None

    first_year = int(
        match.group(1)
        + match.group(2)
    )

    second_short = int(
        match.group(3)
    )

    century = (
        first_year // 100
    ) * 100

    second_year = (
        century
        + second_short
    )

    if second_year < first_year:
        second_year += 100

    # Australian fire-season approximation:
    # July → June.
    start = pd.Timestamp(
        year=first_year,
        month=7,
        day=1,
    )

    end = pd.Timestamp(
        year=second_year,
        month=6,
        day=30,
    )

    return start, end


# ============================================================
# LOAD FIRE POLYGONS
# ============================================================

def load_fire_polygons():
    print(
        "\nLoading NSW fire-history polygons..."
    )

    fires = gpd.read_file(
        FIRE_SHAPEFILE
    )

    print(
        f"Raw polygons: "
        f"{len(fires):,}"
    )

    fires["StartDate"] = (
        pd.to_datetime(
            fires["StartDate"],
            errors="coerce",
        )
    )

    fires["EndDate"] = (
        pd.to_datetime(
            fires["EndDate"],
            errors="coerce",
        )
    )

    # --------------------------------------------------------
    # Keep wildfire records only
    # --------------------------------------------------------

    wildfire_mask = (
        fires["Label"]
        .astype(str)
        .str.contains(
            "Wildfire",
            case=False,
            na=False,
        )
    )

    fires = (
        fires[
            wildfire_mask
        ]
        .copy()
        .reset_index(drop=True)
    )

    print(
        f"Wildfire polygons: "
        f"{len(fires):,}"
    )

    # --------------------------------------------------------
    # Repair invalid geometry where possible
    # --------------------------------------------------------

    invalid_before = int(
        (~fires.geometry.is_valid).sum()
    )

    print(
        f"Invalid wildfire geometries "
        f"before repair: "
        f"{invalid_before:,}"
    )

    if invalid_before:
        fires["geometry"] = (
            fires.geometry.make_valid()
        )

    unusable = (
        fires.geometry.isna()
        |
        fires.geometry.is_empty
    )

    unusable_count = int(
        unusable.sum()
    )

    if unusable_count:
        print(
            f"Dropping unusable geometries: "
            f"{unusable_count:,}"
        )

        fires = (
            fires[
                ~unusable
            ]
            .copy()
            .reset_index(drop=True)
        )

    invalid_after = int(
        (~fires.geometry.is_valid).sum()
    )

    if invalid_after:
        raise RuntimeError(
            f"{invalid_after:,} wildfire "
            "geometries remain invalid "
            "after repair."
        )

    # --------------------------------------------------------
    # Temporal evidence
    # --------------------------------------------------------

    season_ranges = (
        fires["Label"]
        .apply(parse_fire_season)
    )

    fires["season_start"] = [
        value[0]
        if value is not None
        else pd.NaT
        for value in season_ranges
    ]

    fires["season_end"] = [
        value[1]
        if value is not None
        else pd.NaT
        for value in season_ranges
    ]

    # --------------------------------------------------------
    # Project to Australian Albers
    #
    # EPSG:3577 gives metre-based distances across Australia.
    # --------------------------------------------------------

    fires = fires.to_crs(
        "EPSG:3577"
    )

    print(
        f"Working CRS: "
        f"{fires.crs}"
    )

    print(
        f"Usable wildfire polygons: "
        f"{len(fires):,}"
    )

    return fires


# ============================================================
# TEMPORAL FIRE FILTER
# ============================================================

def relevant_fire_indices(
    fires,
    target_date,
):
    target_date = pd.Timestamp(
        target_date
    )

    window_start = (
        target_date
        - timedelta(
            days=FIRE_DATE_WINDOW_DAYS
        )
    )

    window_end = (
        target_date
        + timedelta(
            days=FIRE_DATE_WINDOW_DAYS
        )
    )

    start = fires["StartDate"]
    end = fires["EndDate"]

    # --------------------------------------------------------
    # Exact-date evidence
    #
    # Case A:
    # valid StartDate + sensible EndDate
    #
    # Candidate date window overlaps fire duration.
    # --------------------------------------------------------

    sensible_duration = (
        start.notna()
        &
        end.notna()
        &
        (end >= start)
    )

    exact_duration_match = (
        sensible_duration
        &
        (start <= window_end)
        &
        (end >= window_start)
    )

    # --------------------------------------------------------
    # Case B:
    # StartDate exists but EndDate is missing/bad.
    #
    # Use ±7 days around StartDate.
    # --------------------------------------------------------

    start_only = (
        start.notna()
        &
        (
            end.isna()
            |
            (end < start)
        )
    )

    start_only_match = (
        start_only
        &
        (start >= window_start)
        &
        (start <= window_end)
    )

    # --------------------------------------------------------
    # Case C:
    # exact StartDate unavailable.
    #
    # Fall back to fire-season label.
    # --------------------------------------------------------

    season_match = (
        start.isna()
        &
        fires["season_start"].notna()
        &
        fires["season_end"].notna()
        &
        (
            fires["season_start"]
            <= target_date
        )
        &
        (
            fires["season_end"]
            >= target_date
        )
    )

    relevant = (
        exact_duration_match
        |
        start_only_match
        |
        season_match
    )

    return fires.index[
        relevant
    ]


# ============================================================
# FIRE-PERIMETER CHECK
# ============================================================

class FirePerimeterChecker:

    def __init__(
        self,
        fires,
    ):
        self.fires = fires

        self.point_transformer = (
            Transformer.from_crs(
                "EPSG:4326",
                "EPSG:3577",
                always_xy=True,
            )
        )

        # Cache temporal subsets by date.
        self.date_cache = {}

    def candidate_near_relevant_fire(
        self,
        latitude,
        longitude,
        target_date,
    ):
        date_key = str(
            pd.Timestamp(target_date).date()
        )

        if date_key not in self.date_cache:
            indices = relevant_fire_indices(
                self.fires,
                target_date,
            )

            subset = (
                self.fires.loc[
                    indices,
                    ["geometry"],
                ]
                .copy()
            )

            self.date_cache[
                date_key
            ] = subset

        relevant = self.date_cache[
            date_key
        ]

        if relevant.empty:
            return False

        x, y = (
            self.point_transformer.transform(
                longitude,
                latitude,
            )
        )

        point = Point(x, y)

        # Search only polygons whose bounding boxes
        # are close enough to the candidate.
        search_geometry = (
            point.buffer(
                FIRE_BUFFER_M
            )
        )

        possible_indices = list(
            relevant.sindex.query(
                search_geometry,
                predicate="intersects",
            )
        )

        if not possible_indices:
            return False

        possible = (
            relevant.iloc[
                possible_indices
            ]
        )

        # Exact metric-distance check.
        distances = (
            possible.geometry.distance(
                point
            )
        )

        return bool(
            (
                distances
                <= FIRE_BUFFER_M
            ).any()
        )


# ============================================================
# VEGETATION MATCH
# ============================================================

def vegetation_match_type(
    source_row,
    candidate_vegetation,
):
    source_class = safe_text(
        source_row.vegetation_class
    )

    source_formation = safe_text(
        source_row.vegetation_formation
    )

    candidate_class = safe_text(
        candidate_vegetation[
            "vegetation_class"
        ]
    )

    candidate_formation = safe_text(
        candidate_vegetation[
            "vegetation_formation"
        ]
    )

    # Explicit missing-PCT pairing.
    if (
        source_class == NO_PCT_LABEL
        and
        candidate_class == NO_PCT_LABEL
    ):
        return "NO_MAPPED_PCT"

    # Preferred match.
    if (
        source_class != NO_PCT_LABEL
        and
        candidate_class == source_class
    ):
        return "CLASS"

    # Controlled fallback.
    if (
        source_formation != NO_PCT_LABEL
        and
        candidate_formation
        == source_formation
    ):
        return "FORMATION"

    return "DIFFERENT"


# ============================================================
# SAVE CHECKPOINT
# ============================================================

def save_checkpoint(rows):
    if not rows:
        return

    checkpoint = pd.DataFrame(
        rows
    )

    checkpoint.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print(
        f"\nCheckpoint saved: "
        f"{len(checkpoint):,}/"
        f"{TARGET_CONTROLS:,}"
    )


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 68)
    print(
        "BUSHFIRE AI - MATCHED NON-FIRE CONTROLS STAGE 7"
    )
    print("=" * 68)

    # --------------------------------------------------------
    # Validate files
    # --------------------------------------------------------

    required_paths = [
        INPUT_PATH,
        FIRE_SHAPEFILE,
        VEGETATION_RASTER,
        VEGETATION_DBF,
        ELEVATION_TILE_DIR,
    ]

    for path in required_paths:
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Required path not found:\n"
                f"{path}"
            )

    # --------------------------------------------------------
    # Load Stage 6
    # --------------------------------------------------------

    fires_df = pd.read_csv(
        INPUT_PATH
    )

    fires_df["date"] = (
        pd.to_datetime(
            fires_df["date"],
            errors="raise",
        )
    )

    print(
        f"\nStage 6 observations: "
        f"{len(fires_df):,}"
    )

    print(
        f"Unique source IDs: "
        f"{fires_df['source_row_id'].nunique():,}"
    )

    print(
        f"Unique fire events: "
        f"{fires_df['event_id'].nunique():,}"
    )

    if len(fires_df) != TARGET_CONTROLS:
        raise ValueError(
            f"Expected {TARGET_CONTROLS:,} "
            f"Stage 6 observations, "
            f"found {len(fires_df):,}."
        )

    if (
        fires_df["source_row_id"]
        .duplicated()
        .any()
    ):
        raise ValueError(
            "Duplicate source_row_id "
            "detected."
        )

    required_columns = [
        "source_row_id",
        "event_id",
        "date",
        "latitude",
        "longitude",
        "elevation",
        "pct_id",
        "pct_name",
        "vegetation_class",
        "vegetation_formation",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in fires_df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing required Stage 6 "
            f"columns: {missing_columns}"
        )

    # --------------------------------------------------------
    # Load spatial datasets
    # --------------------------------------------------------

    vegetation_lookup = (
        load_vegetation_lookup()
    )

    vegetation_sampler = (
        VegetationSampler(
            VEGETATION_RASTER,
            vegetation_lookup,
        )
    )

    elevation_sampler = (
        ElevationSampler(
            ELEVATION_TILE_DIR
        )
    )

    wildfire_polygons = (
        load_fire_polygons()
    )

    fire_checker = (
        FirePerimeterChecker(
            wildfire_polygons
        )
    )

    # --------------------------------------------------------
    # Rejection counters
    # --------------------------------------------------------

    rejection_counts = {
        "outside_vegetation_raster": 0,
        "unknown_vegetation_value": 0,
        "vegetation_mismatch": 0,
        "missing_elevation": 0,
        "elevation_mismatch": 0,
        "fire_perimeter": 0,
    }

    match_counts = {
        "CLASS": 0,
        "FORMATION": 0,
        "DIFFERENT": 0,
        "NO_MAPPED_PCT": 0,
    }

    rows = []

    failed_sources = []

    total_attempts = 0

    print(
        "\nGenerating matched controls..."
    )

    # --------------------------------------------------------
    # Generate one control per Stage 6 observation
    # --------------------------------------------------------

    try:

        for source_number, source in enumerate(
            fires_df.itertuples(
                index=False
            ),
            start=1,
        ):

            accepted = False

            target_date = (
                pd.Timestamp(
                    source.date
                )
            )

            for attempt in range(
                1,
                MAX_ATTEMPTS_PER_FIRE + 1,
            ):
                total_attempts += 1

                (
                    candidate_lat,
                    candidate_lon,
                    generated_distance_km,
                ) = random_location_nearby(
                    source.latitude,
                    source.longitude,
                )

                # --------------------------------------------
                # 1. Vegetation
                # --------------------------------------------

                (
                    candidate_vegetation,
                    vegetation_status,
                ) = vegetation_sampler.sample(
                    candidate_lat,
                    candidate_lon,
                )

                if candidate_vegetation is None:
                    if (
                        vegetation_status
                        in rejection_counts
                    ):
                        rejection_counts[
                            vegetation_status
                        ] += 1

                    continue

                match_type = (
                    vegetation_match_type(
                        source,
                        candidate_vegetation,
                    )
                )

                if match_type is None:
                    rejection_counts[
                        "vegetation_mismatch"
                    ] += 1

                    continue

                # --------------------------------------------
                # 2. Elevation
                # --------------------------------------------

                candidate_elevation = (
                    elevation_sampler.sample(
                        candidate_lat,
                        candidate_lon,
                    )
                )

                if candidate_elevation is None:
                    rejection_counts[
                        "missing_elevation"
                    ] += 1

                    continue

                elevation_difference = abs(
                    candidate_elevation
                    - float(
                        source.elevation
                    )
                )

                if (
                    elevation_difference
                    >
                    MAX_ELEVATION_DIFFERENCE_M
                ):
                    rejection_counts[
                        "elevation_mismatch"
                    ] += 1

                    continue

                # --------------------------------------------
                # 3. Actual fire-perimeter exclusion
                # --------------------------------------------

                near_fire = (
                    fire_checker
                    .candidate_near_relevant_fire(
                        candidate_lat,
                        candidate_lon,
                        target_date,
                    )
                )

                if near_fire:
                    rejection_counts[
                        "fire_perimeter"
                    ] += 1

                    continue

                # --------------------------------------------
                # ACCEPT CONTROL
                # --------------------------------------------

                actual_distance_km = (
                    haversine_km(
                        source.latitude,
                        source.longitude,
                        candidate_lat,
                        candidate_lon,
                    )
                )

                control = {
                    "source_row_id":
                        source.source_row_id,

                    "event_id":
                        source.event_id,

                    "source_date":
                        target_date.strftime(
                            "%Y-%m-%d"
                        ),

                    "source_latitude":
                        source.latitude,

                    "source_longitude":
                        source.longitude,

                    "control_latitude":
                        candidate_lat,

                    "control_longitude":
                        candidate_lon,

                    "distance_from_source_km":
                        round(
                            actual_distance_km,
                            3,
                        ),

                    "source_elevation":
                        float(
                            source.elevation
                        ),

                    "control_elevation":
                        round(
                            candidate_elevation,
                            3,
                        ),

                    "elevation_difference_m":
                        round(
                            elevation_difference,
                            3,
                        ),

                    "source_pct_id":
                        source.pct_id,

                    "control_pct_id":
                        candidate_vegetation[
                            "pct_id"
                        ],

                    "source_pct_name":
                        source.pct_name,

                    "control_pct_name":
                        candidate_vegetation[
                            "pct_name"
                        ],

                    "source_vegetation_class":
                        source.vegetation_class,

                    "control_vegetation_class":
                        candidate_vegetation[
                            "vegetation_class"
                        ],

                    "source_vegetation_formation":
                        source.vegetation_formation,

                    "control_vegetation_formation":
                        candidate_vegetation[
                            "vegetation_formation"
                        ],

                    "vegetation_match_type":
                        match_type,

                    "generation_attempt":
                        attempt,

                    "fire":
                        0,

                    "negative_type":
                        "matched_spatial_control",
                }

                rows.append(
                    control
                )

                match_counts[
                    match_type
                ] += 1

                accepted = True

                break

            # ------------------------------------------------
            # Source failed all attempts
            # ------------------------------------------------

            if not accepted:
                failed_sources.append(
                    {
                        "source_row_id":
                            source.source_row_id,

                        "event_id":
                            source.event_id,

                        "date":
                            target_date.strftime(
                                "%Y-%m-%d"
                            ),

                        "latitude":
                            source.latitude,

                        "longitude":
                            source.longitude,

                        "vegetation_class":
                            source.vegetation_class,

                        "vegetation_formation":
                            source.vegetation_formation,

                        "elevation":
                            source.elevation,
                    }
                )

            # ------------------------------------------------
            # Progress
            # ------------------------------------------------

            if (
                source_number % 100 == 0
                or source_number
                == len(fires_df)
            ):
                print(
                    f"Processed "
                    f"{source_number:,}/"
                    f"{len(fires_df):,} | "
                    f"Accepted "
                    f"{len(rows):,} | "
                    f"Failed "
                    f"{len(failed_sources):,}"
                )

            # ------------------------------------------------
            # Checkpoint
            # ------------------------------------------------

            if (
                source_number
                % CHECKPOINT_EVERY
                == 0
            ):
                
                save_checkpoint(
                    rows
                )

                print(
                    "\n--- LIVE STAGE 7 DIAGNOSTICS ---"
                )
                
                print(
                    f"Sources processed: "
                    f"{source_number:,}"
                )

                print(
                    f"Controls accepted: "
                    f"{len(rows):,}"
                )

                print(
                    f"Sources failed: "
                    f"{len(failed_sources):,}"
                )

                print(
                    f"Total candidate attempts: "
                    f"{total_attempts:,}"
                )

                print(
                    "\nVegetation matches:"
                )

                for key, value in match_counts.items():
                    print(
                        f"  {key:<28} "
                        f"{value:,}"
                    )

                print(
                    "\nCandidate rejections:"
                )

                for key, value in rejection_counts.items():
                    print(
                        f"  {key:<28} "
                        f"{value:,}"
                    )

                print(
                    "--------------------------------\n"
                )

    finally:
        vegetation_sampler.close()
        elevation_sampler.close()

    # --------------------------------------------------------
    # Save current result
    # --------------------------------------------------------

    save_checkpoint(
        rows
    )

    # --------------------------------------------------------
    # Report
    # --------------------------------------------------------

    print("\n" + "=" * 68)
    print("STAGE 7 MATCHED CONTROL GENERATION FINISHED")
    print("=" * 68)

    print(
        f"\nSource observations:       "
        f"{len(fires_df):,}"
    )

    print(
        f"Controls accepted:         "
        f"{len(rows):,}"
    )

    print(
        f"Sources without control:   "
        f"{len(failed_sources):,}"
    )

    print(
        f"Total candidate attempts:  "
        f"{total_attempts:,}"
    )

    if rows:
        print(
            f"Average attempts/control:  "
            f"{total_attempts / len(rows):.2f}"
        )

    print(
        "\nVegetation matches:"
    )

    for key, value in (
        match_counts.items()
    ):
        print(
            f"  {key:<20} "
            f"{value:,}"
        )

    print(
        "\nCandidate rejections:"
    )

    for key, value in (
        rejection_counts.items()
    ):
        print(
            f"  {key:<28} "
            f"{value:,}"
        )

    # --------------------------------------------------------
    # Failed source report
    # --------------------------------------------------------

    if failed_sources:
        failed_path = (
            "data/"
            "full_wildfires_stage7_failed_sources.csv"
        )

        pd.DataFrame(
            failed_sources
        ).to_csv(
            failed_path,
            index=False,
        )

        print(
            f"\nFailed-source report: "
            f"{failed_path}"
        )

    # --------------------------------------------------------
    # Final integrity checks
    # --------------------------------------------------------

    if rows:
        output_df = pd.DataFrame(
            rows
        )

        duplicate_source_ids = int(
            output_df[
                "source_row_id"
            ]
            .duplicated()
            .sum()
        )

        print(
            f"\nDuplicate source pairings: "
            f"{duplicate_source_ids:,}"
        )

        if duplicate_source_ids:
            raise RuntimeError(
                "Duplicate source-control "
                "pairings detected."
            )

        print(
            "\nControl distance:"
        )

        print(
            output_df[
                "distance_from_source_km"
            ]
            .describe()
            .round(2)
            .to_string()
        )

        print(
            "\nElevation difference:"
        )

        print(
            output_df[
                "elevation_difference_m"
            ]
            .describe()
            .round(2)
            .to_string()
        )

    # --------------------------------------------------------
    # Completion state
    # --------------------------------------------------------

    if len(rows) == TARGET_CONTROLS:

        print("\n" + "=" * 68)
        print(
            "STAGE 7 COMPLETE - FULL 1:1 MATCH ACHIEVED"
        )
        print("=" * 68)

        print(
            f"\n9,249 positive observations"
        )

        print(
            f"9,249 matched spatial controls"
        )

        print(
            f"\nSaved to:\n{OUTPUT_PATH}"
        )

    else:

        print("\n" + "=" * 68)
        print(
            "STAGE 7 REQUIRES REVIEW"
        )
        print("=" * 68)

        print(
            "\nNot every source observation "
            "received a valid control."
        )

        print(
            "Do NOT proceed to Stage 8 yet."
        )

        print(
            "\nWe will inspect the failed "
            "sources and rejection statistics "
            "before changing any thresholds."
        )


if __name__ == "__main__":
    main()