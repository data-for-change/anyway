# -*- coding: utf-8 -*-
from __future__ import print_function

from sqlalchemy.orm import load_only

from .models import DiscussionMarker


def main():
    for marker in DiscussionMarker.query.options(load_only("id", "identifier")).all():
        print(marker.identifier)


if __name__ == "__main__":
    main()
