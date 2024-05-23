import logging
from typing import Dict, List

from anyway.app_and_db import db
from anyway.models import RoadJunctionKM, RoadSegments


class SegmentJunctions:
    # {<road segment id>: [<non urban junction id, ...]}
    __segment_junctions: Dict[int, List[int]] = {}
    __singleton = None

    def __init__(self):
        if not self.__segment_junctions:
            self.__segment_junctions = self.__calc_fill_segment_junctions()

    @staticmethod
    def get_instance():
        if not SegmentJunctions.__singleton:
            SegmentJunctions.__singleton = SegmentJunctions()
        return SegmentJunctions.__singleton

    def get_segment_junctions(self, segment: int) -> List[int]:
        res = self.__segment_junctions.get(segment)
        if res is None:
            logging.warning(f"{segment}: no such segment in segment junctions data.")
        return res or []

    @staticmethod
    def __calc_fill_segment_junctions():
        tmp: List[RoadJunctionKM] = db.session.query(RoadJunctionKM).all()
        res = {}
        rkj = {}
        road_last_junction_km = {}
        for t in tmp:
            if t.road not in rkj:
                rkj[t.road] = {}
                road_last_junction_km[t.road] = -1
            if t.km not in rkj[t.road]:
                rkj[t.road][t.km] = []
            else:
                logging.debug(f"Two junctions in same location:road:{t.road},km:{t.km},1:"
                              f"{rkj[t.road][t.km]},2:{t.non_urban_intersection}.")
            rkj[t.road][t.km].append(t.non_urban_intersection)
            if road_last_junction_km[t.road] < t.km:
                road_last_junction_km[t.road] = t.km
        tmp: List[RoadSegments] = db.session.query(RoadSegments).all()
        segments = {t.segment_id: t for t in tmp}
        for seg_id, seg in segments.items():
            if seg.road not in rkj:
                logging.warning(f"No junctions in road {seg.road}.")
                continue
            junctions = []
            for km in rkj[seg.road].keys():
                if is_junction_km_in_segment(km, seg, road_last_junction_km.get(seg.road)):
                    junctions.extend(rkj[seg.road][km])
            res[seg_id] = junctions
        return res


def is_junction_km_in_segment(km: float, seg: RoadSegments, road_last_km: int) -> bool:
    a = seg.from_km <= km < seg.to_km
    b = km == road_last_km and seg.to_km == road_last_km
    return a or b
