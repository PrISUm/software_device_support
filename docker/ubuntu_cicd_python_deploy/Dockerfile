FROM ubuntu:latest

ENV PYTHON_VERSIONS='3.10 3.11'

ENV DEBIAN_FRONTEND=noninteractive

# Install every python version and create venvs with meson/cython for each one.
RUN apt update && \
  apt install -y build-essential ninja-build git openssh-client && \
  for version in $PYTHON_VERSIONS; do \
    apt install -y python$version-dev python$version-venv && \
    python$version -m venv /venv$version && \
    . /venv$version/bin/activate && \
    pip3 install meson cython; \
  done