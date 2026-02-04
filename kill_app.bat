@echo off
setlocal enabledelayedexpansion

echo Stopping NexusLog services...

:: Kill by Window Title (Primary - if windows exist)
taskkill /FI "WINDOWTITLE eq NexusLog Backend" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq NexusLog Frontend" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq NexusLog Bot" /T /F >nul 2>&1

:: Kill by Specific Script Name (Precision method for zombies)
:: Finds python processes running 'app.py' or 'telegram_bot.py'
wmic process where "CommandLine like '%%python%%app.py%%'" call terminate >nul 2>&1
wmic process where "CommandLine like '%%python%%telegram_bot.py%%'" call terminate >nul 2>&1

:: Kill by Port (Network method)
:: Backend (5000)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5000') do taskkill /f /pid %%a >nul 2>&1
:: Frontend (5173 / 3000)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5173') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000') do taskkill /f /pid %%a >nul 2>&1

echo NexusLog services stopped safely.
pause
