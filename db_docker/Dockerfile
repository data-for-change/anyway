FROM postgis/postgis:9.6-2.5

RUN apt-get update && apt-get install -y curl unzip &&\
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" &&\
    unzip awscliv2.zip && ./aws/install && rm -rf aws && aws --version
COPY restore_db.sh /docker-entrypoint-initdb.d/

# values suitable for docker-compose environment
ENV POSTGRES_PASSWORD anyway
ENV POSTGRES_USER anyway
ENV POSTGRES_DB anyway
ENV DBRESTORE_AWS_BUCKET=anyway-partial-db-dumps
