#include Helpers.ahk
#ErrorStdOut

FileAppend Started processing`n, *

FileAppend Waiting for menubar to appear`n, *

MenuBar := FindWithName("AutomationId=bar5", "bar5") ;
bounds := MenuBar.CurrentBoundingRectangle ;

FileAppend % "MenuBar found: " bounds.t " `n", *

FileAppend % "Click File `n", *

MouseMove, bounds.l + 5, bounds.t + 5 ;
Sleep 2000 ;

Click % bounds.l + 5 " " bounds.t + 5 ;
Sleep 2000 ;

FileAppend % "Click TFT `n", *

Sleep 2000 ;

MouseMove, bounds.l + 10, bounds.t + 15 ;
Click % bounds.l + 10 " " bounds.t + 15 ;

Sleep 2000 ;

FileAppend % "Save file `n", *

SaveButton := FindWithName("AutomationId=buttonX2","Output") ;
SaveButton.SetFocus() ;
SaveButton.Click("left") ;

FileAppend % "Wait for save to finish `n", *

ElementGone("AutomationId=buttonX2") ;

ExitApp