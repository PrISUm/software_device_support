#!/bin/bash

echo "Please log in with teamprisum Docker Hub password to push the built docker image when completed."
echo "It is suggested to configure docker to use a credential helper"
echo "https://docs.docker.com/engine/reference/commandline/login/#configure-the-credential-store"

docker login -u teamprisum || exit 1

BUILDER=$(docker buildx create --use)
docker buildx build --platform=linux/amd64,linux/arm64,linux/arm --push -t teamprisum/ubuntu_cicd_python_deploy .
docker buildx rm $BUILDER