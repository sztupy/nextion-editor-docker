#!/usr/bin/env bash

set -euo pipefail

NAME=$1
BASE_FULL=$2

cd ~wineuser/NSPanel-Easy/hmi

BACKGROUND_LIGHT=$(sudo cat /data/options.json | jq -r ".configs[] | select(.name == \"${NAME}\") | .background.light // empty")
BACKGROUND_DARK=$(sudo cat /data/options.json | jq -r ".configs[] | select(.name == \"${NAME}\") | .background.dark // empty")
BACKGROUND_SPLASH=$(sudo cat /data/options.json | jq -r ".configs[] | select(.name == \"${NAME}\") | .background.splash // empty")

sudo rm -rf /app/input/input.hmi
sudo rm -rf /app/input/pics
sudo rm -rf /app/input/fonts
sudo mkdir -p /app/input

git reset --hard "@{u}"

case $BASE_FULL in
  landscape)
    BASE=landscape
    sudo cp nspanel_landscape.hmi /app/input/input.hmi
    ;;
  portrait)
    BASE=portrait
    sudo cp nspanel_portrait.hmi /app/input/input.hmi
    ;;
  landscape_inverted)
    BASE=landscape
    sudo cp nspanel_landscape_inverted.hmi /app/input/input.hmi
    ;;
  *)
    echo "Invalid base"
    exit 1
    ;;
esac

pushd dev/pics

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

COUNT=$(ls /app/input/pics | sort -n | tail -1 | tr -cd '[0-9]')

echo Number of pics: $COUNT

for i in $( seq 0 $COUNT ); do
  if [ ! -e /app/input/pics/$i.png ]; then
    echo "Image ID #${i} missing. Filling with placeholder"
    cp misc/placeholder.png /app/input/pics/$i.png
  fi
done

pushd /app

if [[ -n "${MANUAL:-}" ]]; then
  echo "Enabling RDP"

  [ ! -f /var/run/xrdp/xrdp-sesman.pid ] || sudo rm -f /var/run/xrdp/xrdp-sesman.pid
  [ ! -f /var/run/xrdp/xrdp.pid ] || sudo rm -f /var/run/xrdp/xrdp.pid

  sudo /usr/sbin/xrdp-sesman
  exec sudo /usr/sbin/xrdp --nodaemon
fi

echo "Generating TFT $NAME / $BASE_FULL"

./update_images.sh png $COUNT

sudo mkdir -p /haconfig/www/$NAME

echo "Saving results"
echo "Note: If the next line fails compilation was unsuccessful"

sudo cp input/output.tft /haconfig/www/$NAME/nspanel_$BASE_FULL.tft
sudo cp input/output.hmi /haconfig/www/$NAME/nspanel_$BASE_FULL.hmi

echo "Compilation for $NAME / $BASE_FULL was successful!"

popd

popd
