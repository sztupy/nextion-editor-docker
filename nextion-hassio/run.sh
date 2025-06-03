#!/usr/bin/env bash

set -eux

MAIN_CONFIG=$(cat /data/options.json | jq -r '.main')
RESULT=$(cat /data/options.json | jq -r ".configs[] | select(.name == \"${MAIN_CONFIG}\") | .result")
BASE=$(cat /data/options.json | jq -r ".configs[] | select(.name == \"${MAIN_CONFIG}\") | .base")
BACKGROUND=$(cat /data/options.json | jq -r ".configs[] | select(.name == \"${MAIN_CONFIG}\") | .background")

cd ~wineuser

git clone --depth 1 https://github.com/sztupy/NSPanel_HA_Blueprint

cd NSPanel_HA_Blueprint/hmi

sudo mkdir -p /app/input
sudo cp nspanel_eu.HMI /app/input/input.hmi

cd dev/ui

cp /haconfig/$BACKGROUND back.png
./generate_images.sh back.png
sudo cp -a eu /app/input/pics

ls -la /app/input/pics

cd /app

./update_images.sh

sudo mkdir -p /haconfig/www

sudo cp input/output.tft /haconfig/www/$RESULT
sudo cp input/output.hmi /haconfig/www/$RESULT.hmi