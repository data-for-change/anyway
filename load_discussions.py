# -*- coding: utf-8 -*-
from __future__ import print_function
import argparse
from models import DiscussionMarker
import re
from database import db_session
import sys

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('identifiers', type=str, nargs='*',
                        help='Disqus identifiers to create markers for')
    args = parser.parse_args()

    identifiers = args.identifiers if args.identifiers else sys.stdin

    for identifier in identifiers:
        m = re.match('\((\d+\.\d+),\s*(\d+\.\d+)\)', identifier)
        if not m:
            print("Failed processing: " + identifier)
            continue
        (latitude, longitude) = m.group(1, 2)
        marker = DiscussionMarker.parse({
            'latitude': latitude,
            'longitude': longitude,
            'title': identifier,
            'identifier': identifier
        })
        try:
            db_session.add(marker)
            db_session.commit()
            print("Added:  " + identifier, end="")
        except:
            db_session.rollback()
            print("Failed: " + identifier, end="")


if __name__ == "__main__":
    main()
