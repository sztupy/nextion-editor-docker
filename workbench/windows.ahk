; Native window messages avoid a UI Automation traversal of the entire desktop.
FindDialogButton(marker, caption, title) {
    ; The editor's loading window can have hundreds of child controls. Query
    ; only the known modal window, then verify its text before clicking.
    selector := title " ahk_exe Nextion Editor.exe"
    WinGet, Windows, List, %selector%
    Loop, %Windows% {
        hwnd := Windows%A_Index%
        WinGetText, text, ahk_id %hwnd%
        if (!InStr(text, marker))
            continue
        WinGet, Controls, ControlListHwnd, ahk_id %hwnd%
        Loop, Parse, Controls, `n
        {
            ControlGetText, value,, ahk_id %A_LoopField%
            if (value = caption)
                return A_LoopField
        }
    }
    return 0
}

DismissMultimediaWarning() {
    button := FindDialogButton("Fail to load the multimedia application", "OK", "MessageForm")
    if (button) {
        ControlClick,, ahk_id %button%
        return true
    }
    return false
}

LogStep(message) {
    global Began
    FileAppend, % "[" Round((A_TickCount - Began) / 1000, 3) "s] " message "`n", *
}
