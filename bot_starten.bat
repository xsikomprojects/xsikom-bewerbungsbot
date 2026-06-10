@echo off
title XsiKOM-BewerbungsBOT - Konsole
color 1F
echo.
echo ============================================================
echo   XsiKOM-BewerbungsBOT - Konsolen Version
echo   Komi Tevi - IT-Fachtechniker
echo   Version 6.0
echo ============================================================
echo.
echo   Bot wird gestartet...
echo.
cd /d C:\Users\XsiKOM\IT-Praktikum-Bot
call venv311\Scripts\activate
python main.py
echo.
echo   Bot beendet.
pause