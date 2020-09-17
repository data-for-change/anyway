#!/usr/bin/env bash

NGINX_IMG_URL"${SERVER}/${DOCKER_REPOSITORY_NGINX}" &&\

docker pull "${ANYWAY_IMG_URL}:${SHA_TAG}" &&\
if docker pull "${NGINX_IMG_URL}:${REF_TAG}"; then
    CACHE_FROM=" --cache-from ${NGINX_IMG_URL}:${REF_TAG} "
else
    CACHE_FROM=""
fi &&\
docker build $CACHE_FROM -t "${NGINX_IMG_URL}:${SHA_TAG}" nginx_docker