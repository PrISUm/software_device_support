#!/bin/sh
apk add zstd python3 7zip
cd /windows
python3 fetch.py
sh