# Pulled Dec. 4, 2022
FROM postgres:15.1@sha256:766e8867182b474f02e48c7b1a556d12ddfa246138ddc748d70c891bf2873d82

# This base image needs CA certificates before APT can use the HTTPS archives.
RUN bootstrap_sources=$(mktemp) &&\
    printf '%s\n' 'deb http://deb.debian.org/debian bullseye main' > "$bootstrap_sources" &&\
    apt-get -o Dir::Etc::sourcelist="$bootstrap_sources" -o Dir::Etc::sourceparts=- update &&\
    apt-get -o Dir::Etc::sourcelist="$bootstrap_sources" -o Dir::Etc::sourceparts=- install -y ca-certificates &&\
    rm "$bootstrap_sources"

COPY install-aws-cli.sh /tmp/install-aws-cli.sh
RUN sh /tmp/install-aws-cli.sh && rm /tmp/install-aws-cli.sh
COPY dumpdb.sh /
ENTRYPOINT ["/dumpdb.sh"]
