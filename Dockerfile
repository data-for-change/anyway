FROM python:3.10-slim-bookworm AS builder

# Install system tools
RUN apt-get clean && \
    apt-get -y update && \
    apt-get install -y \
        build-essential \
        libpq-dev \
        binutils \
        postgresql-client && \
    apt-get clean

WORKDIR /anyway

COPY requirements.txt /anyway

# We create the venv inside a builder container to avoid pulling in build deps into final image
RUN python -m venv /venv3
RUN . /venv3/bin/activate && \
                    pip install -U setuptools wheel && \
                    pip install --upgrade pip && \
                    pip install -r requirements.txt

RUN find /venv3 -name '*.so' | xargs strip


FROM python:3.10-slim-bookworm AS runtime

RUN apt-get clean && \
    apt-get -y update && \
    apt-get install -y \
        postgresql-client && \
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

ENTRYPOINT ["/anyway/docker-entrypoint.sh"]
CMD FLASK_APP=anyway flask run --host 0.0.0.0
