#!/usr/bin/env bash

set -euo pipefail

ENABLE_DEBUG=$(sudo cat /data/options.json | jq -r '.create_debug_screenshots')
ENABLE_MANUAL=$(sudo cat /data/options.json | jq -r '.no_processing')
REPOSITORY=$(sudo cat /data/options.json | jq -r '.repository')
BRANCH=$(sudo cat /data/options.json | jq -r '.branch')
RETRIES=$(sudo cat /data/options.json | jq -r '.retries')
TIMEOUT=$(sudo cat /data/options.json | jq -r '.timeout')


if [[ "$ENABLE_DEBUG" == "true" ]]; then
  export DEBUG=true
fi

if [[ "$ENABLE_MANUAL" == "true" ]]; then
  export MANUAL=true
fi

cd ~wineuser

git clone --branch $BRANCH --single-branch --depth 1 $REPOSITORY

cd NSPanel-Easy/hmi

if [[ -n "${DEBUG:-}" ]]; then
  /app/dump_screenshots.sh &
fi

for NAME in $(sudo cat /data/options.json | jq -r '.configs[] | select(.enabled) | .name'); do
  for BASE_FULL in $(sudo cat /data/options.json | jq -r ".configs[] | select(.name == \"${NAME}\") | .base | to_entries[] | select(.value).key"); do
    RETRY_COUNT=$RETRIES
    echo
    echo
    echo ==============================
    echo Running for $NAME / $BASE_FULL
    echo Attempts left: $RETRY_COUNT
    echo
    while ! timeout -v $TIMEOUT bash /app/build_tft.sh $NAME $BASE_FULL; do
      ((RETRY_COUNT=RETRY_COUNT-1))
      echo Attempts left: $RETRY_COUNT
      echo
      if [[ $RETRY_COUNT -le 0 ]]; then
        echo No more attempts, failing
        exit 1
      fi
    done
  done
done

exit 0
