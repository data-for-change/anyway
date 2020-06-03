FROM postgis/postgis:9.6-2.5-alpine

RUN apk add --update-cache python3 sudo &&\
    pip3 install gdown

ARG GDRIVE_FILE_ID=''
ARG RESTORE_DB='FALSE'
ARG GDRIVE_URL='https://drive.google.com/uc?id='
ARG DB_DUMP_PATH=/tmp/anyway_public.pgdump

ADD ./download_dump.py /

RUN if [ -n "${GDRIVE_FILE_ID}" -a "${RESTORE_DB}" == "TRUE" ]; then python3 download_dump.py; else echo "No file ID provided or RESTORE_DB!=TRUE, not downloading dump" ; fi

ENV GDRIVE_URL=$GDRIVE_URL
ENV GDRIVE_FILE_ID=$GDRIVE_FILE_ID
ENV RESTORE_DB=$RESTORE_DB
ENV DB_DUMP_PATH=$DB_DUMP_PATH

ADD ./restore_db.sh /docker-entrypoint-initdb.d/
