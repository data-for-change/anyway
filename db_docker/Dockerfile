# Pulled Dec. 4, 2022
FROM postgis/postgis:15-3.3@sha256:3f0bf89a2f04ed89481393ae11909f16a37ff23f30089f3e599b74541f408d6a

RUN apt-get update && apt-get install -y curl unzip &&\
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" &&\
    unzip awscliv2.zip && ./aws/install && rm -rf aws && aws --version
COPY restore_db.sh /docker-entrypoint-initdb.d/

# values suitable for docker-compose environment
ENV POSTGRES_PASSWORD anyway
ENV POSTGRES_USER anyway
ENV POSTGRES_DB anyway
ENV DBRESTORE_AWS_BUCKET=dfc-anyway-partial-db-dumps
