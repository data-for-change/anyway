# Pulled Dec. 4, 2022
FROM postgres:15.1@sha256:766e8867182b474f02e48c7b1a556d12ddfa246138ddc748d70c891bf2873d82
RUN apt-get update && apt-get install -y curl unzip &&\
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" &&\
    unzip awscliv2.zip && ./aws/install && rm -rf aws && aws --version
COPY dumpdb.sh /
ENTRYPOINT ["/dumpdb.sh"]
