#!/usr/bin/env bash

if github.ref == 'refs/heads/master'; then
    ANYWAY_IMG_URL="${SERVER}/${DOCKER_REPOSITORY_ANYWAY}"
    docker tag "${ANYWAY_IMG_URL}:${SHA_TAG}" "${ANYWAY_IMG_URL}:latest"
fi
