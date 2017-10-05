FROM ubuntu:xenial

# Install system tools
RUN apt-get -y update && \
    apt-get install -y --no-install-recommends -qq \
        build-essential \
        python-pip \
        python-dev \
        python-tk \
        libpq-dev \
        sqlite3 \
        openjdk-9-jre \
    && apt-get clean

WORKDIR /anyway

# First copy only the requirement.txt, so changes in other files won't trigger
# a full pip reinstall
COPY requirements.txt /anyway
RUN pip install -U setuptools wheel
RUN pip install -r requirements.txt

COPY . /anyway

VOLUME ["/anyway/static"]
EXPOSE 5000

ENTRYPOINT ["/anyway/docker-entrypoint.sh"]
CMD ["python", "main.py", "testserver", "--open"]
