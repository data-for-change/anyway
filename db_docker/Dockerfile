FROM postgis/postgis:9.6-2.5-alpine

RUN apk add --update-cache python3 sudo &&\
    pip3 install gdown

ARG GDRIVE_FILE_ID=''
ARG RESTORE_DB='FALSE'
ARG GDRIVE_URL='https://drive.google.com/uc?id='
ARG DB_DUMP_PATH=/tmp/anyway_public.pgdump

ENV GDRIVE_FILE_ID=$GDRIVE_FILE_ID
ENV RESTORE_DB=$RESTORE_DB

ADD ./download_dump.py /

RUN if [ "$RESTORE_DB" == "TRUE" ] ; then python3 download_dump.py && chmod +rwx $DB_DUMP_PATH; else echo "RESTORE_DB!=TRUE, not downloading dump" ; fi

ADD ./restore_db.sh /docker-entrypoint-initdb.d/
