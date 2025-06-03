#include <UIA_Interface>

FindElement(expr) {
  startTime := A_TickCount
  UIA := UIA_Interface() ;
  Root := UIA.GetRootElement() ;
  el := Null ;  

  while (!el && (A_tickCount - startTime < 60000)) {
    FileAppend Waiting for object %expr% ...`n, *
    Try {
      el := Root.FindFirstBy(expr) ;
    } catch e {
      FileAppend Error during enumeration %e% retrying...`n, *
    }
    Root := UIA.GetRootElement() ;
    Sleep, 1000
  }

  if (!el) {
    FileAppend Could not find element %expr% Exiting`n, *
    ExitApp, 1
  }
  return el
}

ElementGone(expr) {
  startTime := A_TickCount
  UIA := UIA_Interface() ;
  Root := UIA.GetRootElement() ;
  el := Root.FindFirstBy(expr) ;

  while (el && (A_tickCount - startTime < 60000)) {
    FileAppend Waiting for object %expr% to disappear...`n, *
    Try {
      el := Root.FindFirstBy(expr) ;
    } catch e {
      FileAppend Error during enumeration %e% retrying...`n, *
    }
    Root := UIA.GetRootElement() ;
    Sleep, 1000
  }
  return el
}

ResetWarning() {
  Warning := FindElement("AutomationID=pp2 AND Name=OK") ;
  Warning.SetFocus() ;
  Warning.Click("left") ;
}

Args( CmdLine := "", Skip := 0 ) {
  ; By SKAN,  http://goo.gl/JfMNpN,  CD:23/Aug/2014 | MD:24/Aug/2014
  Local pArgs := 0, nArgs := 0, A := []
  
  pArgs := DllCall( "Shell32\CommandLineToArgvW", "WStr",CmdLine, "PtrP",nArgs, "Ptr" ) 

  Loop % ( nArgs ) 
     If ( A_Index > Skip ) 
       A[ A_Index - Skip ] := StrGet( NumGet( ( A_Index - 1 ) * A_PtrSize + pArgs ), "UTF-16" )  

  Return A,   A[0] := nArgs - Skip,   DllCall( "LocalFree", "Ptr",pArgs )  
}

GetArgs() {
  CmdLine := DllCall( "GetCommandLine", "Str" )
  Skip    := ( A_IsCompiled ? 1 : 2 )

  argv    := Args( CmdLine, Skip )

  return argv ;
}

FindWithName(expr, name) {
  startTime := A_TickCount
  el := FindElement(expr) ;

  while (!el.Name == name) {
    FileAppend Restarting to get proper object`n, *
    el := FindElement(expr) ;
    Sleep, 1000
  }
  return el
}

ClickElementAt(name, expr, left, top) {
  FileAppend % "Waiting for element: " name " `n", *

  Panel := FindElement(expr) ;
  Bounds := Panel.CurrentBoundingRectangle ;

  Sleep 2000

  FileAppend Clicking at location `n, *
  MouseMove, Bounds.l + left, Bounds.t + top ;
  Click % Bounds.l + left " " Bounds.t + top ;

  Sleep 2000
}

SaveFile() {
  SendInput, ^s

  Sleep 2000 ;

  ; Enter the first item of the menu - TFT Ouput
  SendInput {Alt down}
  Sleep 500 ;
  SendInput {Alt up}
  Sleep 500 ;
  SendInput {Enter}
  Sleep 500 ;
  SendInput {Enter}
  Sleep 500 ;

  FileAppend % "Save file `n", *

  SaveButton := FindElement("AutomationId=buttonX2 AND Name=Output") ;
  SaveButton.SetFocus() ;
  SaveButton.Click("left") ;

  FileAppend % "Wait for save to finish `n", *

  ElementGone("AutomationId=buttonX2") ;
}