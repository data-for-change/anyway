import datetime
import os
import pandas as pd
from tqdm import tqdm
from anyway.models import AccidentMarkerView, RoadSegments, SuburbanJunction
from anyway.widgets.segment_junctions import SegmentJunctions
from anyway.widgets.widget_utils import (
    get_expression_for_fields,
    get_expression_for_road_segment_location_fields,
    split_location_fields_and_others,
)
from anyway.app_and_db import db
from sqlalchemy import func

# Constants
CBS_TYPE_1_SUMMARY_FILE = os.path.join("static", "data", "cbs_summary_files", "2022", "t01_type_1_for_segment_test.xls")
CBS_TYPE_3_SUMMARY_FILE = os.path.join("static", "data", "cbs_summary_files", "2022", "t03_type_3_for_segment_test.xls")
OUTPUT_DIR = os.path.join("static", "data", "cbs_summary_files", "2022", "comparison_output")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "cbs_anyway_road_segments.csv")

# Global dictionary for road segments
ROAD_SEGMENTS_DICT = {}
sg = SegmentJunctions.get_instance()

def read_excel_file(file_path, skip_rows, columns, segment_col="segment"):
    try:
        df = pd.read_excel(file_path, skiprows=skip_rows)
        df.columns = columns
        df = df.loc[df[segment_col].notna() & df[segment_col].astype(str).str.isdigit()]
        return df
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return pd.DataFrame()


def get_cbs_count():
    df_type_1_columns = [
        "segment", "road", "from", "to", "acc_per_million_km", "total", "total_light",
        "total_severe", "total_fatal", "2022_total", "2022_light", "2022_severe", "2022_fatal",
        "2021_total", "2020_total", "avg", "length"
    ]
    df_type_3_columns = [
        "segment", "road", "from", "to", "acc_per_million_km", "total", "2022_total",
        "2021_total", "2020_total", "avg", "length"
    ]

    # Read and process type 1 data
    df_type_1 = read_excel_file(CBS_TYPE_1_SUMMARY_FILE, 4, df_type_1_columns)
    if df_type_1.empty:
        return pd.DataFrame()
    df_type_1["provider_code"] = 1
    df_type_1["road_segment_name_cbs"] = df_type_1["from"].str.slice(start=1) + " -" + df_type_1["to"].str.slice(start=2)
    df_type_1_total = df_type_1[["road_segment_name_cbs", "road", "segment", "provider_code", "2020_total", "2021_total", "2022_total"]].copy()
    df_type_1_total.columns = ["road_segment_name_cbs", "road", "segment", "provider_code", "2020_cbs", "2021_cbs", "2022_cbs"]
    df_type_1_total.fillna({"2020_cbs": 0, "2021_cbs": 0, "2022_cbs": 0}, inplace=True)

    # Read and process type 3 data
    df_type_3 = read_excel_file(CBS_TYPE_3_SUMMARY_FILE, 5, df_type_3_columns)
    if df_type_3.empty:
        return df_type_1_total
    df_type_3["provider_code"] = 3
    df_type_3["road_segment_name_cbs"] = df_type_3["from"].str.slice(start=1) + " - " + df_type_3["to"].str.slice(start=2)
    df_type_3_total = df_type_3[["road_segment_name_cbs", "road", "segment", "provider_code", "2020_total", "2021_total", "2022_total"]].copy()
    df_type_3_total.columns = ["road_segment_name_cbs", "road", "segment", "provider_code", "2020_cbs", "2021_cbs", "2022_cbs"]
    df_type_3_total.fillna({"2020_cbs": 0, "2021_cbs": 0, "2022_cbs": 0}, inplace=True)

    # Combine type 1 and type 3 data
    df_cbs_total = pd.concat([df_type_1_total, df_type_3_total])
    df_cbs_total.set_index(["road", "segment", "provider_code"], inplace=True)
    return df_cbs_total


