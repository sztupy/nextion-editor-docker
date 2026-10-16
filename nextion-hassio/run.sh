#!/usr/bin/env bash

set -eux

MAIN_CONFIG=$(sudo cat /data/options.json | jq -r '.main')
RESULT=$(sudo cat /data/options.json | jq -r ".configs[] | select(.name == \"${MAIN_CONFIG}\") | .result")
BASE=$(sudo cat /data/options.json | jq -r ".configs[] | select(.name == \"${MAIN_CONFIG}\") | .base")
BACKGROUND_LIGHT=$(sudo cat /data/options.json | jq -r ".configs[] | select(.name == \"${MAIN_CONFIG}\") | .background.light // empty")
BACKGROUND_DARK=$(sudo cat /data/options.json | jq -r ".configs[] | select(.name == \"${MAIN_CONFIG}\") | .background.dark // empty")
BACKGROUND_SPLASH=$(sudo cat /data/options.json | jq -r ".configs[] | select(.name == \"${MAIN_CONFIG}\") | .background.splash // empty")

ENABLE_DEBUG=$(sudo cat /data/options.json | jq -r '.create_debug_screenshots')
ENABLE_MANUAL=$(sudo cat /data/options.json | jq -r '.no_processing')

if [[ "$ENABLE_DEBUG" == "true" ]]; then
  export DEBUG=true
fi

if [[ "$ENABLE_MANUAL" == "true" ]]; then
  export MANUAL=true
fi

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

if [[ -n "$BACKGROUND_LIGHT" ]]; then
  sudo cp /haconfig/$BACKGROUND_LIGHT background/background_light_$BASE.png
fi

if [[ -n "$BACKGROUND_DARK" ]]; then
  sudo cp /haconfig/$BACKGROUND_DARK background/background_dark_$BASE.png
fi

if [[ -n "$BACKGROUND_SPLASH" ]]; then
  sudo cp /haconfig/$BACKGROUND_SPLASH background/background_splash_$BASE.png
fi

bash generate_images.sh $BASE
sudo cp -a $BASE /app/input/pics

ls -la /app/input/pics

COUNT=$(ls /app/input/pics | sort -n | tail -1 | tr -cd '[0-9]')

echo Number of pics: $COUNT

echo Injecting missing files

for i in $( seq 0 $COUNT ); do
  if [ ! -e /app/input/pics/$i.png ]; then
    echo "Image ID #${i} missing. Filling with placeholder"
    cp misc/placeholder.png /app/input/pics/$i.png
  fi
done

cd /app

if [[ -n "${MANUAL:-}" ]]; then
  [ ! -f /var/run/xrdp/xrdp-sesman.pid ] || sudo rm -f /var/run/xrdp/xrdp-sesman.pid
  [ ! -f /var/run/xrdp/xrdp.pid ] || sudo rm -f /var/run/xrdp/xrdp.pid

  sudo /usr/sbin/xrdp-sesman
  exec sudo /usr/sbin/xrdp --nodaemon
fi

if [[ -n "${DEBUG:-}" ]]; then
  ./dump_screenshots.sh &
fi

./update_images.sh png $COUNT

sudo mkdir -p /haconfig/www/$RESULT

sudo cp input/output.tft /haconfig/www/$RESULT/nspanel_$BASE.tft
sudo cp input/output.hmi /haconfig/www/$RESULT/nspanel_$BASE.hmi
