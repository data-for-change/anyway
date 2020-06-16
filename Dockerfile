FROM ubuntu:19.10 AS builder

# Install system tools
RUN apt-get clean && \
    apt-get -y update && \
    apt-get install -y \
        python3.7-dev \
        build-essential \
        libpq-dev \
        virtualenv && \
    apt-get clean

WORKDIR /anyway

COPY requirements.txt /anyway

# We create the venv inside a builder container to avoid pulling in build deps into final image
RUN virtualenv /venv3 -p python3
RUN . /venv3/bin/activate && \
                    pip install -U setuptools wheel && \
                    pip install --upgrade pip && \
                    pip install -r requirements.txt

COPY  alembic.ini /anyway
COPY  alembic /anyway/alembic


FROM ubuntu:19.10 AS runtime

RUN apt-get clean && \
    apt-get -y update && \
    apt-get install -y \
        postgresql-client \
        default-jre-headless \
        virtualenv && \
    apt-get clean

WORKDIR /anyway

COPY --from=builder /venv3 /venv3

ENV VIRTUAL_ENV=/venv3
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV ALLOW_ALEMBIC_UPGRADE=yes
ENV FLASK_APP=anyway

COPY  alembic.ini /anyway
COPY  alembic /anyway/alembic

COPY . /anyway

EXPOSE 5000

RUN flask assets clean

ENTRYPOINT ["/anyway/docker-entrypoint.sh"]
CMD FLASK_APP=anyway flask run --host 0.0.0.0
