FROM ubuntu:19.10

# Install system tools
# Install system tools
RUN apt-get clean && \
    apt-get -y update && \
    apt-get install -y \
        python3.7-dev \
        build-essential \
        postgresql-client \
        libpq-dev \
        default-jdk \
        virtualenv && \
    apt-get clean

WORKDIR /anyway

COPY requirements.txt /anyway


# First copy only the requirement.txt, so changes in other files won't trigger
# a full pip reinstall

RUN virtualenv /venv3 -p python3
ENV VIRTUAL_ENV=/venv3
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN . /venv3/bin/activate && \
                    pip install -U setuptools wheel && \
                    pip install --upgrade pip && \
                    pip install -r requirements.txt

COPY  alembic.ini /anyway
COPY  alembic /anyway/alembic


COPY . /anyway

EXPOSE 5000

ENTRYPOINT ["/anyway/docker-entrypoint.sh"]

CMD FLASK_APP=anyway flask run --host 0.0.0.0

ENV ALLOW_ALEMBIC_UPGRADE=yes
ENV FLASK_APP=anyway
RUN flask assets clean
