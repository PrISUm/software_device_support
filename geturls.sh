#!/bin/sh

DEVICE_SUPPORT="atmega samc21 samd21"

for i in $DEVICE_SUPPORT; do
  grep -iF $i < file | sed 's|.*Atmel \([^ ]*\) .*(\([0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*\)).*|http://packs.download.atmel.com/Atmel.\1_DFP.\2.atpack|g'
done > packs