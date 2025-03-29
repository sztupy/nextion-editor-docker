#!/usr/bin/env bash
set -e

cd -- "$(dirname -- "$0")"

mkdir -p data

if ! [ -f data/ahk.zip ]; then
    curl -L --output data/ahk.zip https://www.autohotkey.com/download/1.1/AutoHotkey_1.1.37.02.zip
fi

if ! [ -f data/windows-en-us-kb971513.exe ]; then
    curl -L --output data/windows-en-us-kb971513.exe https://catalog.s.download.windowsupdate.com/msdownload/update/software/updt/2009/10/windows-en-us-kb971513_c18df80f512a6d9cea206825b981e33c0973abec.exe
fi

if ! [ -f data/pulovers.zip ]; then
    curl -L --output data/pulovers.zip https://github.com/mark-wiemer/adware-free-macro-creator/releases/download/v5.4.2/PuloversMacroCreator-Portable-5.4.2.zip
fi

if ! [ -f data/uiaviewer.zip ]; then
    curl -L --output data/uiaviewer.zip https://github.com/Descolada/UIAutomation/archive/0b500bb82e5b30243b577a67c5174f1e70c32ab4.zip
fi

if ! [ -f data/nextion.zip ]; then
    curl -L --output data/nextion.zip https://nextion.tech/download/nextion-setup-v1-67-1.zip
fi

docker build --progress=plain -t nextion-runner .