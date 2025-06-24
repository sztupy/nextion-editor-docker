#!/usr/bin/env bash

export WINEDEBUG=-all

cp input/input.hmi /home/wineuser/.wine/drive_c/data/input.hmi
cp -a input/pics /home/wineuser/.wine/drive_c/

cp *.ahk /home/wineuser/.wine/drive_c/data/ahk/uia
cd /home/wineuser/.wine/drive_c/data/ahk/uia

wine 'C:\data\nextion\NextionEditor.exe' 'C:\data\input.hmi' &

wine ../AutoHotkeyU32.exe ResetWarning.ahk

wine ../AutoHotkeyU32.exe UpdateImages.ahk $1 $2

sudo cp /home/wineuser/.wine/drive_c/users/wineuser/AppData/Roaming/Nextion\ Editor/work/*/output/*.tft /app/input/output.tft
sudo cp /home/wineuser/.wine/drive_c/data/input.hmi /app/input/output.hmi

exit
