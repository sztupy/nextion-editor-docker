#include Helpers.ahk
#ErrorStdOut

FileAppend Started processing`n, *

FileAppend Waiting for Page Panels to load `n, *

; Clicking the boot page
ClickElementAt("Page Panels", "AutomationId=colListBox1 AND IsEnabled=1", 10, 15) ;

Sleep 2000

; Clicking the parameter ComboBox
ClickElementAt("Attribute Selector", "AutomationId=comboBox1 AND IsEnabled=1", 10, 10) ;

Sleep 1000

; p for ProgressBar
SendInput p

Sleep 1000

; Get to data grid
ClickElementAt("Data Grid", "AutomationId=dataGridView1 AND IsEnabled=1", 20, 125) ;

Sleep 500

; Get to the bottom
SendInput {PgDn}

Sleep 100

SendInput {PgDn}

Sleep 100

SendInput {PgDn}

Sleep 100

; What we need is one up and one right

SendInput {Up}

Sleep 100

SendInput {Right}

Sleep 100

SendInput 480{Enter}

Sleep 500

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

Clipboard := RegExReplace( Var, "int display_mode=1","int display_mode=3" )

Sleep 100

SendInput, ^v

Sleep 1000

; Initiating save

Click 250 250

Sleep 500

SaveFile() ;

ExitApp