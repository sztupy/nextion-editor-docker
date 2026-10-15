#!/usr/bin/env bash

set -eux

MAIN_CONFIG=$(sudo cat /data/options.json | jq -r '.main')
RESULT=$(sudo cat /data/options.json | jq -r ".configs[] | select(.name == \"${MAIN_CONFIG}\") | .result")
BASE=$(sudo cat /data/options.json | jq -r ".configs[] | select(.name == \"${MAIN_CONFIG}\") | .base")
BACKGROUND=$(sudo cat /data/options.json | jq -r ".configs[] | select(.name == \"${MAIN_CONFIG}\") | .background")

cd ~wineuser

git clone --depth 1 https://github.com/edwardtfn/NSPanel-Easy

cd NSPanel-Easy/hmi

sudo mkdir -p /app/input

case $BASE in
  landscape)
    sudo cp nspanel_landscape.HMI /app/input/input.hmi
    ;;
  portrait)
    sudo cp nspanel_portrait.HMI /app/input/input.hmi
    ;;
  *)
    echo "Invalid base"
    exit 1
    ;;
esac

cd dev/pics

sudo cp /haconfig/$BACKGROUND back.png
./generate_images.sh $BASE
sudo cp -a $BASE /app/input/pics

ls -la /app/input/pics

cd /app

./update_images.sh png 95

sudo mkdir -p /haconfig/www

sudo cp input/output.tft /haconfig/www/$RESULT
sudo cp input/output.hmi /haconfig/www/$RESULT.hmi
