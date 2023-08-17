FROM ubuntu:20.04 AS builder

# Install system tools
RUN apt-get clean && \
    apt-get -y update && \
    apt-get install -y \
        python3-dev \
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

RUN find /venv3 -name '*.so' | xargs strip


FROM ubuntu:20.04 AS runtime

RUN apt-get clean && \
    apt-get -y update && \
    apt-get install -y \
        postgresql-client \
        virtualenv && \
    apt-get clean

WORKDIR /anyway

COPY --from=builder /venv3 /venv3

ENV VIRTUAL_ENV=/venv3
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV ALLOW_ALEMBIC_UPGRADE=yes
ENV FLASK_APP=anyway
ENV FLASK_ENV=development

COPY . /anyway

EXPOSE 5000

RUN flask assets clean

ENTRYPOINT ["/anyway/docker-entrypoint.sh"]
CMD FLASK_APP=anyway flask run --host 0.0.0.0
