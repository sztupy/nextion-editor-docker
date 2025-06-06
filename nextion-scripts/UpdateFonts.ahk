#include Helpers.ahk
#ErrorStdOut

FileAppend Started processing`n, *

FileAppend Waiting for Page Panels to load `n, *

; Clicking the boot page
ClickElementAt("Page Panels", "AutomationId=colListBox1 AND IsEnabled=1", 10, 15) ;

Sleep 2000

; Switching to fonts panel
PicturePanel := FindElement("AutomationId=picListBox0 AND IsEnabled=1")
Bounds := PicturePanel.CurrentBoundingRectangle ;

Sleep 1000

FileAppend Clicking at location `n, *
MouseMove, Bounds.l + 70, Bounds.b + 5 ;
Click % Bounds.l + 70 " " Bounds.b + 5 ;

; Deleting old images
FileAppend Deleting old fonts `n, *

PicturePanel := FindElement("AutomationId=bar2 AND IsEnabled=1 AND Name=Fonts")
PicturePanel.SetFocus() ;
PicturePanel.Click("right") ;

Sleep 500
SendInput {Down}
Sleep 500
SendInput {Down}
Sleep 500
SendInput {Down}
Sleep 500
SendInput {Down}
Sleep 500
SendInput {Down}
Sleep 500
SendInput {Down}
Sleep 500
SendInput {Enter}

; Confirm

FileAppend Confirm to delete `n, *

Warning := FindElement("AutomationID=pp1 AND Name=Yes") ;
Warning.SetFocus() ;
Warning.Click("left") ;

Sleep 2000

; Add images

FileAppend Add fonts `n, *

PicturePanel.SetFocus() ;
PicturePanel.Click("right") ;

SendInput {Down}
Sleep 100
SendInput {Enter}

FileAppend Import dialog `n, *

Dialog := FindElement("LocalizedControlType=dialog AND Name=Open") ;

SendInput "C:\fonts\0.zi"{Space}

Sleep 100

Loop, 12 {
    SendInput "C:\fonts\%A_Index%.zi"{Space}
    Sleep 100
}

Sleep 1000

SendInput {Enter}

FileAppend Waiting for import `n, *

Sleep 3000

PixelSearch, Px, Py, Bounds.l+50, Bounds.t+50, Bounds.l+150, Bounds.t+150, 0xbeefdf, 1, Fast

if ErrorLevel {
    FileAppend Could not find imported font `n, *
    Sleep 6000

    PixelSearch, Px, Py, Bounds.l+50, Bounds.t+50, Bounds.l+150, Bounds.t+150, 0xbeefdf, 1, Fast
    if ErrorLevel {
        Sleep 12000

        PixelSearch, Px, Py, Bounds.l+50, Bounds.t+50, Bounds.l+150, Bounds.t+150, 0xbeefdf, 1, Fast

        if ErrorLevel {
            FileAppend Could not find imported font `n, *
            ExitApp 1
        }
    }
}

; Clicking the Program.s tab
ClickElementAt("Program.s", "AutomationId=tabControl1 AND IsEnabled=1 AND Name=superTabControl1", 100, 20) ;

Sleep 1000

; Changing code

Click 250 250

Clipboard := ""

Sleep 1000

SendInput, ^a

Sleep 100

SendInput, ^c

Sleep 100

ClipWait, 5

Var := Clipboard

Sleep 100

Size := StrLen(Var)

FileAppend Clipboard size %Size% `n, *

Sleep 100

Clipboard := RegExReplace( Var, "int charset=1","int charset=2" )

Sleep 100

SendInput, ^v

Sleep 1000

; Initiating save

Click 250 250

Sleep 500

SaveFile() ;

ExitApp