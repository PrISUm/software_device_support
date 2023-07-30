#!/bin/sh

# Download ATMEL device support packages which include the CMSIS headers
# and make one downloadable zip containing all of our relevant processors

# This reads a file named packs of line-separated URLs, extracts them, and creates a distribution zip
# to be uploaded as a GitHub release.

# See http://packs.download.atmel.com
# Example URL: http://packs.download.atmel.com/Atmel.SAMC21_DFP.1.2.176.atpack

rm -rf device_support unpack
mkdir -p unpack

for pack in $(cat packs); do
  url=$(echo $pack | cut -d '!' -f 1)
  name=$(echo $pack | cut -d '!' -f 2)
  curl -L $url -o $name.zip
  mkdir -p unpack/$name
  (cd unpack/$name && unzip -o ../../$name.zip)
done

mkdir -p device_support

mkdir -p device_support/atmega
mv unpack/atmega/include device_support/atmega

mkdir -p device_support/samc21
mv unpack/samc21/samc21/include device_support/samc21
mv unpack/samc21/samc21/svd device_support/samc21

mkdir -p device_support/samd21a
mv unpack/samd21/samd21a/include device_support/samd21a
mv unpack/samd21/samd21a/svd device_support/samd21a
mkdir -p device_support/samd21b
mv unpack/samd21/samd21b/include device_support/samd21b
mv unpack/samd21/samd21b/svd device_support/samd21b
mkdir -p device_support/samd21c
mv unpack/samd21/samd21c/include device_support/samd21c
mv unpack/samd21/samd21c/svd device_support/samd21c
mkdir -p device_support/samd21d
mv unpack/samd21/samd21d/include device_support/samd21d
mv unpack/samd21/samd21d/svd device_support/samd21d

mkdir -p device_support/same51
mv unpack/same51/include device_support/same51
mv unpack/same51/svd device_support/same51

mkdir -p device_support/CMSIS/Core device_support/CMSIS/Core/Lib
mv unpack/cmsis/CMSIS/Core/Include device_support/CMSIS/Core 
# Note: libarm_cortexM0l_math.a is a prebuilt DSP library, but does not have LTO and may use libc.
# Note for future reference, the Neural Network library appears to be here and intact.
# Also, we should look into building the DSP library with LTO, it looks useful.

cp meson.build device_support

zip -r device_support.zip device_support
openssl dgst -sha256 device_support.zip