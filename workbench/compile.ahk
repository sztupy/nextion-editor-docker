#NoEnv
#NoTrayIcon
#SingleInstance Force
#ErrorStdOut
#Include C:\data\ahk\uia\Lib\UIA_Interface.ahk
SetTitleMatchMode, 2
SetWorkingDir, C:\workbench
CoordMode, Mouse, Screen
UIA := UIA_Interface()
; The warning is optional. Never spend a full timeout waiting for it.
Loop, 60 {
    try {
        OK := UIA.GetRootElement().FindFirstBy("AutomationID=pp2 AND Name=OK")
        if (OK)
            OK.Click("left")
    }
    if WinExist("Nextion Editor(C:\workbench\project.hmi)")
        break
    Sleep, 500
}
WinWait, Nextion Editor(C:\workbench\project.hmi),, 15
if ErrorLevel {
    FileAppend, Project window was not ready`n, *
    ExitApp, 10
}
WinActivate, Nextion Editor(C:\workbench\project.hmi)
WinWaitActive, Nextion Editor(C:\workbench\project.hmi),, 5
WinMaximize, Nextion Editor(C:\workbench\project.hmi)
FileAppend, Project loaded`n, *
Sleep, 700
SendInput, ^s
Sleep, 500
; The application uses a custom menu that intermittently drops Alt/Enter.
; The dedicated X display is fixed at 1024x768 with a maximized editor.
Click, 15, 30
Sleep, 300
Click, 85, 55
FileAppend, TFT output menu selected`n, *
Loop, 40 {
    try {
        Button := UIA.GetRootElement().FindFirstBy("AutomationId=buttonX2 AND Name=Output")
    }
    if (Button)
        break
    if (A_Index = 2) {
        ; Slow emulated desktops can drop the second mouse click while painting
        ; the custom File menu. Reset it and select the first item by keyboard.
        SendInput, {Esc}
        Sleep, 300
        Click, 15, 30
        Sleep, 1500
        SendInput, {Down}
        Sleep, 300
        SendInput, {Enter}
        FileAppend, Retried TFT menu after a slow UI response`n, *
    }
    Sleep, 250
}
if (!Button) {
    FileAppend, TFT output dialog was not ready`n, *
    ExitApp, 11
}
Button.SetFocus()
Button.Click("left")
FileAppend, Compile started`n, *
Loop, 240 {
    WinGet, EditorHwnd, ID, Nextion Editor(C:\workbench\project.hmi)
    WinGet, Controls, ControlListHwnd, ahk_id %EditorHwnd%
    Loop, Parse, Controls, `n
    {
        ControlGetText, Value,, ahk_id %A_LoopField%
        if (InStr(Value, "Compile Successful!") || InStr(Value, "Compile Failed")) {
            FileDelete, C:\workbench\compile-result.txt
            FileAppend, %Value%, C:\workbench\compile-result.txt, UTF-8
            if InStr(Value, "Compile Failed")
                ExitApp, 12
            ExitApp, 0
        }
    }
    Sleep, 500
}
FileAppend, Compiler completion was not observed`n, *
ExitApp, 13
