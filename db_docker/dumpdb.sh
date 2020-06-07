#!/bin/bash

export TZ=Asia/Jerusalem

echo "
[default]
# Object Storage Region NL-AMS
host_base = s3.nl-ams.scw.cloud
host_bucket = %(bucket)s.s3.nl-ams.scw.cloud
bucket_location = nl-ams
use_https = True

# Login credentials
access_key = ${DBDUMP_S3_ACCESS}
secret_key = ${DBDUMP_S3_SECRET}
" > /etc/anyway-s3cfg

dumpdb() {
  PG_DUMP_ARGS="${1}"
  DUMP_FILE="${2}"
  TEMPDIR=`mktemp -d`
  pushd $TEMPDIR
    chown postgres:postgres .
    echo "Dumping into dump file: ${DUMP_FILE}"
    ! PGPASSWORD=$DBDUMP_PASSWORD pg_dump -h $DBDUMP_HOST -d $DBDUMP_DB -U $DBDUMP_USER $PG_DUMP_ARGS > "${DUMP_FILE}" && echo failed to pg_dump && return 1
    echo "Zipping down the dump file"
    ! gzip "${DUMP_FILE}" && echo failed to gzip && return 1
    if [ -e /etc/anyway-s3cfg ]; then
      echo "Uploading the dump file to a bucket"
      ! s3cmd -c /etc/anyway-s3cfg put "${DUMP_FILE}.gz" s3://anyway-db-dumps && echo failed to s3cmd && return 1
    else
      echo missing anyway-s3cfg file, copying dump to opt directory
      ! cp "${DUMP_FILE}.gz" /opt/ && echo failed to cp && return 1
    fi
  popd
  rm -rf "${TEMPDIR}"
}

dumpdb "" \
       "`date +%Y-%m-%d_%H-%M-%S`_${DBDUMP_S3_FILE_PREFIX}anyway.pgdump" &&\
dumpdb "-T users -T roles -T roles_users -T locationsubscribers -T report_preferences -T general_preferences -T report_problem" \
       "`date +%Y-%m-%d_%H-%M-%S`_${DBDUMP_S3_FILE_PREFIX}anyway_public.pgdump" &&\
echo Great Success && exit 0
echo Failed && exit 1
