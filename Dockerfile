FROM ubuntu:xenial

# Install system tools
RUN apt-get clean
RUN apt-get -y update
RUN apt-get install -y \
        build-essential \
        python-pip \
        python-dev \
        python-tk \
        libpq-dev \
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
