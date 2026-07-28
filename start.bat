@echo off
REM ============================================
REM 青萍小台 MVP - Windows 一键启动入口
REM 双击此文件即可启动（内部调用 start.py）
REM ============================================
chcp 65001 >nul
title 青萍小台 MVP - 启动器

echo.
echo ============================================
echo   青萍小台 MVP - Windows 启动器
echo ============================================
echo.

REM 切换到脚本所在目录
cd /d "%~dp0"

REM 检查 Python 是否安装
where python >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.10 ~ 3.12
    echo 下载地址: https://www.python.org/downloads/
    echo 安装时务必勾选 "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

REM 显示 Python 版本
echo [信息] 检测到 Python:
python --version
echo.

REM 调用跨平台 Python 启动脚本
python start.py

REM 如果 start.py 异常退出，暂停以便查看日志
if errorlevel 1 (
    echo.
    echo [警告] 启动脚本异常退出，错误码: %errorlevel%
    pause
)