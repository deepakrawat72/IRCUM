cls
@ECHO OFF
ECHO. *************************************
ECHO. ***** RUNNING THE IRCUM UTILITY *****
ECHO. *************************************
SET pyScriptPath=%1
ECHO. Python script to run on path - %pyScriptPath%\bin\IRCUM_core.py
ECHO. python  %pyScriptPath%\bin\IRCUM_core.py %pyScriptPath%
python %pyScriptPath%\bin\IRCUM_core.py %pyScriptPath%
ECHO. *************************************
ECHO. ***** IRCUM PROCESSING COMPLETE *****
ECHO. *************************************