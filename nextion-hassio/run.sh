#!/usr/bin/env bash

set -eux

MAIN_CONFIG=$(sudo cat /data/options.json | jq -r '.main')
RESULT=$(sudo cat /data/options.json | jq -r ".configs[] | select(.name == \"${MAIN_CONFIG}\") | .result")
BASE=$(sudo cat /data/options.json | jq -r ".configs[] | select(.name == \"${MAIN_CONFIG}\") | .base")
BACKGROUND_LIGHT=$(sudo cat /data/options.json | jq -r ".configs[] | select(.name == \"${MAIN_CONFIG}\") | .background_light")
BACKGROUND_DARK=$(sudo cat /data/options.json | jq -r ".configs[] | select(.name == \"${MAIN_CONFIG}\") | .background_dark")

cd ~wineuser

git clone --depth 1 https://github.com/edwardtfn/NSPanel-Easy

cd NSPanel-Easy/hmi

sudo mkdir -p /app/input

case $BASE in
  landscape)
    sudo cp nspanel_landscape.hmi /app/input/input.hmi
    ;;
  portrait)
    sudo cp nspanel_portrait.hmi /app/input/input.hmi
    ;;
  *)
    echo "Invalid base"
    exit 1
    ;;
esac

cd dev/pics

sudo cp /haconfig/$BACKGROUND_LIGHT background/background_light_$BASE.png
sudo cp /haconfig/$BACKGROUND_DARK background/background_dark_$BASE.png
./generate_images.sh $BASE
sudo cp -a $BASE /app/input/pics

ls -la /app/input/pics

COUNT=${ls /app/input/pics | sort -n | tail -1 | tr -cd '[0-9]'}

echo Number of pics: $COUNT

cd /app

./update_images.sh png $COUNT

sudo mkdir -p /haconfig/www

sudo cp input/output.tft /haconfig/www/$RESULT
sudo cp input/output.hmi /haconfig/www/$RESULT.hmi
