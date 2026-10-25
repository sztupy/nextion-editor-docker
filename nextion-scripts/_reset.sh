killall -9 wine wineserver || true

rm -f /home/wineuser/.wine/drive_c/data/input.hmi || true
rm -rf /home/wineuser/.wine/drive_c/pics || true
rm -rf /home/wineuser/.wine/drive_c/fonts || true
rm -rf /home/wineuser/.wine/drive_c/users/wineuser/AppData/Roaming/Nextion\ Editor/work/*/output/*.tft || true
