#!/bin/sh

# Download ATMEL device support packages which include the CMSIS headers
# and make one downloadable zip containing all of our relevant processors

# This reads a file named packs of line-separated URLs, extracts them, and creates a distribution zip
# to be uploaded as a GitHub release.

# See http://packs.download.atmel.com
# Example URL: http://packs.download.atmel.com/Atmel.SAMC21_DFP.1.2.176.atpack

rm -rf dist unpack
mkdir -p unpack

for pack in $(cat packs); do
  curl -L $pack > pack.zip
  (cd unpack && unzip -o ../pack.zip)
done

mkdir -p dist

mkdir -p dist/avr
mv unpack/include dist/avr/include

ARM_DIRS="samc21 samc21n samd21a samd21b samd21c samd21d"

for i in $ARM_DIRS; do
  mkdir -p dist/$i
  mv unpack/$i/include dist/$i
  mv unpack/$i/svd dist/$i
done

zip -r device_support.zip dist