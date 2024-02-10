#!/bin/sh
docker run -it --rm -v .:/windows alpine /windows/alpine.sh
openssl dgst -sha256 windows.tar.gz