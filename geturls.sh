#!/bin/sh

DEVICE_SUPPORT="atmega samc21 samd21 same51"

curl -L http://packs.download.atmel.com | grep -F '<a data-toggle="collapse" data-parent="#accordion" href="#collapse-' > raw

for i in $DEVICE_SUPPORT; do
  grep -iF $i < raw | sed "s|.*Atmel \([^ ]*\) .*(\([0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*\)).*|http://packs.download.atmel.com/Atmel.\1_DFP.\2.atpack!$i|g" 
done > packs

grep -iF 'cmsis' < raw | sed 's|.*CMSIS .*(\([0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*\)).*|http://packs.download.atmel.com/ARM.CMSIS.\1.atpack!cmsis|g' >> packs