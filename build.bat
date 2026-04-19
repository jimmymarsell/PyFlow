@echo off
echo ========================================
echo   PyFlow 打包脚本
echo ========================================
echo.

:: 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

:: 安装依赖
echo [1/3] 正在安装依赖...
pip install -r requirements.txt
if errorlevel 1 (
    echo [错误] 依赖安装失败
    pause
    exit /b 1
)

:: 打包
echo [2/3] 正在打包...
pyinstaller build.spec --clean
if errorlevel 1 (
    echo [错误] 打包失败
    pause
    exit /b 1
)

echo [3/3] 打包完成！
echo.
echo ========================================
echo   打包完成！
echo ========================================
echo.
echo 可执行文件位置: dist\PyFlow\PyFlow.exe
echo.
echo 使用方法:
echo   服务端模式: dist\PyFlow\PyFlow.exe --server --ip 0.0.0.0 --port 12345
echo   客户端模式: dist\PyFlow\PyFlow.exe --client --ip ^<服务端IP^> --port 12345
echo.
pause
