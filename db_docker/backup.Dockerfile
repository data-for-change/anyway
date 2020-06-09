FROM postgres:9.6
RUN apt-get update && apt-get install -y curl unzip &&\
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" &&\
    unzip awscliv2.zip && ./aws/install && rm -rf aws && aws --version
COPY dumpdb.sh /
ENTRYPOINT ["/dumpdb.sh"]
