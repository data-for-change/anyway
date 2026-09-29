#!/bin/bash

set -e

# this file is added as a workaround due to
# Bullseye's long-term support ended on 2026-08-31.
# it allows staying on Postgres 15 that is based on Bullseye, while still using PostGIS 3.7 that requires Bookworm.
# The official Postgres image's entrypoint script, /usr/local/bin/docker-entrypoint.sh, calls it. Nothing in our code calls it directly.

# Where it goes

# The Dockerfile copies it into the directory the entrypoint reads at startup:

# COPY initdb-postgis.sh /docker-entrypoint-initdb.d/10_postgis.sh
# COPY restore_db.sh /docker-entrypoint-initdb.d/

# When it runs

# It runs only when the container starts with an empty data directory, which means the first start on a new volume:

# The entrypoint sees that /var/lib/postgresql/data is empty and runs initdb.
# It starts a temporary Postgres server that listens only inside the container.
# It goes through /docker-entrypoint-initdb.d/ in alphabetical order. That's why the file is renamed to 10_postgis.sh: it runs before restore_db.sh, so the PostGIS extensions exist before the restore loads a dump.
# It stops the temporary server and starts the real one.

# If the volume already has data, like your anyway_db_data, this whole step is skipped. So the script never runs against an existing database.

# How it runs

# A .sh file that is not executable is sourced into the entrypoint's shell. The script uses the entrypoint's psql command variable, so sourcing is what it needs.
# An executable .sh file runs as a separate process, where that variable doesn't exist. That's the --dbname=template_postgis: command not found failure from earlier, and why the file must stay non-executable.
# You could see both behaviors in the test logs: "running …10_postgis.sh" before the fix and "sourcing …10_postgis.sh" after.

# What it does

# Creates a template_postgis template database.
# Enables postgis, postgis_topology, fuzzystrmatch and postgis_tiger_geocoder in both that template and $POSTGRES_DB (anyway).

# The old postgis/postgis base image included this same script at the same path. Now that we build on plain postgres:15-bookworm, we copy it in ourselves so a fresh database gets the same setup as before.


# Perform all actions as $POSTGRES_USER
export PGUSER="$POSTGRES_USER"

# Create the 'template_postgis' template db
"${psql[@]}" <<- 'EOSQL'
CREATE DATABASE template_postgis IS_TEMPLATE true;
EOSQL

# Load PostGIS into both template_database and $POSTGRES_DB
for DB in template_postgis "$POSTGRES_DB"; do
	echo "Loading PostGIS extensions into $DB"
	"${psql[@]}" --dbname="$DB" <<-'EOSQL'
		CREATE EXTENSION IF NOT EXISTS postgis;
		CREATE EXTENSION IF NOT EXISTS postgis_topology;
		-- Reconnect to update pg_setting.resetval
		-- See https://github.com/postgis/docker-postgis/issues/288
		\c
		--
		DO $$
		DECLARE
			postgis_major integer;
			postgis_minor integer;
		BEGIN
			SELECT substring(postgis_lib_version() from '^([0-9]+)')::integer,
				substring(postgis_lib_version() from '^[0-9]+\.([0-9]+)')::integer
			INTO postgis_major, postgis_minor;

			-- Install the legacy tiger geocoder stack only for PostGIS versions before 3.7.
			-- fuzzystrmatch is required by postgis_tiger_geocoder, which PostGIS 3.7 and later no longer provide.
			IF postgis_major < 3 OR (postgis_major = 3 AND postgis_minor < 7) THEN
				CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
				CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder;
			END IF;
		END
		$$;
EOSQL
done
