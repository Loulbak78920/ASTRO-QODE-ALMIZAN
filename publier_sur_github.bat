@echo off
setlocal EnableDelayedExpansion
chcp 65001 > nul
cd /d "%~dp0"

echo ================================================================================
echo  PUBLICATION DU DEPOT PUBLIC GITHUB -- M. AHMED EL BAHLOUL (IMAM8MAHDI)
echo  Compte GitHub : Loulbak78920 (Nom affiche : IMAM8MAHDI)
echo  Depot cible   : ASTRO-QODE-ALMIZAN
echo  DOI Zenodo    : 10.5281/zenodo.23554838
echo ================================================================================
echo.

set "DEFAULT_REMOTE=https://github.com/Loulbak78920/ASTRO-QODE-ALMIZAN.git"

if not "%~1"=="" (
    set "REMOTE_URL=%~1"
) else (
    set "REMOTE_URL=%DEFAULT_REMOTE%"
)

echo [1/4] Configuration du remote Git origin vers :
echo       !REMOTE_URL!
git remote remove origin >nul 2>&1
git remote add origin "!REMOTE_URL!"

echo [2/4] Verification de la branche principale...
git branch -M main

echo [3/4] Verification de l'acces au depot distant...
git ls-remote --exit-code origin >nul 2>&1
if errorlevel 1 (
    echo [ATTENTION] Le depot distant ne semble pas accessible ou n'est pas encore cree.
    echo Si vous devez creer le depot sur votre compte, ouvrez :
    echo https://github.com/new?name=ASTRO-QODE-ALMIZAN
    echo.
) else (
    echo [OK] Depot distant detecte et accessible avec succes.
)

echo [4/4] Publication des commits et des tags vers GitHub...
git push -u origin main --tags
if errorlevel 1 (
    echo.
    echo ================================================================================
    echo [ERREUR] Le push a echoue. Verifiez vos identifiants ou permissions GitHub.
    echo ================================================================================
    pause
    exit /b 1
)

echo.
echo ================================================================================
echo [SUCCES] Le depot a ete publie avec succes sur GitHub !
echo URL Publique : https://github.com/Loulbak78920/ASTRO-QODE-ALMIZAN
echo DOI Officiel : https://doi.org/10.5281/zenodo.23554838
echo ================================================================================
echo.
endlocal
