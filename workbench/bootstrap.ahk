#NoEnv
#NoTrayIcon
#SingleInstance Force
#ErrorStdOut
#Include Z:\opt\workbench\windows.ahk
SetTitleMatchMode, 2
Began := A_TickCount
Loop {
    if DismissMultimediaWarning() {
        LogStep("Optional multimedia warning dismissed")
        ExitApp, 0
    }
    if WinExist("Nextion Editor(C:\workbench\project.hmi)")
        ExitApp, 0
    if (A_TickCount - Began > 300000)
        ExitApp, 1
    Sleep, 250
}
