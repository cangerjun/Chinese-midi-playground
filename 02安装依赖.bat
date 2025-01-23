@echo off
setlocal

REM 设置代码页为 UTF-8 (65001) 或 GBK (936)
chcp 65001 >nul
REM 如果需要使用GBK编码，可以将上面一行改为：
REM chcp 936 >nul

REM 检查 requirements.txt 是否存在
if not exist requirements.txt (
    echo 错误：requirements.txt 文件不存在！
    exit /b 1
)

REM 升级 pip 并安装依赖包
echo 正在升级 pip...
python -m pip install --upgrade pip
if %errorlevel% neq 0 (
    echo 错误：pip 升级失败！
    exit /b 1
)

echo 正在安装依赖包...
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple
if %errorlevel% neq 0 (
    echo 错误：依赖包安装失败！
    exit /b 1
)

echo 依赖包安装完成！

endlocal