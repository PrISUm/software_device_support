#!/bin/bash

echo "Please log in with teamprisum Docker Hub password to push the built docker image when completed."
docker login -u teamprisum

BUILDER=$(docker buildx create --use)
docker buildx build --platform=linux/amd64,linux/arm64 --push -t teamprisum/alpine_cicd_verify .
docker buildx rm $BUILDER