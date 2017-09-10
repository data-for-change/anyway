# -*- coding: utf-8 -*-
from __future__ import print_function
from .models import DiscussionMarker
from sqlalchemy.orm import load_only

def main():
    for marker in DiscussionMarker.query.options(load_only("id", "identifier")).all():
        print(marker.identifier)


if __name__ == "__main__":
    main()
