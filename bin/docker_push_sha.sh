#!/usr/bin/env bash

IMG_URL="${SERVER}/${DOCKER_REPOSITORY_NGINX}"

docker tag "${IMG_URL}:${SHA_TAG}" "${IMG_URL}:${REF_TAG}" &&\
docker push "${IMG_URL}:${SHA_TAG}" &&\
docker push "${IMG_URL}:${REF_TAG}"