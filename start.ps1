# 1. 设置工作目录为脚本所在的文件夹
$PSScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $PSScriptRoot

# 2. 定义虚拟环境激活脚本的路径
$activateScript = ".\.venv\Scripts\Activate.ps1"

# 3. 检查 venv 是否存在
if (Test-Path $activateScript) {
    Write-Host "--- 正在激活虚拟环境 ---" -ForegroundColor Cyan
    # 激活虚拟环境
    . $activateScript

    Write-Host "--- 正在启动 main.py ---" -ForegroundColor Green
    # 运行你的程序
    python main.py

    # 运行结束后退出虚拟环境
    deactivate
}
else {
    Write-Host "错误: 未找到虚拟环境 (venv)。请确认 venv 文件夹在当前目录下。" -ForegroundColor Red
    Pause
}