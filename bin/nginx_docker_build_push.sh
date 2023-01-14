#!/usr/bin/env bash

REF_TAG="${GITHUB_REF##*/}" &&\
SHA_TAG=sha-`git rev-parse --short $GITHUB_SHA` &&\
echo REF_TAG=$REF_TAG &&\
echo SHA_TAG=$SHA_TAG &&\
ANYWAY_IMG_URL="${SERVER}/${DOCKER_REPOSITORY_ANYWAY}" &&\
NGINX_IMG_URL="${SERVER}/${DOCKER_REPOSITORY_NGINX}" &&\
echo ANYWAY_IMG_URL="${SERVER}/${DOCKER_REPOSITORY_ANYWAY}" &&\
echo NGINX_IMG_URL="${SERVER}/${DOCKER_REPOSITORY_NGINX}" &&\
bin/docker_login.sh &&\
docker pull "${ANYWAY_IMG_URL}:${SHA_TAG}" &&\
docker tag "${ANYWAY_IMG_URL}:${SHA_TAG}" "docker.pkg.github.com/hasadna/anyway/anyway:latest" &&\
if docker pull "${NGINX_IMG_URL}:${REF_TAG}"; then
    CACHE_FROM=" --cache-from ${NGINX_IMG_URL}:${REF_TAG} "
else
    CACHE_FROM=""
fi &&\
docker build $CACHE_FROM -t "${NGINX_IMG_URL}:${SHA_TAG}" nginx_docker &&\
docker tag "${NGINX_IMG_URL}:${SHA_TAG}" "${NGINX_IMG_URL}:${REF_TAG}" &&\
docker push "${NGINX_IMG_URL}:${SHA_TAG}" &&\
docker push "${NGINX_IMG_URL}:${REF_TAG}"
