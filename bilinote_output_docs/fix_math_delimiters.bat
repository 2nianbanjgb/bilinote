@echo off
chcp 65001 >nul
cd /d "%~dp0"

rem 用法：
rem   1. 直接双击：先预览本目录所有 .md 的修改，回车确认后写入
rem   2. 把 .md 文件（或文件夹）拖到本文件上：直接按参数处理
rem   3. 命令行：fix_math_delimiters.bat -n .   （参数原样传给 fix_math_delimiters.mjs）

if not "%~1"=="" (
    node "%~dp0fix_math_delimiters.mjs" %*
    echo.
    pause
    exit /b %errorlevel%
)

echo [1/2] 预览本目录中将要修改的内容...
echo.
node "%~dp0fix_math_delimiters.mjs" -n .
echo.
set "GO="
set /p "GO=直接回车确认写入（输入任意其它内容则取消）："
if defined GO (
    echo.
    echo 已取消，文件未改动。
    echo.
    pause
    exit /b 0
)
echo.
echo [2/2] 正在写入（自动生成 .bak 备份）...
echo.
node "%~dp0fix_math_delimiters.mjs" .
echo.
pause
