FROM alpine:latest

# Install programs needed for all CICD tasks (software_development, telemetry, and strategy)
RUN apk add clang lld llvm musl-dev \
            py3-pip samurai pkgconf cython python3-dev \
            git openssh yarn openssl-dev zlib-dev && \
  pip3 install meson