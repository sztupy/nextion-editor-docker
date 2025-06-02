#include Helpers.ahk
#ErrorStdOut

FileAppend Started processing`n, *

FileAppend Waiting for Page Panels to load `n, *

; Clicking the boot page
ClickElementAt("Page Panels", "AutomationId=colListBox1 AND IsEnabled=1", 10, 15) ;

; Clicking the first variable - version
ClickElementAt("Variable Panels", "AutomationId=objpanel AND IsEnabled=1", 30, 30) ;

; Clicking the Txt field
ClickElementAt("Data Grid", "AutomationId=dataGridView1 AND IsEnabled=1", 130, 125) ;

; Updating the variable

argv := GetArgs() ;
Version := argv[1]

FileAppend % "New version: " Version "`n", *

SendInput, %Version%{Enter}

Sleep 2000

; Initiating save

Click 250 250

SaveFile() ;

ExitApp