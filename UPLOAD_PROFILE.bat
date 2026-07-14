@echo off
title GitHub Profile Uploader
color 0b
echo ===================================================
echo             GITHUB PROFILE UPLOADER
echo ===================================================
echo.
echo This tool will upload your new animated profile 
echo README and JARVIS banner directly to GitHub.
echo.
echo Make sure you have created the public repository 
echo named "Mukil630" on github.com first!
echo.
echo Press any key to start the upload...
pause > nul
echo.
echo [1/2] Syncing files...
git push -u origin main
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Upload failed.
    echo Please make sure the repository "Mukil630" is created on github.com.
    echo.
) else (
    echo.
    echo [SUCCESS] Upload complete! 
    echo Visit your profile at https://github.com/Mukil630 to see your new animated profile page.
    echo.
)
echo ===================================================
echo Press any key to exit.
pause > nul
