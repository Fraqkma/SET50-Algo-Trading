@echo off
setlocal
set "REPO_ROOT=%~dp0.."
pushd "%REPO_ROOT%" || exit /b 1
"%REPO_ROOT%\.venv\Scripts\python.exe" "%REPO_ROOT%\scripts\run_settrade_daily.py" %*
set "EXIT_CODE=%ERRORLEVEL%"
popd
exit /b %EXIT_CODE%
