while /bin/true; do
    sudo import -window root /app/input/$(date '+%Y%m%d%H%M%S')_screenshot.png
    sleep 1
done &