FROM postgis/postgis:9.6-2.5-alpine

RUN apk add --update-cache python3 sudo &&\
    pip3 install gdown

ARG GDRIVE_FILE_ID=''
ARG CURR_ENV='TEST'
ARG GDRIVE_URL='https://drive.google.com/uc?id='
ARG DB_DUMP_DIR=/docker-entrypoint-initdb.d
ARG DB_DUMP_PATH=/docker-entrypoint-initdb.d/anyway_public.pgdump

ENV GDRIVE_FILE_ID=$GDRIVE_FILE_ID
ENV CURR_ENV=$CURR_ENV

ADD ./download_dump.py /

RUN if [ "$CURR_ENV" == "DEV" ] ; then python3 download_dump.py && chmod +rwx $DB_DUMP_PATH; else echo "Not DEV Environment, not downloading dump" ; fi

ADD ./restore_db.sh /docker-entrypoint-initdb.d/