def get_anyway_count():
    dfs = []
    road_segments = RoadSegments.query.all()
    for road_segment in tqdm(road_segments, desc="Processing road segments"):
        road_segment_id = road_segment.segment_id
        road = road_segment.road
        segment = road_segment.segment
        road_segment_name = f"{road_segment.from_name} - {road_segment.to_name}"
        ROAD_SEGMENTS_DICT[road_segment_id] = road_segment_name

        filters = {
            "road_segment_id": road_segment_id,
            "accident_year": [2020, 2021, 2022]
        }
        query = db.session.query(AccidentMarkerView)
        location_fields, other_fields = split_location_fields_and_others(filters)

        if other_fields:
            query = query.filter(get_expression_for_fields(other_fields, AccidentMarkerView))
        if location_fields:
            query = query.filter(get_expression_for_road_segment_location_fields(location_fields, AccidentMarkerView))
        query = query.filter(AccidentMarkerView.location_accuracy.in_([1,3,4,9]))
        query = query.group_by(AccidentMarkerView.provider_code, AccidentMarkerView.accident_year)
        query = query.with_entities(
            AccidentMarkerView.provider_code,
            AccidentMarkerView.accident_year,
            func.count().label("anyway_count"),
        )

        df = pd.read_sql_query(query.statement, query.session.bind)
        df["road_segment_id"] = road_segment_id
        df["road"] = road
        df["segment"] = segment
        df["road_segment_name"] = road_segment_name
        junctions_numbers = list(sg.get_segment_junctions(road_segment_id))

        if not junctions_numbers:
            junctions_numbers = []
        df["junctions_ids_in_segment"] = str(junctions_numbers)

        junctions_objects = db.session.query(SuburbanJunction.non_urban_intersection,
                                SuburbanJunction.non_urban_intersection_hebrew).filter(
            SuburbanJunction.non_urban_intersection.in_(junctions_numbers)
        ).all()
        df["junctions_names_in_segment"] = str([j.non_urban_intersection_hebrew for j in junctions_objects])
        dfs.append(df)

    df_all_segments = pd.concat(dfs)
    df_all_segments.sort_values(["road_segment_id", "provider_code", "accident_year"], inplace=True)
    return df_all_segments


def parse():
    df_anyway = get_anyway_count()
    df_anyway_total = df_anyway.groupby([ "junctions_ids_in_segment", "junctions_names_in_segment", "road", "segment", "provider_code", "road_segment_id", "accident_year"])["anyway_count"].sum().unstack(fill_value=0).reset_index()
    df_anyway_total.set_index(["road", "segment", "provider_code"], inplace=True)

    df_cbs_total = get_cbs_count()
    if df_cbs_total.empty:
        return

    df_total = pd.merge(df_cbs_total, df_anyway_total, left_index=True, right_index=True, how="outer")
    df_total.reset_index(inplace=True)
    df_total["road_segment_name"] = df_total["road_segment_id"].map(ROAD_SEGMENTS_DICT)
    df_total.rename(columns={2020: "2020_anyway", 2021: "2021_anyway", 2022: "2022_anyway"}, inplace=True)
    df_total = df_total[[
        "road_segment_name_cbs", "road_segment_name", "road_segment_id", "road", "segment", "provider_code",
        "2020_cbs", "2020_anyway", "2021_cbs", "2021_anyway", "2022_cbs", "2022_anyway", "junctions_ids_in_segment", "junctions_names_in_segment"
    ]]
    df_total["road_segment_name_cbs"] = df_total["road_segment_name_cbs"].str.strip()
    df_total["road_segment_name_cbs"] = df_total["road_segment_name_cbs"].replace(r'\s+', ' ', regex=True)
    df_total["road_names_matches"] = df_total["road_segment_name_cbs"] == df_total["road_segment_name"]
    df_total["2020_match"] = df_total["2020_cbs"] == df_total["2020_anyway"]
    df_total["2021_match"] = df_total["2021_cbs"] == df_total["2021_anyway"]
    df_total["2022_match"] = df_total["2022_cbs"] == df_total["2022_anyway"]
    df_total["all_match"] = df_total[["2020_match", "2021_match", "2022_match"]].all(axis=1)
    df_total["diff_anyway_cbs"] = df_total[["2020_anyway", "2021_anyway", "2022_anyway"]].sum(axis=1) - df_total[["2020_cbs", "2021_cbs", "2022_cbs"]].sum(axis=1)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    df_total.to_csv(OUTPUT_FILE, index=False)
    print(f"Output saved to {OUTPUT_FILE}")
