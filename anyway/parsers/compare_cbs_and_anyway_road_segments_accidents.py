from anyway.models import AccidentMarkerView
from anyway.widgets.widget_utils import get_expression_for_fields, get_expression_for_road_segment_location_fields, split_location_fields_and_others
from anyway.models import AccidentMarkerView, RoadSegments
from anyway.app_and_db import db
from sqlalchemy import func, and_
import pandas as pd
from tqdm import tqdm

CBS_TYPE_1_SUMMARY_FILE = "static/data/cbs_summary_files/t01_type_1_for_segment_test.xls"
CBS_TYPE_3_SUMMARY_FILE = "static/data/cbs_summary_files/t03_type_3_for_segment_test.xls"
ROAD_SEGMENTS_DICT = {}


def get_cbs_count():
    df_type_1 = pd.read_excel(CBS_TYPE_1_SUMMARY_FILE, skiprows=4)
    df_type_1.columns = ["segment", "road", "from", "to", "acc_per_milion_km", "total", "total_light", "total_severe", "total_fatal", "2022_total", "2022_light", "2022_severe", "2022_fatal", "2021_total", "2020_total", "avg", "length"]
    df_type_1 = df_type_1.loc[df_type_1.segment.notna()]
    df_type_1 = df_type_1.loc[df_type_1.segment.astype(str).str.isdigit()]
    df_type_1["provider_code"] = 1
    df_type_1["road_segment_name_cbs"] = df_type_1["from"] + "_" + df_type_1["to"]
    df_type_1_total = df_type_1[["road_segment_name_cbs", "road" , "segment","provider_code", "2020_total","2021_total", "2022_total"]].copy()
    df_type_1_total.columns = ["road_segment_name_cbs",  "road" , "segment", "provider_code",  "2020_cbs", "2021_cbs", "2022_cbs"]
    df_type_1_total[["2020_cbs", "2021_cbs", "2022_cbs"]] = df_type_1_total[["2020_cbs", "2021_cbs", "2022_cbs"]].fillna(0)

    df_type_1_2022 = df_type_1[["road_segment_name_cbs", "road" , "segment", "provider_code", "2022_light", "2022_severe", "2022_fatal"]]


    df_type_3 = pd.read_excel(CBS_TYPE_3_SUMMARY_FILE, skiprows=5)
    df_type_3.columns = ["segment", "road", "from", "to", "acc_per_milion_km", "total", "2022_total", "2021_total", "2020_total", "avg", "length"]
    df_type_3 = df_type_3.loc[df_type_3.segment.notna()]
    df_type_3 = df_type_3.loc[df_type_3.segment.astype(str).str.isdigit()]
    df_type_3["provider_code"] = 3
    df_type_3["road_segment_name_cbs"] = df_type_3["from"] + "_" + df_type_3["to"]
    df_type_3_total = df_type_3[["road_segment_name_cbs", "road" , "segment", "provider_code", "2020_total","2021_total", "2022_total"]].copy()
    df_type_3_total.columns = ["road_segment_name_cbs", "road" , "segment", "provider_code", "2020_cbs", "2021_cbs", "2022_cbs"]
    df_type_3_total[["2020_cbs", "2021_cbs", "2022_cbs"]] = df_type_3_total[["2020_cbs", "2021_cbs", "2022_cbs"]].fillna(0)

    df_cbs_total = pd.concat([df_type_1_total, df_type_3_total])
    df_cbs_total.set_index(["road" , "segment", "provider_code"], inplace=True)
    return df_cbs_total, df_type_1_2022

