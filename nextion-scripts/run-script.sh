
#!/usr/bin/env bash

export WINEDEBUG=-all

cp input/input.hmi /home/wineuser/.wine/drive_c/data/input.hmi

cp *.ahk /home/wineuser/.wine/drive_c/data/ahk/uia
cd /home/wineuser/.wine/drive_c/data/ahk/uia

wine 'C:\data\nextion\NextionEditor.exe' 'C:\data\input.hmi' &

wine ../AutoHotkeyU32.exe ResetWarning.ahk

SCRIPT_NAME=$1
shift

wine ../AutoHotkeyU32.exe $SCRIPT_NAME "$@"

sudo cp /home/wineuser/.wine/drive_c/users/wineuser/AppData/Roaming/Nextion\ Editor/work/*/output/*.tft /app/input/output.tft
sudo cp /home/wineuser/.wine/drive_c/data/input.hmi /app/input/output.hmi

exit