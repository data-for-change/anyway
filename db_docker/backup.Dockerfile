# Pulled Sep. 29, 2026 (bookworm based; bullseye is EOL and its packages were archived)
FROM postgres:15-bookworm@sha256:539ceaaae49b3a7c8a04467cf00cc6788d8e3f1675df41860d86eebc4c40524f
RUN apt-get update && apt-get install -y curl unzip &&\
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" &&\
    unzip awscliv2.zip && ./aws/install && rm -rf aws && aws --version
COPY dumpdb.sh /
ENTRYPOINT ["/dumpdb.sh"]
