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
        for t in tmp:
            if t.road not in rkj:
                rkj[t.road] = {}
            rkj[t.road][t.km] = t.non_urban_intersection
        tmp: List[RoadSegments] = db.session.query(RoadSegments).all()
        segments = {t.segment_id: t for t in tmp}
        for seg_id, seg in segments.items():
            if seg.road not in rkj:
                logging.warning(f"No junctions in road {seg.road}.")
                continue
            junctions = [
                rkj[seg.road][km] for km in rkj[seg.road].keys() if seg.from_km <= km < seg.to_km
            ]
            res[seg_id] = junctions
        return res
