# -*- coding: utf-8 -*-
from __future__ import print_function
import argparse
from models import DiscussionMarker
import re
from datetime import datetime
from database import db_session

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('identifiers', type=str, nargs='+',
                        help='Disqus identifiers to create markers for')
    args = parser.parse_args()

    for identifier in args.identifiers:
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
        db_session.add(marker)
        db_session.commit()
        print("Added: " + identifier)


if __name__ == "__main__":
    main()
