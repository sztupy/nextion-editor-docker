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
      FileAppend Error during enumeration %e%`n, *
    }
    Root := UIA.GetRootElement() ;
    Sleep, 1000
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
      FileAppend Error during enumeration %e%`n, *
    }
    Root := UIA.GetRootElement() ;
    Sleep, 1000
  }
  return el
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

ResetWarning() {
    FindWithName("AutomationID=pp2","OK") ;
}