sudo mkdir -p /app/input/screenshots

while /bin/true; do
  sudo import -window root /app/input/screenshots/$(date '+%Y%m%d%H%M%S')_screenshot.png
  sleep 1
done &
