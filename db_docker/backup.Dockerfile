FROM postgres:9.6-alpine

RUN apk add --update-cache python py-pip && pip install s3cmd
COPY dumpdb.sh /
ENTRYPOINT ["/dumpdb.sh"]
