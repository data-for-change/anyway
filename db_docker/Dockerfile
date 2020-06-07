FROM postgis/postgis:9.6-2.5-alpine

RUN apk add --update-cache python3 sudo &&\
    pip3 install gdown s3cmd
COPY download_dump.py /
COPY restore_db.sh /docker-entrypoint-initdb.d/

ENV POSTGRES_PASSWORD anyway
ENV POSTGRES_USER anyway
ENV POSTGRES_DB anyway
