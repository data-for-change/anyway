#!/usr/bin/env bash

set -xv

echo "${DOCKER_PASSWORD}" | docker login ${SERVER} -u "${DOCKER_USERNAME}" --password-stdin
