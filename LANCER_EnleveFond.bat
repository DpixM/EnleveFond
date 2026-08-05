@echo off
chcp 65001 >nul
cd /d "%~dp0"

REM Lance directement le programme A JOUR (avec la vectorisation),
REM sans avoir besoin de reconstruire le .exe.

REM S'assure que les modules necessaires sont presents (rapide si deja installes)
python -m pip install --quiet onnxruntime numpy pillow potracer >nul 2>&1

REM Lance sans fenetre noire
start "" pythonw "background_remover.py"
