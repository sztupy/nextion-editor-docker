#!/usr/bin/env bash

set -eux

MAIN_CONFIG=$(sudo cat /data/options.json | jq -r '.main')
RESULT=$(sudo cat /data/options.json | jq -r ".configs[] | select(.name == \"${MAIN_CONFIG}\") | .result")
BASE=$(sudo cat /data/options.json | jq -r ".configs[] | select(.name == \"${MAIN_CONFIG}\") | .base")
BACKGROUND=$(sudo cat /data/options.json | jq -r ".configs[] | select(.name == \"${MAIN_CONFIG}\") | .background")

cd ~wineuser

git clone --depth 1 https://github.com/sztupy/NSPanel_HA_Blueprint

cd NSPanel_HA_Blueprint/hmi

sudo mkdir -p /app/input

PICTURE_DIR=eu

case $BASE in
  eu)
    sudo cp nspanel_eu.HMI /app/input/input.hmi
    ;;
  us)
    sudo cp nspanel_us.HMI /app/input/input.hmi
    PICTURE_DIR=us
    ;;
  usland)
    sudo cp nspanel_us_land.HMI /app/input/input.hmi
    ;;
  eucjk)
    sudo cp nspanel_CJK_eu.HMI /app/input/input.hmi
    ;;
  uscjk)
    sudo cp nspanel_CJK_us.HMI /app/input/input.hmi
    PICTURE_DIR=us
    ;;
  uslandcjk)
    sudo cp nspanel_CJK_us_land.HMI /app/input/input.hmi
    ;;
  *)
    echo "Invalid base"
    exit 1
    ;;
esac

cd dev/ui

sudo cp /haconfig/$BACKGROUND back.png
../scripts/generate_images.sh back.png
sudo cp -a $PICTURE_DIR /app/input/pics

ls -la /app/input/pics

cd /app

./update_images.sh png 42

sudo mkdir -p /haconfig/www

sudo cp input/output.tft /haconfig/www/$RESULT
sudo cp input/output.hmi /haconfig/www/$RESULT.hmi
