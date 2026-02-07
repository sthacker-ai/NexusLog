@echo off
echo Starting NexusLog System...

:: Run Diagnostics
cmd /c "cd backend && venv\Scripts\activate && python check_system.py"

:: Start Backend API (Visible, Persistent)
start "NexusLog Backend" cmd /k "cd backend && venv\Scripts\activate && python app.py"

:: Start Frontend (Visible, Persistent)
start "NexusLog Frontend" cmd /k "cd frontend && npm run dev"

:: Start Telegram Bot (Visible, Persistent)
start "NexusLog Bot" cmd /k "cd backend && venv\Scripts\activate && python telegram_bot.py"

echo All services launched in background! 
echo Logs are written to backend/logs/ folder.
echo Frontend: http://localhost:3000
pause
