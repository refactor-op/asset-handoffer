@echo off
chcp 65001 > nul
setlocal EnableDelayedExpansion

:: ============================================================
:: Asset Handoffer 安装脚本
:: ============================================================

echo.
echo ══════════════════════════════════════════════════════════════
echo   Asset Handoffer 安装程序
echo ══════════════════════════════════════════════════════════════
echo.

set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%.."
cd /d "%PROJECT_DIR%"

set "INSTALL_DIR=%PROJECT_DIR%\.python"
set "PYTHON_EXE=%INSTALL_DIR%\python.exe"
set "PIP_EXE=%INSTALL_DIR%\Scripts\pip.exe"

set "PYTHON_VERSION=3.12.7"
set "PYTHON_ZIP=python-%PYTHON_VERSION%-embed-amd64.zip"
set "PYTHON_URL=https://www.python.org/ftp/python/%PYTHON_VERSION%/%PYTHON_ZIP%"
set "GET_PIP_URL=https://bootstrap.pypa.io/get-pip.py"

:: 检查是否已安装
if exist "%PYTHON_EXE%" (
    echo [√] Python 已安装，跳过下载
    goto :check_pip
)

echo [1/4] 下载 Python %PYTHON_VERSION%...
set "DOWNLOAD_PATH=%INSTALL_DIR%\%PYTHON_ZIP%"
mkdir "%INSTALL_DIR%" 2>nul

powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; $ProgressPreference = 'SilentlyContinue'; Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%DOWNLOAD_PATH%' -UseBasicParsing}"
if errorlevel 1 (
    echo [×] 下载失败，请检查网络
    goto :error
)

echo [2/4] 解压 Python...
powershell -Command "& {Expand-Archive -Path '%DOWNLOAD_PATH%' -DestinationPath '%INSTALL_DIR%' -Force}"
del "%DOWNLOAD_PATH%" 2>nul

:: 配置 pth 文件启用 pip
set "PTH_FILE=%INSTALL_DIR%\python312._pth"
if exist "%PTH_FILE%" (
    powershell -Command "& {(Get-Content '%PTH_FILE%') -replace '#import site', 'import site' | Set-Content '%PTH_FILE%'}"
    echo Lib\site-packages>> "%PTH_FILE%"
)

:check_pip
if exist "%PIP_EXE%" (
    echo [√] pip 已安装
    goto :install_deps
)

echo [3/4] 安装 pip...
set "GET_PIP_PATH=%INSTALL_DIR%\get-pip.py"
powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; $ProgressPreference = 'SilentlyContinue'; Invoke-WebRequest -Uri '%GET_PIP_URL%' -OutFile '%GET_PIP_PATH%' -UseBasicParsing}"
"%PYTHON_EXE%" "%GET_PIP_PATH%"
del "%GET_PIP_PATH%" 2>nul

:install_deps
echo [4/4] 安装 Asset Handoffer...
if exist "%PROJECT_DIR%\pyproject.toml" (
    "%PYTHON_EXE%" -m pip install -e "%PROJECT_DIR%" --quiet
) else (
    "%PYTHON_EXE%" -m pip install asset-handoffer --quiet
)

echo.
echo ══════════════════════════════════════════════════════════════
echo [√] 安装完成！
echo.
"%PYTHON_EXE%" --version
"%PYTHON_EXE%" -m asset_handoffer --version 2>nul
echo.
echo 下一步：运行 asset-handoffer setup your-config.yaml
echo ══════════════════════════════════════════════════════════════
echo.
pause
exit /b 0

:error
echo.
echo [×] 安装失败，请检查网络连接或联系技术支持
pause
exit /b 1
