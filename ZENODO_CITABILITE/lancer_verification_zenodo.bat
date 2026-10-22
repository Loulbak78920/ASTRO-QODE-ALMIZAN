@echo off
chcp 65001 > nul
SETLOCAL
SET "SCRIPT_DIR=%~dp0"
SET "PY_EXE=C:\Users\Administrateur\AppData\Local\Python\pythoncore-3.14-64\python.exe"

IF EXIST "%PY_EXE%" (
    "%PY_EXE%" -u "%SCRIPT_DIR%verifier_et_empaqueter_zenodo.py" %*
) ELSE (
    py -u "%SCRIPT_DIR%verifier_et_empaqueter_zenodo.py" %*
)
ENDLOCAL
