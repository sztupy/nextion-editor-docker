#!/usr/bin/env bash

export WINEDEBUG=-all


cp *.ahk /home/wineuser/.wine/drive_c/data/ahk/uia
cd /home/wineuser/.wine/drive_c/data/ahk/uia

wine 'C:\data\nextion\NextionEditor.exe' 'C:\data\file.hmi' &

wine ../AutoHotkeyU32.exe ResetWarning.ahk

wine ../AutoHotkeyU32.exe Compile.ahk

cp /home/wineuser/.wine/drive_c/users/wineuser/AppData/Roaming/Nextion\ Editor/work/*/output/*.tft /app
