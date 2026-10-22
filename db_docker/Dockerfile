# postgres:15-bookworm, pulled Sep. 29, 2026.
# There is no bookworm-based postgis/postgis:15 image (bullseye is EOL and its packages were archived),
# so PostGIS is installed on top of the official postgres image, same as postgis/postgis does.
FROM postgres:15-bookworm@sha256:539ceaaae49b3a7c8a04467cf00cc6788d8e3f1675df41860d86eebc4c40524f

ENV POSTGIS_MAJOR 3
# Pinned so a rebuild doesn't silently move to a newer PostGIS (e.g. 3.7 dropped postgis_tiger_geocoder).
# If the build fails because apt can't find this version, PGDG removed it from the main repo:
# pick a newer one deliberately (apt-cache madison postgresql-15-postgis-3) and test a restore with it.
ENV POSTGIS_VERSION 3.6.4+dfsg-2.pgdg12+1

RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates curl unzip \
      postgresql-$PG_MAJOR-postgis-$POSTGIS_MAJOR=$POSTGIS_VERSION \
      postgresql-$PG_MAJOR-postgis-$POSTGIS_MAJOR-scripts=$POSTGIS_VERSION &&\
    rm -rf /var/lib/apt/lists/* &&\
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" &&\
    unzip awscliv2.zip && ./aws/install && rm -rf aws awscliv2.zip && aws --version
# Taken from postgis/postgis:15-3.5 - creates the PostGIS extensions on a fresh DB
COPY initdb-postgis.sh /docker-entrypoint-initdb.d/10_postgis.sh
COPY restore_db.sh /docker-entrypoint-initdb.d/

# values suitable for docker-compose environment
ENV POSTGRES_PASSWORD anyway
ENV POSTGRES_USER anyway
ENV POSTGRES_DB anyway
# ENV DBRESTORE_AWS_BUCKET=dfc2-anyway-partial-db-dumps
ENV DBRESTORE_AWS_BUCKET=dfc-anyway-partial-db-dumps
