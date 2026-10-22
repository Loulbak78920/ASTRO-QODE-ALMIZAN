@echo off
chcp 65001 > nul
SETLOCAL
cd /d "%~dp0"
echo ================================================================================
echo PUBLICATION DU DEPOT PUBLIC GITHUB -- M. AHMED EL BAHLOUL (IMAM8MAHDI)
echo DOI Officiel Reel : 10.5281/zenodo.23554838
echo ================================================================================
IF "%~1"=="" (
    echo Statut Git actuel du depot :
    git status -s -b
    echo.
    echo Pour pousser vers votre depot GitHub distant, executez :
    echo   .\publier_sur_github.bat https://github.com/IMAM8MAHDI/ASTRO-QODE-ALMIZAN.git
) ELSE (
    git remote remove origin >nul 2>&1
    git remote add origin "%~1"
    git branch -M main
    git push -u origin main --tags
)
ENDLOCAL
