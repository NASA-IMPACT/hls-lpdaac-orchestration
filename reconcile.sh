#!/bin/bash
doy=2022081
while [ $doy -le 2022089 ];
do
  echo $doy
  python3 make_report_athena.py $doy
  doy=$(( $doy + 1 ))
  sleep 40m
done
