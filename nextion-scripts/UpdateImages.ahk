#include Helpers.ahk
#ErrorStdOut

FileAppend Started processing`n, *

FileAppend Waiting for Page Panels to load `n, *

; Clicking the boot page
ClickElementAt("Page Panels", "AutomationId=colListBox1 AND IsEnabled=1", 10, 15) ;

Sleep 2000

; Deleting old images
FileAppend Deleting old images `n, *

PicturePanel := FindElement("AutomationId=picListBox0 AND IsEnabled=1")
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

FileAppend Add images `n, *

PicturePanel.SetFocus() ;
PicturePanel.Click("right") ;

SendInput {Down}
Sleep 100
SendInput {Enter}

FileAppend Import dialog `n, *

Dialog := FindElement("LocalizedControlType=dialog AND Name=Open") ;

argv := GetArgs() ;
Extension := argv[1]
Amount := argv[2]

SendInput "C:\pics\0.png"{Space}

Sleep 100

Loop %Amount% {
    SendInput "C:\pics\%A_Index%.%Extension%"{Space}
    Sleep 100
}

Sleep 1000

SendInput {Enter}

FileAppend Waiting for import `n, *

Warning := FindElement("AutomationID=pp2 AND Name=OK") ;
Warning.SetFocus() ;
Warning.Click("left") ;

Sleep 3000

; Initiating save

Click 250 250

Sleep 500

SaveFile() ;

ExitApp
