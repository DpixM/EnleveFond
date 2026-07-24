@echo off
chcp 65001 >nul
title Installation - EnleveFond
setlocal
cd /d "%~dp0"

echo ============================================================
echo    INSTALLATION DU LOGICIEL "ENLEVE FOND"
echo ============================================================
echo.
echo Ce script installe ce qu'il faut et cree EnleveFond.exe
echo (dans le sous-dossier "dist"). Comptez quelques minutes.
echo Ne fermez pas cette fenetre pendant l'operation.
echo.
pause

echo.
echo [1/4] Verification de Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  !! Python n'est pas installe.
    echo     Installez-le depuis https://www.python.org/downloads/
    echo     en COCHANT la case "Add Python to PATH", puis relancez.
    echo.
    pause
    exit /b 1
)
python --version

echo.
echo [2/4] Mise a jour de pip...
python -m pip install --upgrade pip

echo.
echo [3/4] Installation des modules (onnxruntime, numpy, pillow)...
python -m pip install --upgrade onnxruntime numpy pillow pyinstaller
if errorlevel 1 (
    echo.
    echo  !! Probleme pendant l'installation. Verifiez internet et relancez.
    echo.
    pause
    exit /b 1
)

echo.
echo [4/4] Creation de EnleveFond.exe...
if exist "build" rmdir /s /q "build"
if exist "dist"  rmdir /s /q "dist"
if exist "EnleveFond.spec" del /q "EnleveFond.spec"

python -m PyInstaller --onefile --windowed --name "EnleveFond" ^
    --collect-all onnxruntime ^
    --copy-metadata onnxruntime ^
    --copy-metadata numpy ^
    background_remover.py
if errorlevel 1 (
    echo.
    echo  !! La creation du .exe a echoue. Voir les messages ci-dessus.
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo    TERMINE !
echo ============================================================
echo.
echo  Votre logiciel :  %~dp0dist\EnleveFond.exe
echo.
echo  Astuce : clic droit sur EnleveFond.exe -^> Envoyer vers -^>
echo           Bureau (creer un raccourci).
echo.

if exist "dist\EnleveFond.exe" start "" "%~dp0dist"

pause
endlocal