def get_anyway_count():
    dfs = []
    for road_segment in tqdm(RoadSegments.query.all()):
        road_segment_id = road_segment.segment_id
        if road_segment_id != 97790010:
            continue
        road = road_segment.road
        segment = road_segment.segment
        road_segment_name = road_segment.from_name + ' - ' + road_segment.to_name
        print(road_segment_name)
        ROAD_SEGMENTS_DICT[road_segment_id] = road_segment_name
        filters={"road_segment_id": road_segment_id,
                "accident_year": [2019, 2020,2021,2022, 2023]}
        query = db.session.query(AccidentMarkerView)
        location_fields, other_fields = split_location_fields_and_others(filters)
        if other_fields:
            query = query.filter(get_expression_for_fields(other_fields, AccidentMarkerView, and_))
        query = query.filter(
            get_expression_for_road_segment_location_fields(location_fields, AccidentMarkerView)
        )
        test_query = query
        test_query = test_query.group_by(AccidentMarkerView.location_accuracy_hebrew)
        test_query = test_query.group_by(AccidentMarkerView.location_accuracy_hebrew, AccidentMarkerView.provider_code, AccidentMarkerView.accident_year)
        test_query = test_query.with_entities(
            AccidentMarkerView.provider_code,
            AccidentMarkerView.location_accuracy_hebrew,
            AccidentMarkerView.accident_year,
            func.count(AccidentMarkerView.location_accuracy_hebrew))
        
        df2 = pd.read_sql_query(test_query.statement, test_query.session.bind)
        print(df2)
        query = query.group_by(AccidentMarkerView.provider_code,
                            AccidentMarkerView.accident_severity,
                            AccidentMarkerView.accident_year)

        query = query.with_entities(
            AccidentMarkerView.provider_code,
            AccidentMarkerView.accident_severity,
            AccidentMarkerView.accident_year,
            func.count(AccidentMarkerView.accident_severity),
        )

 

        df = pd.read_sql_query(query.statement, query.session.bind)
        df.rename(columns={"count_1": "anyway_count"}, inplace=True)  # pylint: disable=no-member
        df["road_segment_id"] = road_segment_id
        df["road"] = road
        df["segment"] = segment
        df["road_segment_name"] = road_segment_name
        dfs.append(df)

    df_alls_segments = pd.concat(dfs)
    df_alls_segments.sort_values(['road_segment_id', 'provider_code', 'accident_year'], inplace=True)
    return df_alls_segments


def parse():
    df_anyway = get_anyway_count()
    df_anyway["road_segment_id"] = df_anyway["road_segment_id"].astype(int)
    df_anyway_total = df_anyway.groupby(["road", "segment" ,"provider_code", "road_segment_id", "accident_year"])["anyway_count"].sum()
    df_anyway_total = df_anyway_total.unstack(-1)
    df_anyway_total.fillna(0, inplace=True)
    df_cbs_total, df_type_1_2022 = get_cbs_count()
    df_anyway_total.reset_index(inplace=True)
    df_anyway_total.set_index(["road" , "segment", "provider_code"], inplace=True)
    df_total = pd.merge(df_cbs_total, df_anyway_total, left_index=True, right_index=True, how="outer")
    df_total.reset_index(inplace=True)
    df_total["road_segment_name"] = df_total.road_segment_id.apply(lambda s: ROAD_SEGMENTS_DICT.get(s))
    df_total = df_total.rename(columns = {2020: "2020_anyway", 2021: "2021_anyway", 2022: "2022_anyway"})
    df_total = df_total[["road_segment_name_cbs", "road_segment_name", "road_segment_id", "road", "segment",  "provider_code", "2020_cbs", "2020_anyway", "2021_cbs",  "2021_anyway", "2022_cbs",  "2022_anyway"]]
    df_total["2020_mismatch"] = df_total["2020_cbs"] != df_total["2020_anyway"]
    df_total["2021_mismatch"] = df_total["2021_cbs"] != df_total["2021_anyway"]
    df_total["2022_mismatch"] = df_total["2022_cbs"] != df_total["2022_anyway"]
    df_total["any_mismatch"] = df_total[["2020_mismatch",
                                         "2021_mismatch",
                                         "2022_mismatch"]].any(axis=1)
    df_total.to_csv("cbs_anyway_road_segments.csv", index=False)