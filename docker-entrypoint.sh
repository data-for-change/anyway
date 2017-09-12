#!/bin/bash
set -u

alembic upgrade head
python main.py process cbs
python main.py process united --light

exec "$@"
